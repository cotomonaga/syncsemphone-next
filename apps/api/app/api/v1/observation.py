from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

DOMAIN_SRC = Path(__file__).resolve().parents[5] / "packages" / "domain" / "src"
if str(DOMAIN_SRC) not in sys.path:
    sys.path.append(str(DOMAIN_SRC))

from domain.common.types import DerivationState
from domain.observation.tree import build_treedrawer_csv_lines

router = APIRouter(prefix="/observation", tags=["observation"])


class ObservationTreeRequest(BaseModel):
    state: DerivationState
    mode: Literal["tree", "tree_cat"] = "tree"


class ObservationTreeResponse(BaseModel):
    mode: Literal["tree", "tree_cat"]
    csv_lines: list[str]
    csv_text: str


@router.post("/tree", response_model=ObservationTreeResponse)
def observation_tree(request: ObservationTreeRequest) -> ObservationTreeResponse:
    try:
        csv_lines = build_treedrawer_csv_lines(state=request.state, mode=request.mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ObservationTreeResponse(
        mode=request.mode,
        csv_lines=csv_lines,
        csv_text="\n".join(csv_lines),
    )
