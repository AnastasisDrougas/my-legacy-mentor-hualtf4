
from ai.decision_calibration import DecisionCalibration
from ai.citation_audit import CitationAuditor


def test_definition_questions_get_scope_instructions():
    prompt = DecisionCalibration.build_prompt()

    assert "technology-agnostic definition" in prompt
    assert "historical example" in prompt.lower()
    assert "Do not force recommendations" in prompt


def test_upload_citation_is_recognized():
    result = CitationAuditor.audit(
        "Found in the new document "
        "[UPLOAD-a5a702288fd5f4edcea5].",
        [
            {
                "source_id":
                    "UPLOAD-a5a702288fd5f4edcea5"
            }
        ],
    )

    assert result["passed"] is True
    assert result["supported_ids"] == [
        "UPLOAD-A5A702288FD5F4EDCEA5"
    ]


def test_fabricated_upload_citation_is_caught():
    result = CitationAuditor.audit(
        "See [UPLOAD-deadbeef].",
        [],
    )

    assert result["passed"] is False
    assert result["unsupported_ids"] == [
        "UPLOAD-DEADBEEF"
    ]


def test_non_numeric_fabricated_adr_is_caught():
    result = CitationAuditor.audit(
        "See [ADR-FAKE].",
        [],
    )

    assert result["passed"] is False
    assert result["unsupported_ids"] == [
        "ADR-FAKE"
    ]
