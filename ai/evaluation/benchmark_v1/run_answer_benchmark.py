
"""Paired answer benchmark: Digital Twin vs baseline RAG.

Uses the existing RAGPipeline and configured LLM.
Does not modify production code.

Default: DEV-007 and DEV-012 = 4 LLM requests.
--all: all pilot questions = 24 LLM requests.

Results are saved incrementally so completed requests
are not repeated in subsequent runs.
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AI_ROOT = ROOT.parents[1]

sys.path.insert(0, str(AI_ROOT))

from rag_pipeline import RAGPipeline


def load_questions():
    path = ROOT / "questions.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        raise ValueError("questions.json must contain a list")

    ids = [q["id"] for q in data]

    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate question IDs")

    return data


def atomic_save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = path.with_suffix(".tmp")

    temp_path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    temp_path.replace(path)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all 12 pilot questions",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned requests without calling the LLM",
    )

    args = parser.parse_args()

    questions = load_questions()

    if not args.all:
        questions = [
            q for q in questions
            if q["id"] in {"DEV-007", "DEV-012"}
        ]

    if not questions:
        raise RuntimeError("No matching questions")

    modes = [
        ("digital_twin", "ask"),
        ("baseline_rag", "baseline"),
    ]

    output_path = (
        ROOT / "results" / "answer_responses.json"
    )

    if output_path.exists():
        saved = json.loads(
            output_path.read_text(encoding="utf-8")
        )

        if not isinstance(saved, list):
            raise ValueError(
                "Existing results must contain a list"
            )
    else:
        saved = []

    completed = {
        (row["case_id"], row["system"])
        for row in saved
        if isinstance(row, dict)
        and isinstance(row.get("answer"), str)
        and row["answer"].strip()
    }

    pending = [
        (q, system, mode)
        for q in questions
        for system, mode in modes
        if (q["id"], system) not in completed
    ]

    print("=" * 60)
    print("KNOWLEDGE LEGACY AI - ANSWER BENCHMARK")
    print("=" * 60)
    print("Questions selected:", len(questions))
    print("System variants:", len(modes))
    print("Requests already saved:",
          len(questions) * len(modes) - len(pending))
    print("Pending LLM requests:", len(pending))

    for q, system, mode in pending:
        print(f"  {q['id']} | {system} | mode={mode}")

    if args.dry_run:
        print("\nDRY RUN - no LLM requests")
        return

    if not pending:
        print("\nAll selected responses already saved.")
        return

    print("\nInitializing the existing RAGPipeline...")

    # Uses the existing production pipeline configuration.
    # If its constructor requires arguments, inspect the
    # real rag_pipeline.py and supply those exact arguments.
    pipeline = RAGPipeline()

    print("Pipeline initialized.")
    print("Starting requests...\n")

    for index, (q, system, mode) in enumerate(
        pending,
        start=1,
    ):
        print(
            f"[{index}/{len(pending)}] "
            f"{q['id']} | {system}"
        )

        started = time.perf_counter()

        try:
            result = pipeline.ask(
                question=q["question"],
                top_k=5,
                mode=mode,
            )
        except Exception as exc:
            print(
                f"FAILED {q['id']} {system}: "
                f"{type(exc).__name__}: {exc}"
            )
            print(
                "Stopping. Saved successful results "
                "will not be requested again."
            )
            raise SystemExit(1) from None

        elapsed = time.perf_counter() - started

        if not isinstance(result, dict):
            raise TypeError(
                f"Expected dict from ask(), "
                f"got {type(result).__name__}"
            )

        answer = result.get("answer")
        sources = result.get("sources", [])

        if not isinstance(answer, str) or not answer.strip():
            raise ValueError(
                f"Empty answer: {q['id']} {system}"
            )

        if not isinstance(sources, list):
            raise TypeError(
                "Pipeline sources must be a list"
            )

        record = {
            "case_id": q["id"],
            "category": q["category"],
            "system": system,
            "mode": mode,
            "question": q["question"],
            "answer": answer,
            "sources": sources,
            "latency_seconds": round(elapsed, 3),
            "timestamp_utc": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        saved.append(record)
        atomic_save(output_path, saved)

        print(
            f"  Saved | latency={elapsed:.2f}s"
            f" | sources={len(sources)}"
        )

    print("\n" + "=" * 60)
    print("BENCHMARK REQUESTS COMPLETED")
    print("Output:", output_path)
    print("Saved records:", len(saved))
    print("No scores assigned automatically.")


if __name__ == "__main__":
    main()
