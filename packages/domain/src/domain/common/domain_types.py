from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

# Grammar / rule naming
GrammarId = Literal["imi01", "imi02", "imi03", "japanese2"]
RuleKind = Literal["double", "single"]
RuleVersion = Literal["01", "03", "04"]
TreeMode = Literal["tree", "tree_cat"]

# Base item slot names
BaseSlotName = Literal["id", "ca", "pr", "sy", "sl", "se", "ph", "wo"]


class DerivationIndex(BaseModel):
    value: int = Field(ge=1)

    model_config = {"frozen": True}


class DoubleMergeTarget(BaseModel):
    left: DerivationIndex
    right: DerivationIndex

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def _validate_distinct(self) -> "DoubleMergeTarget":
        if self.left.value == self.right.value:
            raise ValueError("left and right must be different")
        return self


class SingleMergeTarget(BaseModel):
    check: DerivationIndex

    model_config = {"frozen": True}


class RuleRef(BaseModel):
    rule_name: Optional[str] = None
    rule_number: Optional[int] = Field(default=None, ge=1)

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def _validate_at_least_one(self) -> "RuleRef":
        if self.rule_name is None and self.rule_number is None:
            raise ValueError("Either rule_name or rule_number is required")
        return self
