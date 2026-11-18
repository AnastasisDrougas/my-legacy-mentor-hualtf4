
import json
import re
import time
from pathlib import Path

from adaptive_mentor import AdaptiveMentor
from rag_pipeline import RAGPipeline

PROGRESS = (
    Path(__file__).resolve().parent
    / "evaluation"
    / "results"
    / "mentor_live_progress.json"
)

QUESTIONS = [
    "Our SQLite database has frequent write locks. "
    "Should we immediately migrate to PostgreSQL?",

    "I checked the logs. Some write transactions "
    "remain open for three seconds.",

    "Give me the full solution with verification steps.",
]


def save_progress(data):
    PROGRESS.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp = PROGRESS.with_suffix(".tmp")

    temp.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    temp.replace(PROGRESS)


def call_with_retry(mentor, question, history):
    for attempt in range(4):
        try:
            return mentor.respond(
                question,
                history=history,
            )
        except RuntimeError as exc:
            message = str(exc)

            if "429" not in message or attempt == 3:
                raise

            match = re.search(
                r"Retry-After:\s*(\d+)",
                message,
            )

            delay = int(match.group(1)) if match else 30
            delay = max(delay + 2, 3)

            print(
                f"Rate limited. Retrying after {delay}s.",
                flush=True,
            )

            time.sleep(delay)


def main():
    progress = (
        json.loads(PROGRESS.read_text(encoding="utf-8"))
        if PROGRESS.exists()
        else []
    )

    if len(progress) > len(QUESTIONS):
        raise ValueError("Invalid progress file")

    for index, saved in enumerate(progress):
        if saved["question"] != QUESTIONS[index]:
            raise ValueError(
                "Saved conversation does not match test"
            )

    mentor = AdaptiveMentor(RAGPipeline())

    history = []

    for saved in progress:
        history.extend([
            {
                "role": "user",
                "content": saved["question"],
            },
            {
                "role": "assistant",
                "content": saved["answer"],
            },
        ])

    for index, question in enumerate(QUESTIONS):
        turn = index + 1

        if index < len(progress):
            print(f"SKIP TURN {turn}")
            continue

        print(f"\n{'=' * 60}")
        print(f"TURN {turn}")
        print("JUNIOR:", question)

        result = call_with_retry(
            mentor,
            question,
            history,
        )

        print("\nMENTOR:\n", result["answer"])

        progress.append({
            "question": question,
            "answer": result["answer"],
            "sources": result["sources"],
        })

        save_progress(progress)

        history.extend([
            {"role": "user", "content": question},
            {
                "role": "assistant",
                "content": result["answer"],
            },
        ])

        print(f"SAVED TURN {turn}/3", flush=True)

    print("\nADAPTIVE MENTOR LIVE TEST COMPLETE")


if __name__ == "__main__":
    main()
