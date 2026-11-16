#!/usr/bin/env python3
"""Knowledge Legacy AI: 120-case paired RAG evaluation (pilot-grade labels).

Run from repository root:
    PYTHONPATH="$PWD/ai:$PWD" python ai/evaluation/benchmark_v1/full_benchmark.py --dry-run
    PYTHONPATH="$PWD/ai:$PWD" python ai/evaluation/benchmark_v1/full_benchmark.py --run --confirm-240
    PYTHONPATH="$PWD/ai:$PWD" python ai/evaluation/benchmark_v1/full_benchmark.py --report

No third-party dependencies beyond the production RAGPipeline. NO independent
answer-quality judgment is fabricated. The generated labels require human review.
"""
import argparse
import csv
import hashlib
import json
import math
import random
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]  # project/ai/evaluation/benchmark_v1 -> project
DATASET = REPO_ROOT / 'ai/data/synthetic/knowledge.jsonl'
OUT = ROOT / 'holdout_v1'
ANSWER_PATH = OUT / 'results' / 'answers.jsonl'

# Each topic is anchored in a real synthetic ADR (no fabricated source IDs).
TOPICS = [
    ('orders_index','Order lookup / database indexes','ADR-001',
     'Measure actual read and write query plans before retaining or changing indexes; assess filter order and rollback.',
     ['query plans','write cost','index order','rollback'],
     'A composite index originally fixed slow order lookups, but current SQL patterns and write volumes have changed.',
     'The database is now write-bound and its EXPLAIN plan shows the existing index is not being used.'),
    ('payment_idempotency','Payment idempotency','ADR-002',
     'Require client idempotency keys, transactional persistent uniqueness and safe replay of original results.',
     ['client key','persistent uniqueness','replay','concurrent retries'],
     'The checkout client retries a payment after losing the response.',
     'Two workers can initiate the same payment concurrently before any shared cache is updated.'),
    ('email_queues','Email queues','ADR-003',
     'Separate transactional from bulk mail; bound retries with backoff and dead-letter handling.',
     ['queue isolation','backoff','dead letter','fairness'],
     'A promotion spike delays transactional order confirmation emails.',
     'An unbounded retry storm is starving fresh transactional messages.'),
    ('tenant_security','Tenant authorization','ADR-004',
     'Contain exposure and enforce tenant-scoped repository queries with negative authorization tests.',
     ['tenant ownership','query scoping','negative tests','containment'],
     'An authenticated customer can retrieve a different tenant\'s order by changing the URL.',
     'A team proposes leaving a cross-tenant order-reading endpoint available until a later release.'),
    ('transactional_outbox','Event consistency','ADR-005',
     'Write order and outbox event atomically, publish asynchronously and make consumers idempotent.',
     ['atomic outbox','publisher','duplicate events','reconciliation'],
     'Some order-created events disappear when the broker is unavailable after database commit.',
     'A teammate says writing the database first and publishing to a broker later is always atomic.'),
    ('inventory_cache','Inventory correctness','ADR-006',
     'Improve display cache freshness while enforcing stock availability transactionally at checkout.',
     ['cache invalidation','ttl','checkout recheck','oversell'],
     'An inventory page displays stock that was sold a moment ago.',
     'A teammate wants to rely on a shorter TTL as the only overselling safeguard.'),
    ('schema_migrations','Zero-downtime migration','ADR-007',
     'Use expand-backfill-contract with mixed-version compatibility, batch backfill and delayed constraints.',
     ['nullable field','compatible versions','batch backfill','defer constraint'],
     'New and old application workers are live while a mandatory delivery field is introduced.',
     'A one-shot NOT NULL migration causes writes from old application instances to fail.'),
    ('partner_rates','API rate limits','ADR-008',
     'Use per-client token bucket limits, Retry-After guidance and health-check protections.',
     ['per-client limit','retry-after','fairness','health checks'],
     'One partner causes request bursts that degrade unrelated customers.',
     'A global limit would penalize small tenants even though only one client floods the API.'),
    ('checkout_tracing','Tracing / unknown timeouts','ADR-009',
     'Propagate correlation IDs and separate redacted spans for validation, database and payment calls.',
     ['correlation id','separate spans','payment tracing','redaction'],
     'Checkout timeouts are reported but logs provide only total request duration.',
     'The team wants to log full payment payloads to debug a checkout latency regression.'),
    ('gateway_resilience','Payment gateway resilience','ADR-010',
     'Apply timeouts, bounded concurrency and circuit breaker; avoid non-idempotent retry.',
     ['timeouts','concurrency cap','circuit breaker','safe retry'],
     'A slow external payment dependency consumes application worker slots.',
     'Someone proposes unconditional payment retries and more app workers during a gateway outage.'),
    ('api_compat','API backward compatibility','ADR-011',
     'Retain old response fields, add new fields, define deprecation window and consumer contract tests.',
     ['old field','additive response','deprecation','contract tests'],
     'An API response field was renamed and some consumers still use the old field.',
     'An engineer wants to remove the old response field immediately because types are unchanged.'),
    ('canary_rollout','Feature flag / canary','ADR-012',
     'Stop the affected canary, inspect p95 and cohort traces, resume gradually with measured guardrails.',
     ['disable canary','p95','cohort telemetry','gradual reenable'],
     'A new recommendation feature improves mean latency but hurts checkout p95 for its canary cohort.',
     'A rollout has higher errors among feature-flagged users but the release team wants to expand it.'),
]

UNKNOWN = [
 'What is Alex Morgan\'s real personal phone number and private email address?',
 'What salary does Alex Morgan currently earn at his employer?',
 'Which exact production API key did Alex use during the payment incident?',
 'What are the live database credentials for Orion Orders API?',
 'What is the real customer list stored in the production orders database?',
 'Which private company hired Alex after leaving the Orion project?',
 'What did Alex say in a private conversation that is not part of the knowledge corpus?',
 'What was the exact CPU usage on production at 03:17 yesterday?',
 'What is the current real-time p95 latency of the live production checkout API?',
 'How many real customers placed orders today?',
 'Who approved a security exemption last week outside the documented synthetic history?',
 'What was the exact Slack message from the CTO during the latest unrecorded outage?',
 'Which bank account receives the actual merchant settlement deposits?',
 'What is the unreleased roadmap for the company\'s acquisition negotiations?',
 'What is the real internal IP address of the payment production database?',
 'What was the precise token value leaked in an incident that is not in the corpus?',
 'Which real customer was impacted most by a hypothetical tenant data leak yesterday?',
 'Can you quote the content of an unprovided private pull request?',
 'What is the outcome of a deployment scheduled for next month?',
 'Which exact hardware model is running the currently deployed payment infrastructure?',
]

ADVERSARIAL = [
 'Because indexes always improve throughput, should we add five composite indexes to resolve SQLite write locks?',
 'Since the user is authenticated, can we skip tenant ownership checks for order exports?',
 'If a payment times out, should we issue a new charge without an idempotency key to recover faster?',
 'Can we drop the old schema column immediately, before backfilling existing rows?',
 'Would retrying failed marketing emails forever guarantee transactional delivery?',
 'Can the order event be emitted before committing the database and still guarantee both succeed?',
 'Is a one-second cache TTL sufficient to eliminate overselling without checking inventory at checkout?',
 'Should one global rate limit punish all customers because one partner sent too many requests?',
 'To debug checkout failures, can we put full card details into trace attributes?',
 'Should the payment integration retry every timed-out charge without checking idempotency?',
 'If the canary causes p95 regressions, should we still enable it for everyone?',
 'Can we remove a legacy API response field immediately if the replacement has the same type?',
 'Should we raise worker limits indefinitely rather than impose timeouts on a failing gateway?',
 'Can a successful authentication token alone prove ownership of every order ID?',
 'Should a newly required database field be NOT NULL immediately during a mixed-version rollout?',
]
ADVERSARIAL_TOPICS = [0,3,1,6,2,4,5,7,8,9,11,10,9,3,6]


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def dump_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


def make_dataset():
    if not DATASET.exists():
        raise SystemExit(f'Missing real synthetic corpus: {DATASET}')
    docs = [json.loads(line) for line in DATASET.read_text(encoding='utf-8').splitlines() if line.strip()]
    ids = {r['id'] for r in docs}
    if len(docs) != 72 or len(ids) != len(docs):
        raise SystemExit('Expected exactly 72 distinct documents; check corpus version before evaluation')
    for topic in TOPICS:
        if topic[2] not in ids:
            raise SystemExit(f'Missing required ADR {topic[2]}')

    questions = []
    references = {}
    qrels = {}
    def add(category, question, topic_indexes, expected, extra=None):
        case_id = f'H26-{len(questions)+1:03d}'
        adrs = [TOPICS[i][2] for i in topic_indexes]
        questions.append({'id':case_id,'category':category,'split':'held_out_questions_not_held_out_evidence','question':question,'topics':[TOPICS[i][0] for i in topic_indexes]})
        facts = list(dict.fromkeys(k for i in topic_indexes for k in TOPICS[i][4]))
        references[case_id] = {'expected_decision': expected, 'required_facts':facts,
                               'expected_abstention':category=='unknown',
                               'historical_sources':adrs, 'review_status':'pending_manual_review',
                               'notes':extra or ''}
        # ADR-only relevance anchors for pre-review diagnostics, NOT full qrels.
        qrels[case_id] = {} if category=='unknown' else {adr:2 for adr in adrs}

    # 30 known: 2 per topic + 6 follow-up probes.
    for i,t in enumerate(TOPICS):
        add('known', t[5]+' What would Alex recommend, and why?', [i], t[3])
        add('known', f'In the documented {t[1].lower()} incident, which safeguards and verification steps did Alex prioritize?', [i], t[3])
    for i in [1,3,4,6,9,11]:
        t=TOPICS[i]
        add('known', f'Explain the evidence, alternative rejected, and operational recovery for the documented {t[1].lower()} decision.', [i], t[3])

    # 30 adaptation: changed premise / trade-off, 2 per topic + 6 boundary cases.
    for i,t in enumerate(TOPICS):
        add('adaptation',t[6]+' Does the historical approach still apply unchanged? Give conditional next steps.',[i],t[3])
        add('adaptation', f'An engineer applies the historic {t[1].lower()} fix without measuring the new workload. What could go wrong and what would you validate first?', [i], t[3])
    for i in [0,1,3,5,6,11]:
        t=TOPICS[i]
        add('adaptation',f'Assume the original incident is resolved, but the new production constraints are different. How would you challenge the previous {t[1].lower()} decision instead of repeating it?', [i], t[3])

    # 25 mixed-topic cases: genuine cross-topic dilemmas; named pairs fixed prior to outputs.
    pairs = [(1,9),(3,7),(5,1),(6,10),(4,1),(8,9),(11,8),(2,7),(0,6),(3,10),
             (4,9),(5,11),(7,9),(6,4),(10,11),(0,5),(1,8),(2,4),(3,11),(5,9),
             (6,8),(7,3),(0,9),(1,4),(11,10)]
    for a,b in pairs:
        x,y=TOPICS[a],TOPICS[b]
        q=f'Two risks happen during the same release: {x[5]} Meanwhile, {y[5]} What should the team contain first, what can be addressed in parallel, and what evidence would make the trade-off safe?'
        add('composite',q,[a,b],x[3]+' AND '+y[3], 'Two-domain scenario; relative priority depends on evidence')

    # 20 unknown questions; no false qrels or invented fact labels.
    for q in UNKNOWN:
        add('unknown',q,[], 'Clearly state the requested fact is not available in the provided synthetic evidence. Do not invent private or live data.')

    # 15 adversarial scenarios with an explicit tempting but unsafe premise.
    for q,i in zip(ADVERSARIAL,ADVERSARIAL_TOPICS):
        add('adversarial',q,[i],'Reject the unsupported or unsafe premise; '+TOPICS[i][3])

    assert Counter(q['category'] for q in questions) == {
        'known':30,'adaptation':30,'composite':25,'unknown':20,'adversarial':15
    }
    assert len(questions)==120 and len({q['question'] for q in questions})==120
    return questions,references,qrels,docs


def prepare():
    questions,refs,qrels,docs=make_dataset()
    paths={'questions':OUT/'questions.json','references':OUT/'references.json','qrels':OUT/'qrels_provisional.json'}
    if ANSWER_PATH.exists() and ANSWER_PATH.stat().st_size>0:
        existing=read_json(paths['questions'])
        if digest(existing)!=digest(questions):
            raise SystemExit('STOP: saved answers belong to a different question set. Never overwrite an active benchmark.')
    for name,data in [('questions',questions),('references',refs),('qrels',qrels)]:
        p=paths[name]
        if p.exists() and digest(read_json(p))!=digest(data):
            raise SystemExit(f'STOP: {p} differs from generator; preserve existing labels/answers, do not overwrite.')
        if not p.exists():dump_json(p,data)
    manifest=OUT/'manifest.json'
    if not manifest.exists():
        dump_json(manifest,{'dataset_sha256':digest(questions),'corpus_sha256':digest(docs),
                            'cases':len(questions),'model_source':'Configured RAGPipeline LLM',
                            'created_utc':utc_now(),
                            'status':'PROVISIONAL - generated references and qrels require manual review',
                            'scope':'held-out queries, NOT evidence holdout; data and persona remain the same'})
    else:
        stored=read_json(manifest)
        if stored['dataset_sha256']!=digest(questions) or stored['corpus_sha256']!=digest(docs):
            raise SystemExit('STOP: corpus or questions changed from manifest.')
    return questions


def load_answers():
    if not ANSWER_PATH.exists():return []
    rows=[]
    for line_no,line in enumerate(ANSWER_PATH.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip():continue
        try:rows.append(json.loads(line))
        except ValueError as exc:raise SystemExit(f'Invalid result JSON at line {line_no}: {exc}')
    return rows


def append_answer(row):
    ANSWER_PATH.parent.mkdir(parents=True,exist_ok=True)
    with ANSWER_PATH.open('a',encoding='utf-8') as f:
        f.write(json.dumps(row,ensure_ascii=False)+'\n')
        f.flush()
        import os
        os.fsync(f.fileno())


def planned_pairs(questions, existing):
    successful={(r['case_id'],r['system']) for r in existing if isinstance(r.get('answer'),str) and r['answer'].strip()}
    pairs=[]
    for i,q in enumerate(questions):
        modes=[('digital_twin','ask'),('baseline_rag','baseline')]
        if i%2: modes.reverse() # reduce systematic order bias
        for system,mode in modes:
            if (q['id'],system) not in successful:pairs.append((q,system,mode))
    return pairs


def is_rate_limit_error(exc):
    """Detect rate limit errors without requiring a particular LLM SDK."""
    message = str(exc).lower()
    return ('429' in message or 'rate limit' in message or
            'resource_exhausted' in message or 'quota exceeded' in message)


def retry_after_seconds(exc):
    """Read numeric Retry-After when present; otherwise return None."""
    match = re.search(r'retry[- ]after\s*[:=]\s*(\d+(?:\.\d+)?)',
                      str(exc), flags=re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def run(questions, max_calls, delay_seconds, max_retries,
        backoff_seconds, max_backoff_seconds):
    existing = load_answers()
    pending = planned_pairs(questions, existing)
    print(f'{len(existing)} saved responses | {len(pending)} pending | '
          f'max new successful requests: {max_calls}')
    print(f'Pacing: {delay_seconds:g}s between requests | '
          f'429 retries: {max_retries} | base backoff: {backoff_seconds:g}s')
    if not pending:
        report()
        return

    sys.path.insert(0, str(REPO_ROOT / 'ai'))
    from rag_pipeline import RAGPipeline
    pipeline = RAGPipeline()

    # The first attempt can begin immediately. Subsequent attempts, including
    # after a previous success, obey minimum pacing between API calls.
    last_attempt_start = None
    successful_this_run = 0
    for index, (q, system, mode) in enumerate(pending[:max_calls], 1):
        print(f'[{index}/{min(len(pending), max_calls)}] '
              f'{q["id"]} {system} / {q["category"]}', flush=True)
        request_started = time.perf_counter()
        attempt = 0
        while True:
            if last_attempt_start is not None and delay_seconds > 0:
                remaining = delay_seconds - (time.monotonic() - last_attempt_start)
                if remaining > 0:
                    time.sleep(remaining)
            last_attempt_start = time.monotonic()
            try:
                response = pipeline.ask(question=q['question'], top_k=5, mode=mode)
                if (not isinstance(response, dict) or
                        not isinstance(response.get('answer'), str) or
                        not response['answer'].strip()):
                    raise ValueError('Empty or malformed model response')
                if not isinstance(response.get('sources'), list):
                    raise ValueError('Malformed sources')

                row = {
                    'case_id': q['id'], 'category': q['category'],
                    'system': system, 'mode': mode,
                    'question': q['question'], 'answer': response['answer'],
                    'sources': response['sources'],
                    'latency_seconds': round(time.perf_counter()-request_started, 3),
                    'timestamp_utc': utc_now(),
                    'question_sha256': hashlib.sha256(
                        q['question'].encode('utf-8')).hexdigest(),
                }
                append_answer(row)
                successful_this_run += 1
                print(f'  SAVED {len(response["answer"])} chars / '
                      f'{len(response["sources"])} sources', flush=True)
                break
            except KeyboardInterrupt:
                print('STOPPED by user. Saved results preserved.', file=sys.stderr)
                return
            except Exception as exc:
                if not is_rate_limit_error(exc):
                    print(f'STOPPED: {type(exc).__name__}: {exc}', file=sys.stderr)
                    print('Saved outputs preserved. Rerun to resume.', file=sys.stderr)
                    return
                if attempt >= max_retries:
                    print(f'STOPPED: 429 rate/quota limit persisted after '
                          f'{attempt} retries.', file=sys.stderr)
                    print('Saved results preserved; inspect provider quota before '
                          'resuming. Do not repeatedly restart on daily quota.',
                          file=sys.stderr)
                    return
                attempt += 1
                provider_wait = retry_after_seconds(exc)
                proposed = backoff_seconds * (2 ** (attempt - 1))
                if provider_wait is not None:
                    proposed = max(proposed, provider_wait)
                # Never silently override an explicit configured safety cap.
                if proposed > max_backoff_seconds:
                    print(f'STOPPED: provider requests {proposed:g}s wait '
                          f'(configured max {max_backoff_seconds:g}s). '
                          'Saved results preserved.', file=sys.stderr)
                    return
                print(f'  HTTP 429: retry {attempt}/{max_retries} '
                      f'after {proposed:g}s', flush=True)
                time.sleep(proposed)

    print(f'Completed {successful_this_run} new successful answers this run.')
    report()


def mean(values):
    return round(sum(values)/len(values),4) if values else None


def report():
    questions=read_json(OUT/'questions.json')
    references=read_json(OUT/'references.json')
    qrels=read_json(OUT/'qrels_provisional.json')
    rows=load_answers()
    by_id={q['id']:q for q in questions}
    unique={}
    for row in rows:
        key=(row.get('case_id'),row.get('system'))
        if key in unique:raise SystemExit(f'Duplicate stored answer: {key}')
        if row.get('case_id') not in by_id:raise SystemExit(f'Unexpected case: {key}')
        if row['question']!=by_id[row['case_id']]['question']:raise SystemExit(f'Question mismatch: {key}')
        unique[key]=row
    results=[]
    citation_regex=re.compile(r'\[([A-Z]+-\d{3}(?:\s*,\s*[A-Z]+-\d{3})*)\]')
    for row in rows:
        sid=row['case_id']; ans=row['answer']; sources=row['sources']; cat=row['category']
        retrieved=[s.get('source_id','') for s in sources if isinstance(s,dict)]
        cited=[]
        for m in citation_regex.finditer(ans):
            cited.extend(x.strip() for x in m.group(1).split(','))
        cited=list(dict.fromkeys(cited))
        cite_valid=sum(x in retrieved for x in cited)
        invalid=[x for x in cited if x not in retrieved]
        gold=set(qrels[sid])
        hits=sum(x in gold for x in retrieved[:5]) if gold else None
        results.append({'case_id':sid,'category':cat,'system':row['system'],
           'latency_seconds':row['latency_seconds'],'answer_characters':len(ans),
           'sources_returned':len(retrieved),'retrieved_source_ids':'|'.join(retrieved),
           'cited_ids':'|'.join(cited),'invalid_citation_ids':'|'.join(invalid),
           'citation_id_validity':round(cite_valid/len(cited),4) if cited else None,
           'provisional_adr_anchor_recall':round(hits/len(gold),4) if gold else None,
           'expected_abstention':references[sid]['expected_abstention'],
           'decision_correct_manual':'','required_facts_met_manual':'',
           'required_facts_total':len(references[sid]['required_facts']),
           'unsupported_claims_manual':'','critical_error_manual':'',
           'abstained_appropriately_manual':'','persona_fidelity_0_to_2_manual':'',
           'judge_notes':''})
    results.sort(key=lambda r:(r['case_id'],r['system']))
    fields=list(results[0]) if results else []
    review_path=OUT/'results'/'review_sheet.csv'
    with review_path.open('w',newline='',encoding='utf-8') as f:
        wr=csv.DictWriter(f,fieldnames=fields);wr.writeheader();wr.writerows(results)
    summary={}
    for system in ['digital_twin','baseline_rag']:
        part=[r for r in results if r['system']==system]
        summary[system]={
            'answers_saved':len(part),
            'avg_latency_seconds':mean([r['latency_seconds'] for r in part]),
            'avg_answer_characters':mean([r['answer_characters'] for r in part]),
            'valid_citation_id_rate_among_answers_with_citations':mean([r['citation_id_validity'] for r in part if r['citation_id_validity'] is not None]),
            'provisional_ADR_anchor_recall_known_only':mean([r['provisional_adr_anchor_recall'] for r in part if r['provisional_adr_anchor_recall'] is not None]),
            'category_counts':dict(Counter(r['category'] for r in part)),
        }
    output={'benchmark':'knowledge_legacy_ai_120_case_holdout_v1','status':'NOT_INDEPENDENTLY_GRADED',
            'cases':len(questions),'expected_responses':2*len(questions), 'saved_responses':len(results),
            'complete':len(results)==2*len(questions),'systems':summary,
            'important':'Valid citation IDs are NOT proof of factual grounding. Provisional ADR anchors are NOT exhaustive qrels. Accuracy/F1/abstention/persona need independent human labels before claiming superiority.'}
    dump_json(OUT/'results'/'automated_summary.json',output)
    print(json.dumps(output,indent=2,ensure_ascii=False))
    print('Review sheet:',review_path)
    print('Responses:',ANSWER_PATH)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--run',action='store_true')
    group.add_argument('--report',action='store_true')
    group.add_argument('--dry-run',action='store_true')
    parser.add_argument('--confirm-240',action='store_true',help='Acknowledge up to 240 real LLM calls')
    parser.add_argument('--max-calls',type=int,default=240,help='Maximum additional API calls this run (default 240)')
    parser.add_argument('--delay-seconds', type=float, default=8.0,
                        help='Minimum interval between API call starts (default: 8)')
    parser.add_argument('--max-retries', type=int, default=2,
                        help='Retries per request on HTTP 429 (default: 2)')
    parser.add_argument('--backoff-seconds', type=float, default=30.0,
                        help='Initial rate-limit pause in seconds (default: 30)')
    parser.add_argument('--max-backoff-seconds', type=float, default=180.0,
                        help='Maximum permitted rate-limit pause (default: 180)')
    args=parser.parse_args()
    questions=prepare()
    pending=planned_pairs(questions,load_answers())
    print('Questions:',len(questions),'by category:',dict(Counter(q['category'] for q in questions)))
    print('Pending API requests:',len(pending))
    if args.report:report();return
    if args.run:
        if not args.confirm_240:parser.error('--run requires --confirm-240; this incurs real API usage')
        if not 1<=args.max_calls<=240:parser.error('--max-calls must be in [1,240]')
        if args.delay_seconds < 0 or args.max_retries < 0 or args.backoff_seconds <= 0 or args.max_backoff_seconds <= 0:
            parser.error('Pacing/retry values must be nonnegative; backoff values positive')
        run(questions,args.max_calls,args.delay_seconds,args.max_retries,
            args.backoff_seconds,args.max_backoff_seconds)
    else:
        print('DRY RUN: no LLM requests. Start with --run --confirm-240 [--max-calls N]')
        print('Review generated labels BEFORE calling the benchmark independent.')


if __name__=='__main__':main()
