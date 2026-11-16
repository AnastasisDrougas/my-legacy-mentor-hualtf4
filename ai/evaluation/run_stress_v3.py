
import argparse
import csv
import hashlib
import json
import random
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
AI_DIR = HERE.parent

sys.path.insert(0, str(AI_DIR))
sys.path.insert(0, str(HERE))

from rag_pipeline import RAGPipeline
from stress_cases_v3 import CASES


RESULTS = HERE / "results" / "stress_v3"
PROGRESS = RESULTS / "progress.json"
METADATA = RESULTS / "metadata.json"

MODES = ("baseline", "ask")

CRITERIA = (
    "decision_quality",
    "context_adaptation",
    "source_grounding",
    "uncertainty",
    "technical_safety",
)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    temp.replace(path)


def read_json(path, default):
    if not path.exists():
        return default
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def check_dataset():
    payload = json.dumps(
        CASES,
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")

    digest = hashlib.sha256(payload).hexdigest()

    if METADATA.exists():
        old = read_json(METADATA, {})
        if old.get("dataset_sha256") != digest:
            raise RuntimeError(
                "Dataset changed during benchmark. "
                "Do not mix old and new results."
            )
    else:
        write_json(
            METADATA,
            {
                "dataset_sha256": digest,
                "case_count": len(CASES),
                "modes": list(MODES),
                "top_k": 5,
                "scoring": list(CRITERIA),
                "scoring_range": [0, 2],
            },
        )


def generate(pipeline, question, mode):
    for attempt in range(7):
        try:
            return pipeline.ask(
                question,
                top_k=5,
                mode=mode,
            )
        except RuntimeError as exc:
            message = str(exc)

            if "429" not in message or attempt == 6:
                raise

            match = re.search(
                r"Retry-After:\s*(\d+)",
                message,
                flags=re.IGNORECASE,
            )
            delay = (
                int(match.group(1))
                if match else 30
            )
            delay = max(delay + 3, 5)

            print(
                f"RATE LIMIT: retry after {delay}s",
                flush=True,
            )
            time.sleep(delay)


def export_blind(progress):
    if len(progress) != len(CASES) * len(MODES):
        return

    rng = random.Random(20261114)
    blind = []
    answer_key = {}
    scores = []

    for case in CASES:
        modes = list(MODES)
        rng.shuffle(modes)

        answer_key[case["id"]] = {
            "A": modes[0],
            "B": modes[1],
        }

        responses = {}

        for label, mode in answer_key[
            case["id"]
        ].items():
            result = progress[
                f"{case['id']}::{mode}"
            ]

            responses[label] = {
                "answer": result["answer"],
                "sources": result["sources"],
            }

            row = {
                "case_id": case["id"],
                "response": label,
                **{key: "" for key in CRITERIA},
                "comments": "",
            }
            scores.append(row)

        blind.append({
            **case,
            "responses": responses,
        })

    write_json(
        RESULTS / "blind_review.json",
        blind,
    )

    write_json(
        RESULTS / "answer_key.json",
        answer_key,
    )

    score_path = RESULTS / "scores.csv"

    if not score_path.exists():
        with score_path.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=list(scores[0]),
            )
            writer.writeheader()
            writer.writerows(scores)

    print(
        "\nSTRESS BENCHMARK COMPLETE: "
        f"{len(CASES)} cases, "
        f"{len(progress)} responses",
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--batch",
        type=int,
        default=10,
        help="Maximum number of cases per execution",
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="Minimum pause between successful requests",
    )

    args = parser.parse_args()

    if args.batch < 1:
        parser.error("--batch must be positive")

    if args.delay < 0:
        parser.error("--delay cannot be negative")

    RESULTS.mkdir(parents=True, exist_ok=True)
    check_dataset()

    progress = read_json(PROGRESS, {})
    pipeline = RAGPipeline()

    pending = [
        case for case in CASES
        if any(
            f"{case['id']}::{mode}" not in progress
            for mode in MODES
        )
    ]

    selected = pending[:args.batch]

    if not selected:
        export_blind(progress)
        print("No pending cases.")
        return

    print(
        f"Starting batch: {len(selected)} cases; "
        f"{len(progress)}/120 saved",
        flush=True,
    )

    for case in selected:
        for mode in MODES:
            key = f"{case['id']}::{mode}"

            if key in progress:
                print("SKIP", key, flush=True)
                continue

            print("RUN", key, flush=True)

            try:
                result = generate(
                    pipeline,
                    case["question"],
                    mode,
                )
            except Exception as exc:
                print(
                    f"INTERRUPTED: {len(progress)}/120 "
                    f"saved. Error: {exc}",
                    flush=True,
                )
                raise SystemExit(1) from exc

            progress[key] = {
                "answer": result["answer"],
                "sources": result["sources"],
            }

            write_json(PROGRESS, progress)

            print(
                f"SAVED {len(progress)}/120",
                flush=True,
            )

            time.sleep(args.delay)

    export_blind(progress)

    if len(progress) < 120:
        print(
            f"\nBATCH FINISHED: {len(progress)}/120. "
            "Run the same command again.",
            flush=True,
        )


if __name__ == "__main__":
    main()
