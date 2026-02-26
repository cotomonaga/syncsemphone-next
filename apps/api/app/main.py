import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.derivation import router as derivation_router
from app.api.v1.health import router as health_router
from app.api.v1.legacy_perl import router as legacy_perl_router
from app.api.v1.lexicon import router as lexicon_router
from app.api.v1.observation import router as observation_router
from app.api.v1.reference import router as reference_router
from app.api.v1.semantics import router as semantics_router

app = FastAPI(title="syncsemphone-next API", version="0.1.0")
cors_origins_env = os.getenv("SYNCSEMPHONE_CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173")
cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router, prefix="/v1")
app.include_router(derivation_router, prefix="/v1")
app.include_router(lexicon_router, prefix="/v1")
app.include_router(observation_router, prefix="/v1")
app.include_router(semantics_router, prefix="/v1")
app.include_router(reference_router, prefix="/v1")
app.include_router(legacy_perl_router, prefix="/v1")
