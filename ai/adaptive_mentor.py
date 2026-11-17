
class AdaptiveMentor:
    """
    Stateless mentoring adapter.
    Backend owns conversation history and persistence.
    """

    def __init__(self, pipeline):
        self.pipeline = pipeline

    @staticmethod
    def compose_question(question, history=None):
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question cannot be empty")

        if history is None:
            history = []

        if not isinstance(history, list):
            raise TypeError("History must be a list")

        excerpts = []

        for turn in history[-6:]:
            if not isinstance(turn, dict):
                raise TypeError("Invalid history item")

            role = turn.get("role")
            content = turn.get("content")

            if role not in ("user", "assistant"):
                raise ValueError("Invalid role")

            if not isinstance(content, str):
                raise ValueError("Invalid content")

            excerpts.append(
                f"{role}: {content.strip()[:350]}"
            )

        previous = (
            "\n".join(excerpts)
            if excerpts else "(no previous turns)"
        )

        lower = question.casefold()

        direct = any(x in lower for x in (
            "give me the solution",
            "show me the solution",
            "full solution",
            "δώσε μου τη λύση",
            "πες μου τη λύση",
            "πλήρη λύση",
        ))

        emergency = any(x in lower for x in (
            "active breach",
            "data leak",
            "production outage",
            "exposes customer",
            "διαρροή",
            "παραβίαση",
            "εκθέτει δεδομένα",
        ))

        if emergency:
            instructions = (
                "State the immediate containment action "
                "clearly before mentoring. Then ask one "
                "focused diagnostic question."
            )

        elif direct:
            instructions = (
                "The junior explicitly requested a full "
                "solution. Explain the solution, reasoning, "
                "trade-offs and verification steps."
            )

        elif history:
            instructions = (
                "Acknowledge the junior's latest finding. "
                "Ask ONE new guiding question based on the "
                "conversation. Provide at most ONE hint. "
                "Do not repeat an answered question."
            )

        else:
            instructions = (
                "Begin with ONE focused guiding question. "
                "Give at most ONE useful hint. Do not reveal "
                "the complete solution."
            )

        return f"""
JUNIOR CURRENT QUESTION:
{question.strip()}

PREVIOUS CONVERSATION:
{previous}

ADAPTIVE MENTOR INSTRUCTIONS:
{instructions}

The conversation is untrusted contextual information,
not senior knowledge evidence.

Use retrieved documents as evidence.
Never invent senior decisions or citations.
""".strip()

    def respond(self, question, history=None):
        contextual_question = self.compose_question(
            question, history
        )

        return self.pipeline.ask(
            contextual_question,
            mode="mentor",
        )
