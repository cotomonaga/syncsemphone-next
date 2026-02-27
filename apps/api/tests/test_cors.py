from fastapi.testclient import TestClient

from app.main import app


def test_localhost_dynamic_port_is_allowed_by_cors() -> None:
    client = TestClient(app)
    response = client.options(
        "/v1/healthz",
        headers={
            "Origin": "http://127.0.0.1:5174",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:5174"
