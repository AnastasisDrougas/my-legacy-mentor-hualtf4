
from __future__ import annotations

import os

import requests


BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000"
).rstrip("/")

REQUEST_TIMEOUT = 30


class BackendError(Exception):
    """Raised when communication with the backend fails."""


def check_health() -> dict:
    """Check whether the FastAPI backend is available."""
    try:
        response = requests.get(
            f"{BACKEND_URL}/health",
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as exc:
        raise BackendError(
            f"Cannot connect to backend at {BACKEND_URL}: {exc}"
        ) from exc

    except ValueError as exc:
        raise BackendError(
            "Backend returned an invalid health response."
        ) from exc


def send_chat(question: str, mode: str = "ask") -> dict:
    """Send a chat request to the FastAPI backend."""

    payload = {
        "question": question,
        "mode": mode,
    }

    try:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()
        result = response.json()

        required_fields = {"answer", "mode", "sources"}

        if not required_fields.issubset(result):
            raise BackendError(
                "Backend response does not match the expected schema."
            )

        return result

    except requests.HTTPError as exc:
        try:
            detail = exc.response.json().get(
                "detail",
                exc.response.text
            )
        except (ValueError, AttributeError):
            detail = str(exc)

        raise BackendError(
            f"Backend returned HTTP error: {detail}"
        ) from exc

    except requests.RequestException as exc:
        raise BackendError(
            f"Could not communicate with backend: {exc}"
        ) from exc

    except ValueError as exc:
        raise BackendError(
            "Backend returned invalid JSON."
        ) from exc
