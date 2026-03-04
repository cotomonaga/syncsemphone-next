#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import secrets


def encode_password(password: str, iterations: int = 310000) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    salt_b64 = base64.urlsafe_b64encode(salt).decode("utf-8")
    digest_b64 = base64.urlsafe_b64encode(digest).decode("utf-8")
    return f"pbkdf2_sha256${iterations}${salt_b64}${digest_b64}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SYNCSEMPHONE password hash")
    parser.add_argument("--username", required=True, help="username key")
    parser.add_argument("--password", required=True, help="plain password")
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="print only JSON object for SYNCSEMPHONE_AUTH_PASSWORD_HASHES_JSON",
    )
    args = parser.parse_args()

    encoded = encode_password(args.password)
    payload = {args.username: encoded}
    payload_json = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))

    if args.json_only:
        print(payload_json)
        return

    print("Hash:")
    print(encoded)
    print("")
    print("SYNCSEMPHONE_AUTH_PASSWORD_HASHES_JSON value:")
    print(payload_json)


if __name__ == "__main__":
    main()
