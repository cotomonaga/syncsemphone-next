from pydantic import BaseModel, Field


class DerivationState(BaseModel):
    grammar_id: str
    memo: str = ""
    newnum: int = 0
    basenum: int = 0
    history: str = ""
    base: list = Field(default_factory=lambda: [None])
