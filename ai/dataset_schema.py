
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


DocumentType = Literal[
    "technical_document",
    "architecture_decision",
    "incident",
    "pull_request",
    "commit",
    "mentoring"
]


class KnowledgeRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=3)
    senior_id: str = Field(min_length=3)
    type: DocumentType

    title: str = Field(min_length=5)
    date: date
    project: str = Field(min_length=3)

    content: str = Field(min_length=100)

    context: str = Field(min_length=30)
    decision: str = Field(min_length=20)
    reasoning: str = Field(min_length=30)

    trade_offs: list[str] = Field(default_factory=list)
    related_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
