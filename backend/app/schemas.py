from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    mode: Literal["ask", "mentor"] = "ask"

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        # Reject questions containing only whitespace
        question = value.strip()

        if not question:
            raise ValueError("Question cannot be empty")

        return question


class Source(BaseModel):
    document_id: str
    title: str
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    mode: Literal["ask", "mentor"]
    sources: list[Source] = Field(default_factory=list)