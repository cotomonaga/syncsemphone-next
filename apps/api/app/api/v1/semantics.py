from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

DOMAIN_SRC = Path(__file__).resolve().parents[5] / "packages" / "domain" / "src"
if str(DOMAIN_SRC) not in sys.path:
    sys.path.append(str(DOMAIN_SRC))

from domain.common.types import DerivationState
from domain.semantics.lf_sr import build_lf_items, build_sr_layers

router = APIRouter(prefix="/semantics", tags=["semantics"])


class LFItemResponse(BaseModel):
    lexical_id: str
    category: str
    idslot: str
    semantics: list[str] = Field(default_factory=list)
    predication: list[list[str]] = Field(default_factory=list)


class LfResponse(BaseModel):
    list_representation: list[LFItemResponse]
    unresolved_feature_like_token: bool


class SRLayerResponse(BaseModel):
    object_id: int
    layer: int
    kind: Literal["object", "Predication"]
    properties: list[str] = Field(default_factory=list)


class SrResponse(BaseModel):
    truth_conditional_meaning: list[SRLayerResponse]


class SemanticsRequest(BaseModel):
    state: DerivationState


@router.post("/lf", response_model=LfResponse)
def semantics_lf(request: SemanticsRequest) -> LfResponse:
    items = build_lf_items(request.state)
    unresolved = any("=" in semantic for item in items for semantic in item.semantics)
    return LfResponse(
        list_representation=[
            LFItemResponse(
                lexical_id=item.lexical_id,
                category=item.category,
                idslot=item.idslot,
                semantics=item.semantics,
                predication=item.predication,
            )
            for item in items
        ],
        unresolved_feature_like_token=unresolved,
    )


@router.post("/sr", response_model=SrResponse)
def semantics_sr(request: SemanticsRequest) -> SrResponse:
    layers = build_sr_layers(request.state)
    return SrResponse(
        truth_conditional_meaning=[
            SRLayerResponse(
                object_id=row.object_id,
                layer=row.layer,
                kind="Predication" if row.kind == "Predication" else "object",
                properties=row.properties,
            )
            for row in layers
        ]
    )
