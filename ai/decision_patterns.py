
import json
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

INPUT_PATH = (
    BASE_DIR / "data" / "synthetic" / "knowledge.jsonl"
)

OUTPUT_PATH = (
    BASE_DIR / "data" / "derived" / "decision_patterns.json"
)


def load_records(path=INPUT_PATH):
    records = []

    with Path(path).open(encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))

    return records


def extract_patterns(records):
    if not records:
        raise ValueError("Cannot extract from empty dataset")

    grouped = defaultdict(list)

    for record in records:
        tags = record.get("tags", [])

        # Dataset generator stores:
        # [scenario_slug, principle, document_type, ...]
        if len(tags) < 2:
            continue

        principle = tags[1]
        grouped[principle].append(record)

    patterns = []

    for principle, evidence in sorted(grouped.items()):
        # ADRs express the actual documented decision.
        decisions = [
            r for r in evidence
            if r["type"] == "architecture_decision"
        ]

        if not decisions:
            continue

        source_ids = sorted({
            r["id"] for r in evidence
        })

        patterns.append({
            "pattern_id": principle,
            "senior_id": "senior_001",
            "principle": principle.replace("_", " "),
            "observed_decisions": [
                {
                    "source_id": r["id"],
                    "context": r["context"],
                    "decision": r["decision"],
                    "reasoning": r["reasoning"],
                    "trade_offs": r.get("trade_offs", []),
                }
                for r in decisions
            ],
            "evidence_ids": source_ids,
            "evidence_count": len(source_ids),
            "scenario_count": len(decisions),
        })

    return patterns


def build_patterns(
    input_path=INPUT_PATH,
    output_path=OUTPUT_PATH,
):
    records = load_records(input_path)
    patterns = extract_patterns(records)

    result = {
        "senior_id": "senior_001",
        "extraction_method": "tag_grouping_v1",
        "source_record_count": len(records),
        "pattern_count": len(patterns),
        "patterns": patterns,
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return result


if __name__ == "__main__":
    result = build_patterns()

    print("DECISION PATTERN EXTRACTION COMPLETED")
    print("Source records:", result["source_record_count"])
    print("Patterns:", result["pattern_count"])

    for pattern in result["patterns"]:
        print(
            f"- {pattern['pattern_id']}: "
            f"{pattern['scenario_count']} scenarios, "
            f"{pattern['evidence_count']} records"
        )
