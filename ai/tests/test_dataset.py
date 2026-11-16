from datetime import date
from pathlib import Path
from typing import Literal
from collections import Counter
from pydantic import BaseModel, Field, ConfigDict

DocumentType = Literal['technical_document','architecture_decision','incident','pull_request','commit','mentoring']
class KnowledgeRecord(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id:str=Field(min_length=3)
    senior_id:str=Field(min_length=3)
    type:DocumentType
    title:str=Field(min_length=5)
    date:date
    project:str=Field(min_length=3)
    content:str=Field(min_length=100)
    context:str=Field(min_length=30)
    decision:str=Field(min_length=20)
    reasoning:str=Field(min_length=30)
    trade_offs:list[str]=Field(default_factory=list)
    related_ids:list[str]=Field(default_factory=list)
    tags:list[str]=Field(default_factory=list)

p = Path(__file__).resolve().parents[1] / "data" / "synthetic" / "knowledge.jsonl"
records=[KnowledgeRecord.model_validate_json(line) for line in p.read_text().splitlines() if line.strip()]
ids={r.id for r in records}
assert len(ids)==len(records)==72
assert all(r.senior_id=='senior_001' for r in records)
assert all(set(r.related_ids).issubset(ids) for r in records)
assert Counter(r.type for r in records)=={'technical_document':12,'architecture_decision':12,'incident':10,'pull_request':12,'commit':10,'mentoring':16}
print('PASS: 72 schema-valid records, unique IDs, valid links, 6 expected type counts')
