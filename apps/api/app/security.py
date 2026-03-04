from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from urllib.parse import parse_qs
from typing import Dict, List, Optional
from urllib.parse import urlparse

from fastapi import HTTPException, Request, status

SESSION_USERNAME_KEY = "username"
SESSION_CSRF_KEY = "csrf_token"
LEGACY_FORM_CSRF_FIELD = "_csrf_token"
SESSION_COOKIE_NAME = "syncsemphone_session"
DEFAULT_SESSION_MAX_AGE_SECONDS = 60 * 60 * 12
DEFAULT_LOGIN_RATE_LIMIT_WINDOW_SECONDS = 60 * 5
DEFAULT_LOGIN_RATE_LIMIT_MAX_ATTEMPTS = 10
DEFAULT_LOGIN_RATE_LIMIT_LOCK_SECONDS = 60 * 10

_DEFAULT_PASSWORD_HASHES: dict[str, str] = {
    "ueyama": "pbkdf2_sha256$310000$ZusfnleIJwvYTnNcyohuRg==$OPQknwlw9YSi-cA6vIfnfIK49FAr8gVFyzwqGDkOa5o=",
    "tomonaga": "pbkdf2_sha256$310000$HMMzvmVcDSBuqm1rBOFvtA==$I4fWveISYq_vnBo47x4HBKibhmFeAH8_Zgt3VNDBioQ=",
}
_runtime_session_secret: Optional[str] = None
_runtime_secret_warned = False
_login_attempts_lock = threading.Lock()
_login_attempts_by_key: Dict[str, List[float]] = {}
_login_lockout_until_by_key: Dict[str, float] = {}


def _is_truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def is_production_environment() -> bool:
    env_name = os.getenv("SYNCSEMPHONE_ENV", "").strip().lower()
    return env_name in {"prod", "production"}


def is_auth_enabled() -> bool:
    return not _is_truthy(os.getenv("SYNCSEMPHONE_DISABLE_AUTH"))


def is_secure_cookie_enabled() -> bool:
    return _is_truthy(os.getenv("SYNCSEMPHONE_COOKIE_SECURE"))


def session_max_age_seconds() -> int:
    raw = os.getenv("SYNCSEMPHONE_SESSION_MAX_AGE_SECONDS", "").strip()
    if raw == "":
        return DEFAULT_SESSION_MAX_AGE_SECONDS
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_SESSION_MAX_AGE_SECONDS
    return value if value > 0 else DEFAULT_SESSION_MAX_AGE_SECONDS


def _allowed_cors_origins() -> List[str]:
    default_origins = "http://127.0.0.1:5173,http://localhost:5173"
    raw = os.getenv("SYNCSEMPHONE_CORS_ORIGINS", default_origins)
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def _extract_origin_from_headers(request: Request) -> Optional[str]:
    origin = request.headers.get("Origin", "").strip()
    if origin:
        return origin
    referer = request.headers.get("Referer", "").strip()
    if not referer:
        return None
    parsed = urlparse(referer)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def _legacy_post_origin_allowed(request: Request) -> bool:
    sec_fetch_site = request.headers.get("Sec-Fetch-Site", "").strip().lower()
    if sec_fetch_site in {"same-origin", "same-site", "none"}:
        return True

    origin = _extract_origin_from_headers(request)
    if not origin:
        return False
    if origin in _allowed_cors_origins():
        return True
    if not is_production_environment():
        parsed = urlparse(origin)
        if parsed.hostname in {"127.0.0.1", "localhost"}:
            return True
    return False


def _extract_legacy_form_csrf_token(request: Request, raw_body: bytes) -> str:
    if not raw_body:
        return ""
    content_type = request.headers.get("content-type", "").lower()
    if "application/x-www-form-urlencoded" not in content_type:
        return ""
    try:
        payload = raw_body.decode("utf-8", errors="replace")
    except Exception:
        return ""
    parsed = parse_qs(payload, keep_blank_values=True)
    values = parsed.get(LEGACY_FORM_CSRF_FIELD, [])
    if not values:
        return ""
    token = values[0]
    return token.strip() if isinstance(token, str) else ""


def session_secret_key() -> str:
    global _runtime_session_secret
    global _runtime_secret_warned

    configured = os.getenv("SYNCSEMPHONE_SESSION_SECRET", "").strip()
    if configured:
        return configured

    if is_production_environment():
        raise RuntimeError(
            "SYNCSEMPHONE_SESSION_SECRET must be set in production (at least 32 chars)."
        )

    if _runtime_session_secret is None:
        _runtime_session_secret = secrets.token_urlsafe(48)
    if not _runtime_secret_warned:
        # 運用時は固定シークレットを環境変数で設定すること。
        print(
            "WARNING: SYNCSEMPHONE_SESSION_SECRET is not set; using ephemeral secret.",
            flush=True,
        )
        _runtime_secret_warned = True
    return _runtime_session_secret


def load_password_hashes() -> dict[str, str]:
    raw = os.getenv("SYNCSEMPHONE_AUTH_PASSWORD_HASHES_JSON", "").strip()
    if raw == "":
        if is_production_environment():
            raise RuntimeError("SYNCSEMPHONE_AUTH_PASSWORD_HASHES_JSON must be set in production.")
        return dict(_DEFAULT_PASSWORD_HASHES)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        if is_production_environment():
            raise RuntimeError("SYNCSEMPHONE_AUTH_PASSWORD_HASHES_JSON is not valid JSON.")
        return dict(_DEFAULT_PASSWORD_HASHES)
    if not isinstance(parsed, dict):
        if is_production_environment():
            raise RuntimeError("SYNCSEMPHONE_AUTH_PASSWORD_HASHES_JSON must be a JSON object.")
        return dict(_DEFAULT_PASSWORD_HASHES)
    out: dict[str, str] = {}
    for key, value in parsed.items():
        if isinstance(key, str) and isinstance(value, str) and value.strip() != "":
            out[key.strip()] = value.strip()
    if out:
        return out
    if is_production_environment():
        raise RuntimeError(
            "SYNCSEMPHONE_AUTH_PASSWORD_HASHES_JSON must contain at least one username/hash pair."
        )
    return dict(_DEFAULT_PASSWORD_HASHES)


def _login_rate_limit_window_seconds() -> int:
    raw = os.getenv("SYNCSEMPHONE_LOGIN_RATE_LIMIT_WINDOW_SECONDS", "").strip()
    if raw == "":
        return DEFAULT_LOGIN_RATE_LIMIT_WINDOW_SECONDS
    try:
        parsed = int(raw)
    except ValueError:
        return DEFAULT_LOGIN_RATE_LIMIT_WINDOW_SECONDS
    return parsed if parsed > 0 else DEFAULT_LOGIN_RATE_LIMIT_WINDOW_SECONDS


def _login_rate_limit_max_attempts() -> int:
    raw = os.getenv("SYNCSEMPHONE_LOGIN_RATE_LIMIT_MAX_ATTEMPTS", "").strip()
    if raw == "":
        return DEFAULT_LOGIN_RATE_LIMIT_MAX_ATTEMPTS
    try:
        parsed = int(raw)
    except ValueError:
        return DEFAULT_LOGIN_RATE_LIMIT_MAX_ATTEMPTS
    return parsed if parsed > 0 else DEFAULT_LOGIN_RATE_LIMIT_MAX_ATTEMPTS


def _login_rate_limit_lock_seconds() -> int:
    raw = os.getenv("SYNCSEMPHONE_LOGIN_RATE_LIMIT_LOCK_SECONDS", "").strip()
    if raw == "":
        return DEFAULT_LOGIN_RATE_LIMIT_LOCK_SECONDS
    try:
        parsed = int(raw)
    except ValueError:
        return DEFAULT_LOGIN_RATE_LIMIT_LOCK_SECONDS
    return parsed if parsed > 0 else DEFAULT_LOGIN_RATE_LIMIT_LOCK_SECONDS


def _build_login_rate_limit_key(request: Request, username: str) -> str:
    client_host = request.client.host if request.client and request.client.host else "unknown"
    return f"{client_host}:{username.strip().lower()}"


def login_rate_limit_retry_after_seconds(request: Request, username: str) -> int:
    key = _build_login_rate_limit_key(request, username)
    now = time.time()
    window_seconds = _login_rate_limit_window_seconds()
    with _login_attempts_lock:
        lock_until = _login_lockout_until_by_key.get(key, 0.0)
        if lock_until > now:
            return int(lock_until - now) + 1
        _login_lockout_until_by_key.pop(key, None)
        attempts = [
            ts for ts in _login_attempts_by_key.get(key, []) if (now - ts) <= window_seconds
        ]
        if attempts:
            _login_attempts_by_key[key] = attempts
        else:
            _login_attempts_by_key.pop(key, None)
        return 0


def record_failed_login_attempt(request: Request, username: str) -> None:
    key = _build_login_rate_limit_key(request, username)
    now = time.time()
    window_seconds = _login_rate_limit_window_seconds()
    max_attempts = _login_rate_limit_max_attempts()
    lock_seconds = _login_rate_limit_lock_seconds()
    with _login_attempts_lock:
        attempts = [
            ts for ts in _login_attempts_by_key.get(key, []) if (now - ts) <= window_seconds
        ]
        attempts.append(now)
        if len(attempts) >= max_attempts:
            _login_lockout_until_by_key[key] = now + lock_seconds
            _login_attempts_by_key.pop(key, None)
            return
        _login_attempts_by_key[key] = attempts


def record_successful_login_attempt(request: Request, username: str) -> None:
    key = _build_login_rate_limit_key(request, username)
    with _login_attempts_lock:
        _login_attempts_by_key.pop(key, None)
        _login_lockout_until_by_key.pop(key, None)


def validate_production_security_settings() -> None:
    if not is_production_environment():
        return

    validation_errors: List[str] = []
    if not is_auth_enabled():
        validation_errors.append("SYNCSEMPHONE_DISABLE_AUTH must not be enabled in production.")

    secret = os.getenv("SYNCSEMPHONE_SESSION_SECRET", "").strip()
    if len(secret) < 32:
        validation_errors.append(
            "SYNCSEMPHONE_SESSION_SECRET must be set to a strong value (32+ chars) in production."
        )

    if not is_secure_cookie_enabled():
        validation_errors.append(
            "SYNCSEMPHONE_COOKIE_SECURE must be enabled in production (HTTPS-only session cookie)."
        )

    if os.getenv("SYNCSEMPHONE_AUTH_PASSWORD_HASHES_JSON", "").strip() == "":
        validation_errors.append(
            "SYNCSEMPHONE_AUTH_PASSWORD_HASHES_JSON must be set in production (no built-in default users)."
        )

    try:
        load_password_hashes()
    except RuntimeError as config_error:
        validation_errors.append(str(config_error))

    if validation_errors:
        raise RuntimeError(
            "Insecure production configuration detected:\n- "
            + "\n- ".join(validation_errors)
        )


def _verify_pbkdf2_sha256_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, iterations_raw, salt_b64, digest_b64 = encoded_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_raw)
        salt = base64.urlsafe_b64decode(salt_b64.encode("utf-8"))
        expected_digest = base64.urlsafe_b64decode(digest_b64.encode("utf-8"))
    except (ValueError, base64.binascii.Error):
        return False

    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(digest, expected_digest)


def verify_login_credentials(username: str, password: str) -> bool:
    password_hashes = load_password_hashes()
    stored_hash = password_hashes.get(username)
    if not stored_hash:
        return False
    return _verify_pbkdf2_sha256_password(password, stored_hash)


def create_authenticated_session(request: Request, username: str) -> str:
    csrf_token = secrets.token_urlsafe(32)
    request.session.clear()
    request.session[SESSION_USERNAME_KEY] = username
    request.session[SESSION_CSRF_KEY] = csrf_token
    return csrf_token


def clear_authenticated_session(request: Request) -> None:
    request.session.clear()


def get_authenticated_username(request: Request) -> Optional[str]:
    if not is_auth_enabled():
        return "test-user"
    username = request.session.get(SESSION_USERNAME_KEY)
    if not isinstance(username, str) or username.strip() == "":
        return None
    if username not in load_password_hashes():
        return None
    return username


def get_or_create_csrf_token(request: Request) -> Optional[str]:
    if not is_auth_enabled():
        return None
    csrf_token = request.session.get(SESSION_CSRF_KEY)
    if isinstance(csrf_token, str) and csrf_token.strip() != "":
        return csrf_token
    csrf_token = secrets.token_urlsafe(32)
    request.session[SESSION_CSRF_KEY] = csrf_token
    return csrf_token


async def require_authenticated_user(request: Request) -> str:
    username = get_authenticated_username(request)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    method = request.method.upper()
    if method in {"GET", "HEAD", "OPTIONS"}:
        return username

    csrf_in_session = get_or_create_csrf_token(request)
    csrf_from_header = request.headers.get("X-CSRF-Token", "")
    valid_session_token = isinstance(csrf_in_session, str) and csrf_in_session.strip() != ""
    if valid_session_token and csrf_from_header.strip() != "":
        if hmac.compare_digest(csrf_in_session, csrf_from_header.strip()):
            return username

    if request.url.path.startswith("/v1/legacy/perl/"):
        raw_body = await request.body()
        csrf_from_form = _extract_legacy_form_csrf_token(request, raw_body)
        if (
            valid_session_token
            and csrf_from_form != ""
            and hmac.compare_digest(csrf_in_session, csrf_from_form)
            and _legacy_post_origin_allowed(request)
        ):
            return username

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="CSRF token missing or invalid",
    )
