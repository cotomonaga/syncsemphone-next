from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.security import (
    clear_authenticated_session,
    create_authenticated_session,
    get_authenticated_username,
    get_or_create_csrf_token,
    is_auth_enabled,
    login_rate_limit_retry_after_seconds,
    record_failed_login_attempt,
    record_successful_login_attempt,
    require_authenticated_user,
    verify_login_credentials,
)

router = APIRouter(prefix="/auth")


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=512)


class SessionResponse(BaseModel):
    authenticated: bool
    username: Optional[str] = None
    csrf_token: Optional[str] = None


@router.get("/session", response_model=SessionResponse)
def auth_session(request: Request) -> SessionResponse:
    username = get_authenticated_username(request)
    if not username:
        return SessionResponse(authenticated=False, username=None, csrf_token=None)
    return SessionResponse(
        authenticated=True,
        username=username,
        csrf_token=get_or_create_csrf_token(request),
    )


@router.post("/login", response_model=SessionResponse)
def auth_login(request: Request, payload: LoginRequest) -> SessionResponse:
    username = payload.username.strip()
    if username == "":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    retry_after_seconds = login_rate_limit_retry_after_seconds(request, username)
    if retry_after_seconds > 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Retry after {retry_after_seconds} seconds.",
            headers={"Retry-After": str(retry_after_seconds)},
        )

    if is_auth_enabled() and not verify_login_credentials(username, payload.password):
        record_failed_login_attempt(request, username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    record_successful_login_attempt(request, username)
    csrf_token = create_authenticated_session(request, username)
    return SessionResponse(authenticated=True, username=username, csrf_token=csrf_token)


@router.post("/logout")
def auth_logout(
    request: Request,
    _username: str = Depends(require_authenticated_user),
) -> dict[str, bool]:
    clear_authenticated_session(request)
    return {"ok": True}
