from types import SimpleNamespace
from typing import Optional

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.security import (
    login_rate_limit_retry_after_seconds,
    record_failed_login_attempt,
    record_successful_login_attempt,
    require_authenticated_user,
    validate_production_security_settings,
)


def _dummy_request(host: str = "127.0.0.1"):
    return SimpleNamespace(client=SimpleNamespace(host=host))


def _build_authenticated_request(
    *,
    method: str,
    path: str,
    origin: Optional[str] = None,
    referer: Optional[str] = None,
    csrf_header: Optional[str] = None,
    content_type: Optional[str] = None,
    body: bytes = b"",
    sec_fetch_site: Optional[str] = None,
) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if origin:
        headers.append((b"origin", origin.encode("utf-8")))
    if referer:
        headers.append((b"referer", referer.encode("utf-8")))
    if csrf_header:
        headers.append((b"x-csrf-token", csrf_header.encode("utf-8")))
    if content_type:
        headers.append((b"content-type", content_type.encode("utf-8")))
    if sec_fetch_site:
        headers.append((b"sec-fetch-site", sec_fetch_site.encode("utf-8")))
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "headers": headers,
        "client": ("127.0.0.1", 12345),
        "session": {"username": "ueyama", "csrf_token": "csrf-ok"},
    }
    delivered = False

    async def _receive():
        nonlocal delivered
        if delivered:
            return {"type": "http.request", "body": b"", "more_body": False}
        delivered = True
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(scope, _receive)


def test_validate_production_security_settings_rejects_unsafe_defaults(monkeypatch):
    monkeypatch.setenv("SYNCSEMPHONE_ENV", "production")
    monkeypatch.delenv("SYNCSEMPHONE_SESSION_SECRET", raising=False)
    monkeypatch.delenv("SYNCSEMPHONE_AUTH_PASSWORD_HASHES_JSON", raising=False)
    monkeypatch.setenv("SYNCSEMPHONE_COOKIE_SECURE", "0")
    monkeypatch.delenv("SYNCSEMPHONE_DISABLE_AUTH", raising=False)

    with pytest.raises(RuntimeError):
        validate_production_security_settings()


def test_validate_production_security_settings_accepts_hardened_config(monkeypatch):
    monkeypatch.setenv("SYNCSEMPHONE_ENV", "production")
    monkeypatch.setenv("SYNCSEMPHONE_SESSION_SECRET", "x" * 48)
    monkeypatch.setenv(
        "SYNCSEMPHONE_AUTH_PASSWORD_HASHES_JSON",
        '{"ueyama":"pbkdf2_sha256$310000$ZusfnleIJwvYTnNcyohuRg==$OPQknwlw9YSi-cA6vIfnfIK49FAr8gVFyzwqGDkOa5o="}',
    )
    monkeypatch.setenv("SYNCSEMPHONE_COOKIE_SECURE", "1")
    monkeypatch.delenv("SYNCSEMPHONE_DISABLE_AUTH", raising=False)

    validate_production_security_settings()


def test_login_rate_limit_blocks_then_resets(monkeypatch):
    monkeypatch.setenv("SYNCSEMPHONE_LOGIN_RATE_LIMIT_WINDOW_SECONDS", "60")
    monkeypatch.setenv("SYNCSEMPHONE_LOGIN_RATE_LIMIT_MAX_ATTEMPTS", "2")
    monkeypatch.setenv("SYNCSEMPHONE_LOGIN_RATE_LIMIT_LOCK_SECONDS", "60")

    request = _dummy_request()
    username = "ueyama"

    assert login_rate_limit_retry_after_seconds(request, username) == 0
    record_failed_login_attempt(request, username)
    assert login_rate_limit_retry_after_seconds(request, username) == 0

    record_failed_login_attempt(request, username)
    retry_after_seconds = login_rate_limit_retry_after_seconds(request, username)
    assert retry_after_seconds > 0

    record_successful_login_attempt(request, username)
    assert login_rate_limit_retry_after_seconds(request, username) == 0


@pytest.mark.anyio
async def test_require_authenticated_user_accepts_legacy_post_with_form_csrf_token(monkeypatch):
    monkeypatch.delenv("SYNCSEMPHONE_DISABLE_AUTH", raising=False)
    monkeypatch.delenv("SYNCSEMPHONE_ENV", raising=False)
    monkeypatch.setenv("SYNCSEMPHONE_CORS_ORIGINS", "http://127.0.0.1:5173")
    request = _build_authenticated_request(
        method="POST",
        path="/v1/legacy/perl/syncsemphone.cgi",
        origin="http://127.0.0.1:5173",
        content_type="application/x-www-form-urlencoded",
        body=b"mode=numeration_select&_csrf_token=csrf-ok",
    )
    assert await require_authenticated_user(request) == "ueyama"


@pytest.mark.anyio
async def test_require_authenticated_user_rejects_legacy_post_with_disallowed_origin(monkeypatch):
    monkeypatch.delenv("SYNCSEMPHONE_DISABLE_AUTH", raising=False)
    monkeypatch.delenv("SYNCSEMPHONE_ENV", raising=False)
    monkeypatch.setenv("SYNCSEMPHONE_CORS_ORIGINS", "https://app.example.com")
    request = _build_authenticated_request(
        method="POST",
        path="/v1/legacy/perl/syncsemphone.cgi",
        origin="https://evil.example.com",
        content_type="application/x-www-form-urlencoded",
        body=b"mode=numeration_select&_csrf_token=csrf-ok",
    )
    with pytest.raises(HTTPException) as exc_info:
        await require_authenticated_user(request)
    assert exc_info.value.status_code == 403


@pytest.mark.anyio
async def test_require_authenticated_user_requires_csrf_for_non_legacy_posts(monkeypatch):
    monkeypatch.delenv("SYNCSEMPHONE_DISABLE_AUTH", raising=False)
    monkeypatch.delenv("SYNCSEMPHONE_ENV", raising=False)
    request = _build_authenticated_request(
        method="POST",
        path="/v1/derivation/init",
        origin="http://127.0.0.1:5173",
    )
    with pytest.raises(HTTPException) as exc_info:
        await require_authenticated_user(request)
    assert exc_info.value.status_code == 403
