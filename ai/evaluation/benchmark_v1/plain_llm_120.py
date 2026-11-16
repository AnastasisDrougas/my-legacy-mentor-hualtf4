#!/usr/bin/env python3
"""120-case plain-LLM baseline, reusing the existing Knowledge Legacy holdout.

Only 120 new calls. NEVER edits the existing answers.jsonl.
Compatible with OpenAI-style /chat/completions endpoint (incl. Gemini compatibility).
Run from project root. For config use --base-url / --model / --api-key-env,
or LLM_BASE_URL / LLM_MODEL / GEMINI_API_KEY environment variables.
"""
import argparse
import hashlib
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOLDOUT = HERE / 'holdout_v1'
QUESTIONS = HOLDOUT / 'questions.json'
PREVIOUS = HOLDOUT / 'results' / 'answers.jsonl'
NEW = HOLDOUT / 'results' / 'plain_llm_answers.jsonl'
META = HOLDOUT / 'results' / 'plain_llm_manifest.json'
SYSTEM_PROMPT = (
    'You are a general-purpose software engineering assistant. Answer the user '
    'accurately and practically using your general knowledge. You have NOT been '
    'given documents about Alex Morgan, any historical decisions, incidents, '
    'or private production data. Do not pretend to know Alex\'s personal '
    'decisions or private facts, and do not invent citations or source IDs. '
    'When you cannot know a specific historical fact, say so plainly; you '
    'may still offer clearly labeled general engineering advice. '
    'If a suggested action is unsafe or based on a false premise, correct it. '
    'Avoid unnecessary verbosity.'
)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def read_jsonl(path):
    if not path.exists():
        return []
    rows = []
    for n, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except ValueError as exc:
                raise SystemExit(f'Invalid {path}:{n}: {exc}')
    return rows


def append_jsonl(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + '\n')
        handle.flush()
        os.fsync(handle.fileno())


def load_and_validate():
    if not QUESTIONS.is_file():
        raise SystemExit(f'Missing {QUESTIONS}; place script next to full_benchmark.py')
    qs = json.loads(QUESTIONS.read_text(encoding='utf-8'))
    if len(qs) != 120 or len({q['id'] for q in qs}) != 120:
        raise SystemExit('STOP: expected exactly 120 unique question IDs')
    old = read_jsonl(PREVIOUS)
    old_keys = [(r.get('case_id'), r.get('system')) for r in old]
    expected_old = {(q['id'], sys) for q in qs for sys in ('digital_twin', 'baseline_rag')}
    if len(old_keys) != 240 or len(set(old_keys)) != 240 or set(old_keys) != expected_old:
        raise SystemExit('STOP: Existing benchmark is not exactly 240 unique paired results. Check data before running.')
    question_by_id = {q['id']: q for q in qs}
    for row in old:
        q = question_by_id[row['case_id']]
        if row.get('question') != q['question'] or not row.get('answer', '').strip():
            raise SystemExit(f'STOP: existing response is missing/mismatched: {row["case_id"]}')
    prior = read_jsonl(NEW)
    seen = set()
    for row in prior:
        sid = row.get('case_id')
        if sid in seen or sid not in question_by_id or row.get('system') != 'plain_llm':
            raise SystemExit(f'STOP: invalid/duplicate plain LLM response: {sid}')
        if row.get('question') != question_by_id[sid]['question'] or not row.get('answer', '').strip():
            raise SystemExit(f'STOP: changed question or empty response: {sid}')
        seen.add(sid)
    return qs, prior


def normalize_base_url(raw):
    raw = raw.strip().rstrip('/')
    if raw.endswith('/chat/completions'):
        return raw
    return raw + '/chat/completions'


def api_chat(url, key, model, question, temperature, timeout):
    body = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': question},
        ],
        'temperature': temperature,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode('utf-8'),
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        err = exc.read(1000).decode('utf-8', errors='replace')
        retry = exc.headers.get('Retry-After') if exc.headers else None
        # No API keys, URLs, or response content with secrets printed.
        raise APIError(exc.code, retry, err[:240]) from None
    options = payload.get('choices', [])
    if not options:
        raise RuntimeError('LLM returned no choices')
    content = options[0].get('message', {}).get('content')
    if isinstance(content, list):
        content = '\n'.join(p.get('text', '') for p in content if isinstance(p, dict))
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError('LLM returned no answer text')
    return content.strip()


class APIError(Exception):
    def __init__(self, code, retry_after, detail):
        self.code = code
        try:
            self.retry_after = float(retry_after)
        except (TypeError, ValueError):
            self.retry_after = None
        super().__init__(f'HTTP {code}: {detail}')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--dry-run', action='store_true')
    g.add_argument('--run', action='store_true')
    g.add_argument('--report', action='store_true')
    p.add_argument('--confirm-120', action='store_true', help='Explicit approval for the 120 additional paid API calls')
    p.add_argument('--model', default=os.getenv('LLM_MODEL') or os.getenv('GEMINI_MODEL') or '')
    p.add_argument('--base-url', default=os.getenv('LLM_BASE_URL') or os.getenv('OPENAI_BASE_URL') or 'https://generativelanguage.googleapis.com/v1beta/openai')
    p.add_argument('--api-key-env', default='GEMINI_API_KEY', help='Environment variable name containing the key (never the secret value)')
    p.add_argument('--temperature', type=float, default=0.2)
    p.add_argument('--delay-seconds', type=float, default=8)
    p.add_argument('--max-retries', type=int, default=3)
    p.add_argument('--backoff-seconds', type=float, default=30)
    p.add_argument('--max-backoff-seconds', type=float, default=180)
    p.add_argument('--max-calls', type=int, default=120)
    p.add_argument('--timeout-seconds', type=float, default=90)
    args = p.parse_args()
    if args.delay_seconds < 0 or args.max_retries < 0 or args.max_calls < 1 or args.backoff_seconds < 0:
        p.error('Delay, retries and backoff must be non-negative; max-calls must be positive')
    qs, prior = load_and_validate()
    completed = {r['case_id'] for r in prior}
    todo = [q for q in qs if q['id'] not in completed]
    print(f'Existing historical responses: 240/240 (read only)')
    print(f'Plain LLM: {len(prior)}/120 saved; {len(todo)} pending')
    print(f'Categories: {dict(Counter(q["category"] for q in qs))}')
    if args.dry_run or args.report:
        print('No API requests made.')
        if args.report:
            print(json.dumps({'complete': len(todo) == 0, 'plain_llm_saved': len(prior), 'all_systems_total': 240 + len(prior), 'average_plain_latency_seconds': round(sum(r['latency_seconds'] for r in prior) / len(prior), 3) if prior else None}, indent=2))
        return
    if not args.confirm_120:
        p.error('--run requires --confirm-120')
    if not args.model.strip():
        p.error('Specify --model EXACTLY matching the other two benchmark systems, or set LLM_MODEL')
    key = os.getenv(args.api_key_env) or (os.getenv('LLM_API_KEY') if args.api_key_env == 'GEMINI_API_KEY' else None)
    if not key:
        p.error(f'API key not found in ${args.api_key_env} (or $LLM_API_KEY)')
    url = normalize_base_url(args.base_url)
    signature = {'model': args.model, 'base_url': url, 'temperature': args.temperature, 'system_prompt_sha256': sha(SYSTEM_PROMPT), 'questions_sha256': sha(json.dumps(qs, sort_keys=True, ensure_ascii=False))}
    if META.exists():
        previous_signature = json.loads(META.read_text(encoding='utf-8'))
        if signature != previous_signature:
            raise SystemExit('STOP: model, endpoint, temperature, prompt or questions changed. Preserve benchmark comparability.')
    else:
        if prior:
            raise SystemExit('STOP: responses exist but plain manifest missing; do not risk mixing model configs.')
        META.parent.mkdir(parents=True, exist_ok=True)
        META.write_text(json.dumps(signature, indent=2, ensure_ascii=False), encoding='utf-8')
    last_attempt = None
    completed_now = 0
    for idx, q in enumerate(todo[:args.max_calls], 1):
        print(f'[{idx}/{min(len(todo), args.max_calls)}] {q["id"]} plain_llm / {q["category"]}', flush=True)
        for retry in range(args.max_retries + 1):
            if last_attempt is not None:
                wait = args.delay_seconds - (time.monotonic() - last_attempt)
                if wait > 0:
                    time.sleep(wait)
            last_attempt = time.monotonic()
            started = time.perf_counter()
            try:
                answer = api_chat(url, key, args.model, q['question'], args.temperature, args.timeout_seconds)
                row = {
                    'case_id': q['id'], 'category': q['category'],
                    'system': 'plain_llm', 'mode': 'plain',
                    'question': q['question'], 'answer': answer, 'sources': [],
                    'latency_seconds': round(time.perf_counter() - started, 3),
                    'timestamp_utc': utc_now(), 'question_sha256': sha(q['question']),
                }
                append_jsonl(NEW, row)
                completed_now += 1
                print(f'  SAVED {len(answer)} chars / 0 sources', flush=True)
                break
            except KeyboardInterrupt:
                print('Interrupted; saved rows retained.')
                return
            except APIError as exc:
                if exc.code not in (429, 500, 502, 503, 504) or retry == args.max_retries:
                    print(f'STOPPED: {exc}; outputs preserved. Retry later.')
                    return
                backoff = args.backoff_seconds * (2 ** retry) + random.uniform(0, 2)
                backoff = max(backoff, exc.retry_after or 0)
                if backoff > args.max_backoff_seconds:
                    print(f'STOPPED: retry would exceed max backoff ({backoff:.1f}s). Outputs preserved.')
                    return
                print(f'  HTTP {exc.code}: retry {retry + 1}/{args.max_retries} after {backoff:.1f}s', flush=True)
                time.sleep(backoff)
            except Exception as exc:
                print(f'STOPPED: {type(exc).__name__}: {exc}. Saved outputs preserved.')
                return
    print(f'Completed {completed_now} new answers. Plain LLM total: {len(prior) + completed_now}/120')


if __name__ == '__main__':
    main()
