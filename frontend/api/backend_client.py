"""HTTP client for the existing FastAPI contracts (no frontend persistence)."""
from __future__ import annotations

import os

import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
REQUEST_TIMEOUT = 120


class BackendError(Exception):
    """An HTTP, connection, or response-contract error."""


def _request(method: str, path: str, **kwargs) -> requests.Response:
    try:
        response = requests.request(
            method, f"{BACKEND_URL}{path}", timeout=REQUEST_TIMEOUT, **kwargs
        )
        response.raise_for_status()
        return response
    except requests.HTTPError as exc:
        try:
            body = exc.response.json()
            detail = body.get("detail", exc.response.text) if isinstance(body, dict) else exc.response.text
        except ValueError:
            detail = exc.response.text if exc.response is not None else str(exc)
        raise BackendError(f"Backend returned HTTP error: {detail}") from exc
    except requests.RequestException as exc:
        raise BackendError(f"Could not communicate with backend: {exc}") from exc


def _json(response: requests.Response):
    try:
        return response.json()
    except ValueError as exc:
        raise BackendError("Backend returned invalid JSON.") from exc


def check_health() -> dict:
    result = _json(_request("GET", "/health"))
    if not isinstance(result, dict):
        raise BackendError("Invalid health response")
    return result


def list_conversations() -> list[dict]:
    result = _json(_request("GET", "/conversations"))
    if not isinstance(result, list) or any(not isinstance(x, dict) or "id" not in x for x in result):
        raise BackendError("Invalid conversations list")
    return result


def get_conversation(conversation_id: str) -> dict:
    result = _json(_request("GET", f"/conversations/{conversation_id}"))
    if not isinstance(result, dict) or not isinstance(result.get("messages"), list):
        raise BackendError("Invalid conversation history")
    return result


def send_chat(question: str, mode: str = "ask", conversation_id: str | None = None) -> dict:
    """Post to /chat and return the backend-assigned conversation ID with the answer."""
    headers = {"X-Conversation-ID": conversation_id} if conversation_id else {}
    response = _request(
        "POST", "/chat", json={"question": question, "mode": mode}, headers=headers
    )
    result = _json(response)
    if not isinstance(result, dict) or not {"answer", "mode", "sources"}.issubset(result):
        raise BackendError("Backend response does not match the expected schema.")
    returned_id = response.headers.get("X-Conversation-ID")
    if not returned_id:
        raise BackendError("Backend did not return X-Conversation-ID")
    if conversation_id and returned_id != conversation_id:
        raise BackendError("Backend returned a different conversation ID")
    return {**result, "conversation_id": returned_id}


def upload_document(filename: str, data: bytes, content_type: str) -> dict:
    result = _json(_request(
        "POST", "/documents", files={"file": (filename, data, content_type)}
    ))
    if not isinstance(result, dict) or not {"id", "filename", "status"}.issubset(result):
        raise BackendError("Invalid document upload response")
    return result
