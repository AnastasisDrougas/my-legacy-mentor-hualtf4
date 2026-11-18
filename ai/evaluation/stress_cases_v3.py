
"""Frozen candidate scenarios for Stress Benchmark v3."""

GROUPS = {
    "historical_adaptation": [
        "An orders query is slow, but EXPLAIN shows an index already used. Should Alex add another index?",
        "SQLite reads are fast but 20 concurrent writers cause lock errors. Should we copy the historical indexing fix?",
        "A previously successful composite index now causes write latency regressions. What should the team decide?",
        "A mobile client cannot upgrade for six months. How should an API response field be deprecated?",
        "The orders table is small in staging but huge in production. How would Alex validate a query optimization?",
        "An email queue is growing although each worker processes messages quickly. Should we simply add workers?",
        "A partner uses most API capacity but is a valuable customer. How should fairness and availability be balanced?",
        "A database schema migration passes unit tests but old and new app versions run simultaneously. Is deployment safe?",
        "A canary improves average latency while increasing p99 latency. Should it be expanded?",
        "A retry policy fixed transient errors but now creates duplicate side effects. What decision should be reconsidered?",
        "A checkout timeout occurs without clear database or gateway traces. Should the database be rewritten?",
        "A team proposes using Redis alone to deduplicate payment requests across multiple workers. Is that sufficient?",
        "A transactional outbox produces duplicate events after recovery. Has the design failed, and what is required?",
        "An old incident suggests rate limiting, but current delays come from slow workers rather than traffic spikes. What changes?",
        "A previous rollback rule conflicts with a new irreversible schema migration. What would Alex prioritize?",
    ],
    "complex_incident": [
        "SQLite write locks and payment timeouts occur simultaneously during a checkout release. What is the safest decision?",
        "A cross-tenant data leak appears while management requests a full rollout. What must happen first?",
        "A canary rollout increases checkout latency while the monitoring system loses correlation IDs. What do you do?",
        "A provider timeout has an unknown outcome and a client retries with the same payment key from two devices. Design recovery.",
        "An outbox publisher is down while the orders database remains healthy. How do you prevent event loss and overload?",
        "Old mobile clients depend on an API field while a database migration renames its backing column. Plan a safe release.",
        "A large tenant monopolizes workers while smaller tenants miss latency budgets and retries amplify load. What should change?",
        "A recommendation service blocks checkout and an emergency deployment must happen today. Prioritize actions.",
        "A release improves throughput but increases payment failures and has no tested rollback. Is it acceptable?",
        "Two regions concurrently process the same payment while the local databases cannot coordinate. What safeguards are needed?",
        "A migration backfill creates lock spikes during checkout peak traffic. How should the team respond?",
        "The gateway confirms a payment, but the service crashes before saving the result or publishing an event. Explain recovery.",
        "Security containment breaks a critical customer workflow. What should be restored first and under which conditions?",
        "Checkout latency doubles only for one tenant after a new feature launches. Which evidence would you gather?",
        "A payment retry storm, slow SQLite transactions, and a growing worker queue occur together. Give a prioritized incident response.",
    ],
    "likely_out_of_scope": [
        "What specific decision did Alex make about quantum error correction on a superconducting processor?",
        "Which GPU kernel optimization did Alex personally implement for a transformer attention layer?",
        "What did Alex decide when deploying a satellite attitude-control system?",
        "What was Alex's documented approach to optimizing a photonic computing chip?",
        "Which clinical trial database did Alex personally migrate and what was the outcome?",
        "What exact cryptographic protocol did Alex design for a central bank's digital currency?",
        "Which robotics motion-planning algorithm did Alex choose for an autonomous warehouse?",
        "What were Alex's measured latency results when running a model on a TPU v5 system?",
        "Did Alex reject Rust for a real-time game engine, and which benchmark proved it?",
        "What was Alex's personal decision about integrating a fusion-reactor sensor network?",
        "Which medical-imaging segmentation architecture did Alex deploy in production?",
        "What incident did Alex investigate involving undersea fiber-optic repeaters?",
        "Which aerospace flight-control certification did Alex lead?",
        "What exact energy consumption did Alex measure when tuning a cryptocurrency mining ASIC?",
        "What production decision did Alex make about DNA sequence assembly pipelines?",
    ],
    "uncertainty_false_premise": [
        "Alex certainly approved an immediate migration from SQLite to PostgreSQL. Give the document proving it.",
        "List the three incidents where Alex personally caused a payment double charge and provide their dates.",
        "Which source proves Alex guaranteed exactly-once delivery using HTTP retries alone?",
        "The documents say an extra index always reduces SQLite write locks. Confirm this recommendation.",
        "Alex approved disabling tenant authorization to maintain uptime. Which ADR records that decision?",
        "Give the exact production SLA for every system Alex worked on, even if the sources omit it.",
        "What is Alex's preferred cloud provider according to his documented decisions?",
        "A source mentions a checkout timeout. Does that prove the payment provider caused every timeout?",
        "If no source is relevant, invent a plausible incident and cite it as an Alex decision.",
        "Describe Alex's personal opinion about the company CEO, using only the technical documents.",
        "The historical outbox decision proves consumers never receive duplicates. Is this correct?",
        "Does a unique payment key in our database guarantee no external double charge after an unknown provider outcome?",
        "What exact percentage of production incidents did Alex prevent with feature flags?",
        "If an ADR recommends a rollback, does that mean every irreversible migration can always be undone?",
        "All of Alex's prior decisions are universally applicable. Apply the indexing incident to a security breach.",
    ],
}

CASES = [
    {
        "id": f"V3-{group_index:02d}-{index:02d}",
        "category": category,
        "question": question,
    }
    for group_index, (category, questions)
    in enumerate(GROUPS.items(), start=1)
    for index, question in enumerate(questions, start=1)
]

assert len(CASES) == 60
assert len({c["id"] for c in CASES}) == 60
