from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def _legacy_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _load_num_file(relative_path: str) -> str:
    return (_legacy_root() / relative_path).read_text(encoding="utf-8")


def _state_after_one_step(client: TestClient) -> dict:
    init_payload = {
        "grammar_id": "imi03",
        "numeration_text": _load_num_file("imi03/set-numeration/04.num"),
        "legacy_root": str(_legacy_root()),
    }
    init_response = client.post("/v1/derivation/init", json=init_payload)
    assert init_response.status_code == 200
    t0 = init_response.json()
    t1_response = client.post(
        "/v1/derivation/execute",
        json={
            "state": t0,
            "rule_name": "LH-Merge",
            "left": 5,
            "right": 6,
        },
    )
    assert t1_response.status_code == 200
    return t1_response.json()


def test_observation_tree_endpoint() -> None:
    client = TestClient(app)
    t1 = _state_after_one_step(client=client)
    response = client.post(
        "/v1/observation/tree",
        json={"state": t1, "mode": "tree"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "tree"
    assert len(body["csv_lines"]) > 0
    assert "&lt;br&gt;-ta" in body["csv_text"]


def test_observation_tree_cat_endpoint() -> None:
    client = TestClient(app)
    t1 = _state_after_one_step(client=client)
    response = client.post(
        "/v1/observation/tree",
        json={"state": t1, "mode": "tree_cat"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "tree_cat"
    assert len(body["csv_lines"]) > 0
    assert "T&lt;br&gt;-ta" in body["csv_text"]


def test_observation_tree_is_invariant_after_resume_import_imi03() -> None:
    client = TestClient(app)
    t1 = _state_after_one_step(client=client)

    export_response = client.post(
        "/v1/derivation/resume/export",
        json={"state": t1},
    )
    assert export_response.status_code == 200
    resume_text = export_response.json()["resume_text"]

    import_response = client.post(
        "/v1/derivation/resume/import",
        json={"resume_text": resume_text},
    )
    assert import_response.status_code == 200
    restored = import_response.json()

    for mode in ("tree", "tree_cat"):
        original_obs = client.post(
            "/v1/observation/tree",
            json={"state": t1, "mode": mode},
        )
        restored_obs = client.post(
            "/v1/observation/tree",
            json={"state": restored, "mode": mode},
        )
        assert original_obs.status_code == 200
        assert restored_obs.status_code == 200
        assert restored_obs.json()["csv_lines"] == original_obs.json()["csv_lines"]
        assert restored_obs.json()["csv_text"] == original_obs.json()["csv_text"]


def test_observation_tree_is_invariant_after_resume_import_japanese2_single() -> None:
    client = TestClient(app)
    init_payload = {
        "grammar_id": "japanese2",
        "numeration_text": _load_num_file("japanese2/set-numeration/08-05-45.num"),
        "legacy_root": str(_legacy_root()),
    }
    init_response = client.post("/v1/derivation/init", json=init_payload)
    assert init_response.status_code == 200
    t0 = init_response.json()

    exec_response = client.post(
        "/v1/derivation/execute",
        json={
            "state": t0,
            "rule_name": "Partitioning",
            "check": 5,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert exec_response.status_code == 200
    state = exec_response.json()

    export_response = client.post(
        "/v1/derivation/resume/export",
        json={"state": state},
    )
    assert export_response.status_code == 200
    resume_text = export_response.json()["resume_text"]
    import_response = client.post(
        "/v1/derivation/resume/import",
        json={"resume_text": resume_text},
    )
    assert import_response.status_code == 200
    restored = import_response.json()

    for mode in ("tree", "tree_cat"):
        original_obs = client.post(
            "/v1/observation/tree",
            json={"state": state, "mode": mode},
        )
        restored_obs = client.post(
            "/v1/observation/tree",
            json={"state": restored, "mode": mode},
        )
        assert original_obs.status_code == 200
        assert restored_obs.status_code == 200
        assert restored_obs.json()["csv_lines"] == original_obs.json()["csv_lines"]
        assert restored_obs.json()["csv_text"] == original_obs.json()["csv_text"]
