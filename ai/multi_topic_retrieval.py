
import re
from collections import OrderedDict


TOPICS = {
    "database": {
        "patterns": (
            r"\bsqlite\b",
            r"\bdatabase\b",
            r"\bwrite.lock\w*\b",
            r"\bdb contention\b",
        ),
        "query": (
            "SQLite database write lock contention "
            "long transactions measure before migrating "
            "index write cost historical decision"
        ),
    },
    "payments": {
        "patterns": (
            r"\bpayment\w*\b",
            r"\bcharge\w*\b",
            r"\bidempoten\w*\b",
            r"\bgateway\b",
        ),
        "query": (
            "payment provider timeout unknown outcome "
            "duplicate charge idempotency retry "
            "reconciliation historical decision"
        ),
    },
    "deployment": {
        "patterns": (
            r"\bdeploy\w*\b",
            r"\brelease\b",
            r"\bfeature[-_ ]flag\w*\b",
            r"\brollout\b",
            r"\bcanary\b",
        ),
        "query": (
            "production deployment release decision "
            "canary rollback feature flag "
            "performance guardrails"
        ),
    },
}


def detect_topics(question: str) -> list[str]:
    if not isinstance(question, str):
        raise TypeError("question must be a string")

    value = question.casefold()

    return [
        name
        for name, config in TOPICS.items()
        if any(
            re.search(pattern, value)
            for pattern in config["patterns"]
        )
    ]


def source_identity(item: dict) -> str:
    """
    Deduplicate retrieved chunks by their source ID,
    falling back to an ID or textual representation.
    """

    if not isinstance(item, dict):
        raise TypeError("retrieval result must be a dict")

    metadata = item.get("metadata") or {}

    if not isinstance(metadata, dict):
        metadata = {}

    source_id = (
        metadata.get("source_id")
        or item.get("source_id")
        or item.get("id")
    )

    if source_id is not None:
        return str(source_id)

    return repr(item)


class MultiTopicRetriever:
    """
    Adapter around an existing retriever.

    Uses the original retrieval for single-topic queries.
    For multi-topic queries, retrieves per topic, merges
    deterministically and limits the evidence budget.

    Does not alter the returned item structure.
    """

    def __init__(
        self,
        retriever,
        max_topics=3,
        per_topic_k=4,
    ):
        self.retriever = retriever
        self.max_topics = max_topics
        self.per_topic_k = per_topic_k

    def search(self, question, top_k=5):
        if top_k < 1:
            raise ValueError("top_k must be positive")

        topics = detect_topics(question)[:self.max_topics]

        if len(topics) < 2:
            return self.retriever.search(
                question,
                top_k=top_k,
            )

        original = self.retriever.search(
            question,
            top_k=top_k,
        )

        topic_results = []

        for topic in topics:
            result = self.retriever.search(
                TOPICS[topic]["query"],
                top_k=self.per_topic_k,
            )
            topic_results.append(result)

        selected = OrderedDict()

        # First pass: give each detected topic one
        # opportunity to contribute a distinct source.
        for results in topic_results:
            for item in results:
                key = source_identity(item)
                if key not in selected:
                    selected[key] = item
                    break

            if len(selected) >= top_k:
                return list(selected.values())

        # Preserve useful original-query evidence.
        for item in original:
            selected.setdefault(
                source_identity(item),
                item,
            )

            if len(selected) >= top_k:
                return list(selected.values())

        # Fill remaining slots from specialized searches.
        for results in topic_results:
            for item in results:
                selected.setdefault(
                    source_identity(item),
                    item,
                )

                if len(selected) >= top_k:
                    return list(selected.values())

        return list(selected.values())
