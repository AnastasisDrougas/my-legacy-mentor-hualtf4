
import csv
import hashlib
import json
import random
import sys
from pathlib import Path

AI_DIR = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent

CASES = HERE / "decision_cases_v2.json"
RESULTS = HERE / "results" / "holdout_v2"
PROGRESS = RESULTS / "progress.json"

sys.path.insert(0, str(AI_DIR))

from rag_pipeline import RAGPipeline


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    tmp.replace(path)


def main():
    raw = CASES.read_bytes()
    cases = json.loads(raw)

    if len(cases) != 10:
        raise ValueError("Expected 10 evaluation cases")

    if len({c["id"] for c in cases}) != 10:
        raise ValueError("Duplicate case IDs")

    RESULTS.mkdir(parents=True, exist_ok=True)

    fingerprint = hashlib.sha256(raw).hexdigest()
    metadata_path = RESULTS / "metadata.json"

    if metadata_path.exists():
        metadata = json.loads(
            metadata_path.read_text(encoding="utf-8")
        )
        if metadata["cases_sha256"] != fingerprint:
            raise ValueError(
                "Evaluation cases changed. "
                "Do not mix benchmark results."
            )
    else:
        save_json(
            metadata_path,
            {
                "cases_sha256": fingerprint,
                "modes": ["baseline", "ask"],
                "top_k": 5,
            },
        )

    progress = (
        json.loads(PROGRESS.read_text(encoding="utf-8"))
        if PROGRESS.exists()
        else {}
    )

    pipeline = RAGPipeline()

    for case in cases:
        for mode in ("baseline", "ask"):
            key = f"{case['id']}::{mode}"

            if key in progress:
                print("SKIP", key, flush=True)
                continue

            print("RUN", key, flush=True)

            try:
                result = pipeline.ask(
                    case["question"],
                    top_k=5,
                    mode=mode,
                )
            except Exception as exc:
                print(
                    f"Interrupted: {len(progress)}/20. "
                    f"Reason: {exc}"
                )
                raise SystemExit(1) from exc

            progress[key] = {
                "answer": result["answer"],
                "sources": result["sources"],
            }

            save_json(PROGRESS, progress)
            print(
                f"SAVED {len(progress)}/20",
                flush=True,
            )

    rng = random.Random(20261114)

    blind = []
    keymap = {}
    score_rows = []

    for case in cases:
        modes = ["baseline", "ask"]
        rng.shuffle(modes)

        keymap[case["id"]] = {
            "A": modes[0],
            "B": modes[1],
        }

        responses = {}

        for label, mode in keymap[case["id"]].items():
            responses[label] = progress[
                f"{case['id']}::{mode}"
            ]

            score_rows.append({
                "case_id": case["id"],
                "response": label,
                "decision_match": "",
                "reasoning_quality": "",
                "source_grounding": "",
                "safety": "",
                "comments": "",
            })

        blind.append({
            "id": case["id"],
            "category": case["category"],
            "question": case["question"],
            "responses": responses,
        })

    save_json(RESULTS / "blind_review.json", blind)
    save_json(RESULTS / "answer_key.json", keymap)

    score_path = RESULTS / "scores.csv"

    if not score_path.exists():
        with score_path.open(
            "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=list(score_rows[0]),
            )
            writer.writeheader()
            writer.writerows(score_rows)

    print("\nBENCHMARK COMPLETE: 10 cases, 20 answers")


if __name__ == "__main__":
    main()
