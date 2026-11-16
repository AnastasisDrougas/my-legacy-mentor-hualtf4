
import re


class CriticalDecisionGuard:

    @staticmethod
    def detect(question: str) -> set[str]:
        if not isinstance(question, str):
            raise TypeError("question must be a string")

        q = question.casefold()
        categories = set()

        payment = re.search(
            r"\b(payment|payments|charge|charges|"
            r"χρέωση|χρεώσεις|πληρωμή|πληρωμές)\b",
            q,
        )
        retry = re.search(
            r"\b(retry|retries|duplicate|idempoten\w*|"
            r"race|concurrent|διπλ\w*|επανάληψ\w*)\b",
            q,
        )

        if payment and retry:
            categories.add("payment_idempotency")

        tenant = re.search(
            r"\b(tenant|tenants|cross-tenant|"
            r"authorization|unauthorized|"
            r"εξουσιοδότηση|διαρροή)\b",
            q,
        )
        if tenant and re.search(
            r"\b(expos\w*|leak\w*|access|breach|"
            r"vulnerab\w*|διαρροή|παραβίαση)\b",
            q,
        ):
            categories.add("security_exposure")

        return categories

    @classmethod
    def build_prompt(cls, question: str) -> str:
        categories = cls.detect(question)
        rules = []

        if "payment_idempotency" in categories:
            rules.append("""
PAYMENT RACE SAFETY:
- A local UNIQUE constraint alone does not guarantee
  exactly one external charge.
- Persist and commit an atomic idempotency reservation
  before initiating an external payment.
- Only the authorized owner of a pending operation
  may submit it to the external provider.
- Repeated requests must not independently submit
  the same payment.
- Use provider-side idempotency when available.
- Handle timeouts and uncertain external outcomes
  with status checks or reconciliation.
- Never assume a retry is safe merely because the
  initial response was lost.
- Test concurrent requests and crash recovery.
- Do not hold a database transaction open during
  a slow external provider call as the default
  solution.
""".strip())

        if "security_exposure" in categories:
            rules.append("""
ACTIVE DATA EXPOSURE SAFETY:
- Stop unauthorized access immediately.
- Do not keep a known vulnerable route exposed
  while waiting for a permanent patch.
- Distinguish containment from final remediation.
- Validate authorization boundaries with negative
  tests before restoring access.
- Do not falsely claim a vulnerability is fixed
  without verification.
""".strip())

        if not rules:
            return ""

        return (
            "CRITICAL ENGINEERING CORRECTNESS GUARDRAILS\n\n"
            + "\n\n".join(rules)
            + "\n\nThese are technical safety constraints, "
            "not evidence of undocumented personal "
            "decisions by the senior."
        )
