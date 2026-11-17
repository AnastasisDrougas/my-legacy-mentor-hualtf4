
import os

import httpx
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.model = os.getenv("LLM_MODEL")
        self.base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")

        if not all([self.api_key, self.model, self.base_url]):
            raise ValueError(
                "Missing LLM_API_KEY, LLM_MODEL or LLM_BASE_URL"
            )

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }

        try:
            with httpx.Client(timeout=90.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )

                response.raise_for_status()
                result = response.json()

        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code

            if status == 429:
                retry_after = exc.response.headers.get("retry-after")
                raise RuntimeError(
                    f"LLM rate limit exceeded (429). "
                    f"Retry-After: {retry_after or 'not provided'}"
                ) from exc

            raise RuntimeError(
                f"LLM API returned HTTP {status}"
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                f"LLM connection error: {type(exc).__name__}"
            ) from exc

        try:
            content = result["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError("Empty LLM response")
            return content.strip()

        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise RuntimeError(
                "Invalid LLM API response"
            ) from exc
