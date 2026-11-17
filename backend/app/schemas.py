from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    mode: Literal["ask", "mentor"] = "ask"

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        # Reject whitespace-only questions
        question = value.strip()

        if not question:
            raise ValueError("Question cannot be empty")

        return question


class Source(BaseModel):
    source_id: str
    title: str
    type: str


class ChatResponse(BaseModel):
    answer: str
    mode: Literal["ask", "mentor"]
    sources: list[Source] = Field(default_factory=list)