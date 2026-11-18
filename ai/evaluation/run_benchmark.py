
import csv
import json
import random
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
EVAL_DIR = Path(__file__).resolve().parent
RESULTS_DIR = EVAL_DIR / "results"
PROGRESS_PATH = RESULTS_DIR / "progress.json"

sys.path.insert(0, str(BASE_DIR))

from rag_pipeline import RAGPipeline


def save_json(path, data):
    """Write safely, replacing only after serialization succeeds."""
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temp.replace(path)


def main():
    cases = json.loads(
        (EVAL_DIR / "decision_cases.json").read_text(
            encoding="utf-8"
        )
    )

    if not cases:
        raise ValueError("Evaluation dataset is empty")

    case_ids = [c["id"] for c in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("Duplicate evaluation IDs")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if PROGRESS_PATH.exists():
        progress = json.loads(
            PROGRESS_PATH.read_text(encoding="utf-8")
        )
    else:
        progress = {}

    expected_keys = {
        f"{case['id']}::{mode}"
        for case in cases
        for mode in ("baseline", "ask")
    }

    if not set(progress).issubset(expected_keys):
        raise ValueError(
            "Progress belongs to a different benchmark"
        )

    pipeline = RAGPipeline()

    for case in cases:
        for mode in ("baseline", "ask"):
            key = f"{case['id']}::{mode}"

            if key in progress:
                print(f"SKIP {key} - already completed")
                continue

            print(f"RUN {key}", flush=True)

            try:
                result = pipeline.ask(
                    case["question"],
                    top_k=5,
                    mode=mode,
                )
            except Exception as exc:
                print(f"\nBenchmark interrupted: {exc}")
                print(
                    "Completed answers saved:",
                    len(progress),
                    "/",
                    len(expected_keys),
                )
                print(
                    "Restart the script when API access "
                    "is available again."
                )
                raise SystemExit(1) from exc

            progress[key] = result
            save_json(PROGRESS_PATH, progress)

            print(
                f"SAVED {key} "
                f"({len(progress)}/{len(expected_keys)})",
                flush=True,
            )

    # Reaching this point means all responses exist.
    rng = random.Random(2026)

    review_data = []
    answer_key = {}
    score_rows = []

    for case in cases:
        modes = ["baseline", "ask"]
        rng.shuffle(modes)

        answer_key[case["id"]] = {
            "A": modes[0],
            "B": modes[1],
        }

        review_case = {
            "id": case["id"],
            "category": case["category"],
            "question": case["question"],
            "responses": {},
        }

        for label, mode in zip(("A", "B"), modes):
            result = progress[f"{case['id']}::{mode}"]

            review_case["responses"][label] = result

            score_rows.append({
                "case_id": case["id"],
                "response": label,
                "decision_match": "",
                "reasoning_quality": "",
                "source_grounding": "",
                "safety": "",
                "comments": "",
            })

        review_data.append(review_case)

    save_json(
        RESULTS_DIR / "blind_review.json",
        review_data,
    )

    save_json(
        RESULTS_DIR / "answer_key.json",
        answer_key,
    )

    with (RESULTS_DIR / "scores.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(score_rows[0]),
        )
        writer.writeheader()
        writer.writerows(score_rows)

    print("\nBENCHMARK COMPLETED")
    print(f"Cases: {len(cases)}")
    print(f"Answers: {len(progress)}")
    print("Results saved to:", RESULTS_DIR)


if __name__ == "__main__":
    main()
