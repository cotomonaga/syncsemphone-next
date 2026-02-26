from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response

router = APIRouter(prefix="/legacy/perl", tags=["legacy"])

ALLOWED_CGI = {
    "index-IMI.cgi",
    "syncsemphone.cgi",
    "lexicon.cgi",
}

ALLOWED_STATIC = {
    "syncsem.css",
    "vis.min.js",
    "vacant.html",
}


def _default_legacy_root() -> Path:
    env_value = os.getenv("SYNCSEMPHONE_LEGACY_ROOT")
    if env_value:
        return Path(env_value).expanduser().resolve()
    return Path(__file__).resolve().parents[6]


def _resolve_legacy_root(raw: Optional[str]) -> Path:
    return Path(raw).expanduser().resolve() if raw else _default_legacy_root()


def _parse_cgi_response(raw: bytes) -> tuple[int, dict[str, str], bytes]:
    separator = b"\r\n\r\n"
    index = raw.find(separator)
    if index < 0:
        separator = b"\n\n"
        index = raw.find(separator)
    if index < 0:
        return 200, {"Content-Type": "text/html; charset=utf-8"}, raw

    header_block = raw[:index].decode("iso-8859-1", errors="replace")
    body = raw[index + len(separator) :]
    status_code = 200
    headers: dict[str, str] = {}

    for line in header_block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        lower = key.lower()
        if lower == "status":
            try:
                status_code = int(value.split(" ", 1)[0])
            except ValueError:
                status_code = 200
            continue
        if lower == "content-length":
            continue
        headers[key] = value

    return status_code, headers, body


def _execute_perl_cgi(
    *,
    root: Path,
    script_name: str,
    method: str,
    query_string: str,
    body: bytes,
    content_type: Optional[str],
    script_url_path: str,
) -> Response:
    script_path = root / script_name
    if not script_path.exists():
        raise HTTPException(status_code=404, detail=f"missing Perl script: {script_name}")

    env = os.environ.copy()
    perl5lib_entries = [str(root), str(root / "My")]
    existing_perl5lib = env.get("PERL5LIB", "")
    if existing_perl5lib:
        perl5lib_entries.append(existing_perl5lib)
    env["PERL5LIB"] = os.pathsep.join(perl5lib_entries)
    env["REQUEST_METHOD"] = method
    env["QUERY_STRING"] = query_string
    env["SCRIPT_NAME"] = script_url_path
    env["GATEWAY_INTERFACE"] = "CGI/1.1"
    env["SERVER_PROTOCOL"] = "HTTP/1.1"
    env["CONTENT_LENGTH"] = str(len(body))
    if content_type:
        env["CONTENT_TYPE"] = content_type
    elif "CONTENT_TYPE" in env:
        del env["CONTENT_TYPE"]

    result = subprocess.run(
        ["perl", str(script_path)],
        cwd=root,
        env=env,
        input=body,
        capture_output=True,
        check=False,
        timeout=60,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise HTTPException(
            status_code=500,
            detail=f"Perl CGI failed ({script_name}): {stderr or f'exit {result.returncode}'}",
        )

    status_code, headers, response_body = _parse_cgi_response(result.stdout)
    content_type_header = headers.pop("Content-Type", None) or headers.pop("content-type", None)

    response = Response(content=response_body, status_code=status_code)
    if content_type_header:
        response.headers["Content-Type"] = content_type_header
    for key, value in headers.items():
        response.headers[key] = value
    return response


@router.api_route("/{resource_name}", methods=["GET", "POST"])
async def perl_resource(
    resource_name: str,
    request: Request,
    legacy_root: Optional[str] = None,
) -> Response:
    root = _resolve_legacy_root(legacy_root)
    if not root.exists():
        raise HTTPException(status_code=404, detail=f"legacy_root not found: {root}")

    if resource_name in ALLOWED_STATIC:
        if request.method != "GET":
            raise HTTPException(status_code=405, detail="static resource only supports GET")
        path = root / resource_name
        if not path.exists() or not path.is_file():
            raise HTTPException(status_code=404, detail=f"missing static file: {resource_name}")
        return FileResponse(path)

    if resource_name in ALLOWED_CGI:
        body = await request.body()
        forward_query_items = [
            (key, value)
            for key, value in request.query_params.multi_items()
            if key != "legacy_root"
        ]
        query_string = urlencode(forward_query_items, doseq=True)
        return _execute_perl_cgi(
            root=root,
            script_name=resource_name,
            method=request.method.upper(),
            query_string=query_string,
            body=body,
            content_type=request.headers.get("content-type"),
            script_url_path=f"/v1/legacy/perl/{resource_name}",
        )

    raise HTTPException(status_code=404, detail=f"unsupported legacy resource: {resource_name}")
