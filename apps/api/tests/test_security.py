from types import SimpleNamespace

import pytest

from app.security import (
    login_rate_limit_retry_after_seconds,
    record_failed_login_attempt,
    record_successful_login_attempt,
    validate_production_security_settings,
)


def _dummy_request(host: str = "127.0.0.1"):
    return SimpleNamespace(client=SimpleNamespace(host=host))


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
