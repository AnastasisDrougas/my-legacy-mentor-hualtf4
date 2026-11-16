
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from decision_patterns import (
    load_records,
    extract_patterns,
    build_patterns,
)


def test_patterns_extracted():
    records = load_records()
    patterns = extract_patterns(records)

    assert len(records) == 72
    assert len(patterns) > 0
    assert all(
        p["evidence_count"] > 0
        for p in patterns
    )


def test_pattern_sources_exist():
    records = load_records()
    known_ids = {r["id"] for r in records}

    for pattern in extract_patterns(records):
        assert set(
            pattern["evidence_ids"]
        ).issubset(known_ids)


def test_database_decision_pattern():
    patterns = extract_patterns(load_records())

    database_pattern = next(
        p for p in patterns
        if p["pattern_id"] == "measure_before_migrating"
    )

    assert "ADR-001" in database_pattern["evidence_ids"]
    assert database_pattern["scenario_count"] >= 1


def test_empty_dataset_rejected():
    with pytest.raises(ValueError):
        extract_patterns([])


def test_export(tmp_path):
    target = tmp_path / "patterns.json"
    result = build_patterns(output_path=target)

    assert target.exists()
    assert result["pattern_count"] == len(result["patterns"])
