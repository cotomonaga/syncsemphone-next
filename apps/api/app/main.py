import os
from typing import Optional

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.derivation import router as derivation_router
from app.api.v1.health import router as health_router
from app.api.v1.legacy_perl import router as legacy_perl_router
from app.api.v1.lexicon import router as lexicon_router
from app.api.v1.lexicon_ext import router as lexicon_ext_router
from app.api.v1.observation import router as observation_router
from app.api.v1.reference import router as reference_router
from app.api.v1.semantics import router as semantics_router
from app.security import (
    SESSION_COOKIE_NAME,
    is_auth_enabled,
    is_production_environment,
    is_secure_cookie_enabled,
    require_authenticated_user,
    session_max_age_seconds,
    session_secret_key,
    validate_production_security_settings,
)

def _is_truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


is_production = is_production_environment()
validate_production_security_settings()

default_docs_enabled = not is_production
docs_enabled = _is_truthy(os.getenv("SYNCSEMPHONE_ENABLE_DOCS")) if is_production else default_docs_enabled
app = FastAPI(
    title="syncsemphone-next API",
    version="0.1.0",
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
)

default_cors_origins = "http://127.0.0.1:5173,http://localhost:5173" if not is_production else ""
cors_origins_env = os.getenv("SYNCSEMPHONE_CORS_ORIGINS", default_cors_origins)
cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
default_origin_regex = r"^https?://(127\.0\.0\.1|localhost)(:\d+)?$" if not is_production else ""
cors_origin_regex = os.getenv("SYNCSEMPHONE_CORS_ORIGIN_REGEX", default_origin_regex).strip() or None
if any(origin == "*" for origin in cors_origins):
    raise RuntimeError("SYNCSEMPHONE_CORS_ORIGINS must not contain '*' when credentials are enabled.")
if is_production and not cors_origins and not cors_origin_regex:
    raise RuntimeError("Set SYNCSEMPHONE_CORS_ORIGINS and/or SYNCSEMPHONE_CORS_ORIGIN_REGEX in production.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

default_allowed_hosts = "127.0.0.1,localhost,testserver" if not is_production else ""
allowed_hosts_env = os.getenv("SYNCSEMPHONE_ALLOWED_HOSTS", default_allowed_hosts)
allowed_hosts = [host.strip() for host in allowed_hosts_env.split(",") if host.strip()]
if is_production and not allowed_hosts:
    raise RuntimeError("SYNCSEMPHONE_ALLOWED_HOSTS must be configured in production.")
if allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

default_frame_ancestors = "'self' http://127.0.0.1:5173 http://localhost:5173" if not is_production else "'self'"
frame_ancestors_policy = (
    os.getenv("SYNCSEMPHONE_FRAME_ANCESTORS", default_frame_ancestors).strip()
    or default_frame_ancestors
)

if is_auth_enabled():
    app.add_middleware(
        SessionMiddleware,
        secret_key=session_secret_key(),
        session_cookie=SESSION_COOKIE_NAME,
        same_site="lax",
        https_only=is_secure_cookie_enabled(),
        max_age=session_max_age_seconds(),
    )

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    if request.url.path.startswith("/v1/legacy/perl/"):
        response.headers.setdefault(
            "Content-Security-Policy", f"frame-ancestors {frame_ancestors_policy}"
        )
    else:
        response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Cache-Control", "no-store")
    return response


protected_dependencies = [Depends(require_authenticated_user)] if is_auth_enabled() else []

app.include_router(health_router, prefix="/v1")
app.include_router(auth_router, prefix="/v1")
app.include_router(derivation_router, prefix="/v1", dependencies=protected_dependencies)
app.include_router(lexicon_ext_router, prefix="/v1", dependencies=protected_dependencies)
app.include_router(lexicon_router, prefix="/v1", dependencies=protected_dependencies)
app.include_router(observation_router, prefix="/v1", dependencies=protected_dependencies)
app.include_router(semantics_router, prefix="/v1", dependencies=protected_dependencies)
app.include_router(reference_router, prefix="/v1", dependencies=protected_dependencies)
app.include_router(legacy_perl_router, prefix="/v1", dependencies=protected_dependencies)
