
import json
from collections import Counter
from pathlib import Path

from pydantic import ValidationError

from dataset_schema import KnowledgeRecord


DATA_DIR = Path(__file__).parent / "data" / "synthetic"


def main():
    profile = json.loads(
        (DATA_DIR / "senior_profile.json").read_text(
            encoding="utf-8"
        )
    )

    senior_id = profile["senior_id"]
    records = []

    path = DATA_DIR / "knowledge.jsonl"

    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.strip():
            continue

        try:
            record = KnowledgeRecord.model_validate_json(line)
        except ValidationError as exc:
            raise ValueError(
                f"Invalid record at line {line_number}: {exc}"
            ) from exc

        if record.senior_id != senior_id:
            raise ValueError(
                f"Senior mismatch in {record.id}"
            )

        records.append(record)

    if not records:
        raise ValueError("Dataset is empty")

    ids = [record.id for record in records]

    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate record IDs")

    known_ids = set(ids)

    for record in records:
        for related_id in record.related_ids:
            if related_id not in known_ids:
                raise ValueError(
                    f"{record.id}: unknown reference {related_id}"
                )

    print("DATASET VALIDATION PASSED")
    print(f"Senior: {senior_id}")
    print(f"Total records: {len(records)}")
    print("Types:", dict(Counter(r.type for r in records)))


if __name__ == "__main__":
    main()
