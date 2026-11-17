
import re

SOURCE_ID_RE = re.compile(
    r"\b(?:ADR|COM|DOC|INC|PR|MENTOR)-\d{3}\b",
    flags=re.IGNORECASE,
)


class CitationAuditor:

    @staticmethod
    def audit(answer: str, sources: list[dict]) -> dict:
        if not isinstance(answer, str):
            raise TypeError("answer must be a string")

        if not isinstance(sources, list):
            raise TypeError("sources must be a list")

        allowed_ids = {
            item["source_id"].upper()
            for item in sources
        }

        cited_ids = {
            match.upper()
            for match in SOURCE_ID_RE.findall(answer)
        }

        unsupported = sorted(cited_ids - allowed_ids)
        supported = sorted(cited_ids & allowed_ids)

        return {
            "passed": len(unsupported) == 0,
            "cited_ids": sorted(cited_ids),
            "supported_ids": supported,
            "unsupported_ids": unsupported,
            "retrieved_ids": sorted(allowed_ids),
        }
