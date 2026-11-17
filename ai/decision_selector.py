
import json
from pathlib import Path

PATTERNS_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "derived"
    / "decision_patterns.json"
)


class DecisionPatternSelector:
    def __init__(self, path=PATTERNS_PATH):
        self.path = Path(path)

        if not self.path.exists():
            raise FileNotFoundError(
                "Decision patterns missing. "
                "Run python ai/decision_patterns.py"
            )

        data = json.loads(
            self.path.read_text(encoding="utf-8")
        )

        self.senior_id = data["senior_id"]
        self.patterns = data["patterns"]

    def select(self, retrieved_sources, top_k=3):
        """
        Select patterns supported by retrieved source IDs.
        Do not introduce unrelated historical evidence.
        """
        if top_k < 1:
            raise ValueError("top_k must be positive")

        source_ids = {
            item["metadata"]["source_id"]
            for item in retrieved_sources
        }

        matches = []

        for pattern in self.patterns:
            evidence_ids = set(pattern["evidence_ids"])
            matched_ids = evidence_ids & source_ids

            if not matched_ids:
                continue

            decisions = [
                decision
                for decision in pattern["observed_decisions"]
                if decision["source_id"] in source_ids
            ]

            matches.append({
                "pattern_id": pattern["pattern_id"],
                "principle": pattern["principle"],
                "matched_evidence_ids": sorted(matched_ids),
                "match_count": len(matched_ids),
                "decisions": decisions,
            })

        matches.sort(
            key=lambda p: (
                -p["match_count"],
                p["pattern_id"],
            )
        )

        return matches[:top_k]

    def format_for_prompt(self, selected_patterns):
        if not selected_patterns:
            return (
                "No directly supported personal "
                "decision patterns were found."
            )

        sections = []

        for pattern in selected_patterns:
            lines = [
                f"Pattern: {pattern['pattern_id']}",
                f"Principle: {pattern['principle']}",
                "Supporting source IDs: "
                + ", ".join(
                    pattern["matched_evidence_ids"]
                ),
            ]

            for decision in pattern["decisions"]:
                lines.extend([
                    f"Decision source: {decision['source_id']}",
                    f"Context: {decision['context']}",
                    f"Decision: {decision['decision']}",
                    f"Reasoning: {decision['reasoning']}",
                    "Trade-offs: " + "; ".join(
                        decision["trade_offs"]
                    ),
                ])

            sections.append("\n".join(lines))

        return "\n\n---\n\n".join(sections)
