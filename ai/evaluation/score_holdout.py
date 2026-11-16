
import csv
import json
from collections import defaultdict
from pathlib import Path

RESULTS = (
    Path(__file__).resolve().parent
    / "results"
    / "holdout_v2"
)

FIELDS = (
    "decision_match",
    "reasoning_quality",
    "source_grounding",
    "safety",
)


def main():
    keymap = json.loads(
        (RESULTS / "answer_key.json").read_text(
            encoding="utf-8"
        )
    )

    with (RESULTS / "scores.csv").open(
        encoding="utf-8",
        newline="",
    ) as file:
        rows = list(csv.DictReader(file))

    if len(rows) != 20:
        raise ValueError("Expected 20 scored answers")

    totals = defaultdict(int)
    counts = defaultdict(int)

    for row in rows:
        values = []

        for field in FIELDS:
            value = row[field]

            if value not in ("0", "1", "2"):
                raise ValueError(
                    f"Missing or invalid score: "
                    f"{row['case_id']} {row['response']}"
                )

            values.append(int(value))

        mode = keymap[row["case_id"]][
            row["response"]
        ]

        totals[mode] += sum(values)
        counts[mode] += 1

    for mode in ("baseline", "ask"):
        print(
            f"{mode}: {totals[mode]}/80 "
            f"({counts[mode]} responses)"
        )


if __name__ == "__main__":
    main()
