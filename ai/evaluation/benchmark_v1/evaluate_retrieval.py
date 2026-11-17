
"""Offline retrieval evaluation for Knowledge Legacy AI.

Compares:
- Digital Twin Ask retrieval: MultiTopicRetriever
- Baseline RAG retrieval: SeniorRetriever

Metrics:
Precision@5, Recall@5, F1@5, AP@5,
MRR@5, nDCG@5.

IMPORTANT:
The current qrels are preliminary suggestions.
Scores are pilot diagnostics, NOT final verified metrics.

No Gemini calls. No production code changes.
"""

import csv
import json
import math
from pathlib import Path

from retrieval import SeniorRetriever
from multi_topic_retrieval import MultiTopicRetriever


ROOT = Path(__file__).resolve().parent
K = 5


def load_json(name):
    with (ROOT / name).open(encoding="utf-8") as f:
        return json.load(f)


def get_source_ids(retriever, question, k=K):
    # Match the existing RAGPipeline retrieval budget:
    # retrieve up to max(k * 3, 10) candidates,
    # then keep the first k unique source IDs.
    candidates = retriever.search(
        question,
        top_k=max(k * 3, 10),
    )

    ids = []
    seen = set()

    for item in candidates:
        source_id = item["metadata"]["source_id"]

        if source_id not in seen:
            seen.add(source_id)
            ids.append(source_id)

        if len(ids) >= k:
            break

    return ids


def evaluate_one(retrieved, qrels, k=K):
    relevant = {
        source_id
        for source_id, grade in qrels.items()
        if grade > 0
    }

    if not relevant:
        raise ValueError(
            "Retrieval metrics require at least one "
            "relevant source. Evaluate unknown cases "
            "separately using abstention metrics."
        )

    hits = [
        1 if source_id in relevant else 0
        for source_id in retrieved[:k]
    ]

    true_positives = sum(hits)

    precision = true_positives / k
    recall = true_positives / len(relevant)

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall > 0
        else 0.0
    )

    # AP@k with standard truncated normalization.
    hit_count = 0
    ap_sum = 0.0

    for rank, hit in enumerate(hits, start=1):
        if hit:
            hit_count += 1
            ap_sum += hit_count / rank

    ap = ap_sum / min(len(relevant), k)

    reciprocal_rank = 0.0

    for rank, hit in enumerate(hits, start=1):
        if hit:
            reciprocal_rank = 1.0 / rank
            break

    def dcg(grades):
        return sum(
            (2 ** grade - 1) / math.log2(rank + 1)
            for rank, grade in enumerate(grades, start=1)
        )

    retrieved_grades = [
        qrels.get(source_id, 0)
        for source_id in retrieved[:k]
    ]

    ideal_grades = sorted(
        qrels.values(),
        reverse=True,
    )[:k]

    actual_dcg = dcg(retrieved_grades)
    ideal_dcg = dcg(ideal_grades)

    ndcg = (
        actual_dcg / ideal_dcg
        if ideal_dcg > 0
        else 0.0
    )

    return {
        "precision_at_5": precision,
        "recall_at_5": recall,
        "f1_at_5": f1,
        "ap_at_5": ap,
        "mrr_at_5": reciprocal_rank,
        "ndcg_at_5": ndcg,
        "relevant_found": true_positives,
        "total_relevant": len(relevant),
    }


def average(rows, key):
    return (
        sum(row[key] for row in rows) / len(rows)
        if rows else 0.0
    )


def main():
    questions = load_json("questions.json")
    qrels = load_json("qrels.json")
    references = load_json("references.json")

    ids = [item["id"] for item in questions]

    if not ids or len(ids) != len(set(ids)):
        raise ValueError(
            "Questions must have unique nonempty IDs"
        )

    if set(ids) != set(qrels):
        raise ValueError(
            "Question IDs and qrels IDs differ"
        )

    if set(ids) != set(references):
        raise ValueError(
            "Question IDs and reference IDs differ"
        )

    base = SeniorRetriever()

    systems = {
        "digital_twin": MultiTopicRetriever(
            retriever=base,
            max_topics=3,
            per_topic_k=5,
        ),
        "baseline_rag": base,
    }

    results = []

    metric_names = [
        "precision_at_5",
        "recall_at_5",
        "f1_at_5",
        "ap_at_5",
        "mrr_at_5",
        "ndcg_at_5",
    ]

    for question in questions:
        case_id = question["id"]
        question_text = question["question"]
        gold = qrels[case_id]

        if not gold:
            print(
                f"SKIPPED {case_id}: no relevant "
                "sources defined"
            )
            continue

        if any(
            not isinstance(grade, int)
            or isinstance(grade, bool)
            or grade not in (0, 1, 2)
            for grade in gold.values()
        ):
            raise ValueError(
                f"Invalid qrel grade in {case_id}"
            )

        for system_name, retriever in systems.items():
            retrieved = get_source_ids(
                retriever,
                question_text,
            )

            metrics = evaluate_one(
                retrieved,
                gold,
            )

            row = {
                "case_id": case_id,
                "category": question["category"],
                "system": system_name,
                "retrieved_ids": "|".join(retrieved),
                **metrics,
            }

            results.append(row)

            print(
                f"{case_id:8s} "
                f"{system_name:14s} "
                f"P={metrics['precision_at_5']:.3f} "
                f"R={metrics['recall_at_5']:.3f} "
                f"F1={metrics['f1_at_5']:.3f} "
                f"AP={metrics['ap_at_5']:.3f}"
            )

    output_dir = ROOT / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not results:
        raise ValueError(
            "No cases available for retrieval evaluation"
        )

    per_question_path = (
        output_dir / "retrieval_per_question.csv"
    )

    with per_question_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(results[0].keys()),
        )
        writer.writeheader()
        writer.writerows(results)

    summary = {}

    for system_name in systems:
        subset = [
            row
            for row in results
            if row["system"] == system_name
        ]

        summary[system_name] = {
            "evaluated_questions": len(subset),
            **{
                metric: average(subset, metric)
                for metric in metric_names
            },
        }

    report = {
        "benchmark": "knowledge_legacy_ai_pilot_v1",
        "status": "PROVISIONAL_NOT_FINAL",
        "ground_truth_review": "PENDING",
        "top_k": K,
        "scoring_unit": "unique source_id",
        "systems": summary,
    }

    summary_path = (
        output_dir / "retrieval_summary.json"
    )

    summary_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    print("\n" + "=" * 64)
    print("PILOT RETRIEVAL SUMMARY")
    print("=" * 64)

    for system_name, values in summary.items():
        print(f"\n{system_name.upper()}")

        for metric in metric_names:
            print(
                f"  {metric:20s}"
                f"{values[metric]:.4f}"
            )

    print("\nFILES:")
    print(per_question_path)
    print(summary_path)

    print(
        "\nWARNING: QRELS HAVE NOT BEEN "
        "INDEPENDENTLY VALIDATED."
    )
    print("No Gemini calls were made.")


if __name__ == "__main__":
    main()
