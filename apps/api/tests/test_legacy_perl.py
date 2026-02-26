import os
from pathlib import Path
import subprocess

from fastapi.testclient import TestClient

from app.main import app


def _legacy_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _parse_cgi_body(raw: bytes) -> bytes:
    for separator in (b"\r\n\r\n", b"\n\n"):
        index = raw.find(separator)
        if index >= 0:
            return raw[index + len(separator) :]
    return raw


def _run_perl_cgi_direct(
    *,
    script_name: str,
    query_string: str = "",
    method: str = "GET",
    body: bytes = b"",
    content_type: str = "application/x-www-form-urlencoded",
) -> bytes:
    root = _legacy_root()
    env = os.environ.copy()
    perl5lib_entries = [str(root), str(root / "My")]
    existing = env.get("PERL5LIB", "")
    if existing:
        perl5lib_entries.append(existing)
    env["PERL5LIB"] = os.pathsep.join(perl5lib_entries)
    env["REQUEST_METHOD"] = method
    env["QUERY_STRING"] = query_string
    env["SCRIPT_NAME"] = script_name
    env["GATEWAY_INTERFACE"] = "CGI/1.1"
    env["SERVER_PROTOCOL"] = "HTTP/1.1"
    env["CONTENT_LENGTH"] = str(len(body))
    env["CONTENT_TYPE"] = content_type

    result = subprocess.run(
        ["perl", str(root / script_name)],
        cwd=root,
        env=env,
        input=body,
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    return _parse_cgi_body(result.stdout)


def test_legacy_perl_index_html_matches_direct_output() -> None:
    client = TestClient(app)
    direct = _run_perl_cgi_direct(script_name="index-IMI.cgi")
    response = client.get(
        "/v1/legacy/perl/index-IMI.cgi",
        params={"legacy_root": str(_legacy_root())},
    )
    assert response.status_code == 200
    assert response.content == direct
    assert "統語意味論デモプログラム" in response.text


def test_legacy_perl_syncsemphone_html_matches_direct_output() -> None:
    client = TestClient(app)
    query_string = "grammar=imi03"
    direct = _run_perl_cgi_direct(script_name="syncsemphone.cgi", query_string=query_string)
    response = client.get(
        "/v1/legacy/perl/syncsemphone.cgi",
        params={"legacy_root": str(_legacy_root()), "grammar": "imi03"},
    )
    assert response.status_code == 200
    assert response.content == direct
    assert "<HTML>" in response.text


def test_legacy_perl_static_css_matches_source_file() -> None:
    client = TestClient(app)
    root = _legacy_root()
    direct_css = (root / "syncsem.css").read_bytes()
    response = client.get(
        "/v1/legacy/perl/syncsem.css",
        params={"legacy_root": str(root)},
    )
    assert response.status_code == 200
    assert response.content == direct_css
