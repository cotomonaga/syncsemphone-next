from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class DerivationState(BaseModel):
    grammar_id: str
    memo: str = ""
    newnum: int = 0
    basenum: int = 0
    history: str = ""
    # Perl互換で index 1 から lexical item が入る（index 0 は空）
    base: list[Any] = Field(default_factory=lambda: [None])


class RuleCandidate(BaseModel):
    rule_number: int
    rule_name: str
    rule_kind: Literal["double", "single"]
    left: Optional[int] = None
    right: Optional[int] = None
    check: Optional[int] = None
