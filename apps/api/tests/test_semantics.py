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


def test_semantics_lf_endpoint() -> None:
    client = TestClient(app)
    t1 = _state_after_one_step(client=client)
    response = client.post("/v1/semantics/lf", json={"state": t1})
    assert response.status_code == 200
    body = response.json()
    assert "list_representation" in body
    assert isinstance(body["list_representation"], list)
    all_sem = []
    for row in body["list_representation"]:
        all_sem.extend(row["semantics"])
    assert "Name:ジョン" in all_sem


def test_semantics_sr_endpoint() -> None:
    client = TestClient(app)
    t1 = _state_after_one_step(client=client)
    response = client.post("/v1/semantics/sr", json={"state": t1})
    assert response.status_code == 200
    body = response.json()
    assert "truth_conditional_meaning" in body
    assert any(
        row["object_id"] == 1 and row["layer"] == 1
        for row in body["truth_conditional_meaning"]
    )


def test_semantics_lf_reflects_feature_33_resolution_after_v_plus_wo() -> None:
    client = TestClient(app)
    init_payload = {
        "grammar_id": "imi03",
        "numeration_text": _load_num_file("imi03/set-numeration/04.num"),
        "legacy_root": str(_legacy_root()),
    }
    init_response = client.post("/v1/derivation/init", json=init_payload)
    assert init_response.status_code == 200
    t0 = init_response.json()

    step = client.post(
        "/v1/derivation/execute",
        json={
            "state": t0,
            "rule_name": "LH-Merge",
            "left": 5,
            "right": 4,
        },
    )
    assert step.status_code == 200
    t1 = step.json()

    lf = client.post("/v1/semantics/lf", json={"state": t1})
    assert lf.status_code == 200
    all_sem = []
    for row in lf.json()["list_representation"]:
        all_sem.extend(row["semantics"])
    assert "Theme:x4-1" in all_sem


def test_semantics_sr_resolves_beta_binding_synthetic() -> None:
    client = TestClient(app)
    synthetic_state = {
        "grammar_id": "japanese2",
        "memo": "beta-synth",
        "newnum": 6,
        "basenum": 3,
        "history": "",
        "base": [
            None,
            ["x2-1", "V", [], [], "x2-1", ["Agent:x4-1"], "", ""],
            [
                "x5-1",
                "N",
                [],
                ["beta#5#Agent(x2-1)"],
                "β5",
                ["Kind:betaThing"],
                "",
                "",
            ],
            ["x4-1", "N", [], [], "x4-1", ["Name:target"], "", ""],
        ],
    }
    response = client.post("/v1/semantics/sr", json={"state": synthetic_state})
    assert response.status_code == 200
    rows = response.json()["truth_conditional_meaning"]
    assert any(
        row["object_id"] == 4
        and row["layer"] == 1
        and "Kind:betaThing" in row["properties"]
        for row in rows
    )
    assert not any(row["object_id"] == 5 for row in rows)


def test_semantics_sr_resolves_multiple_beta_bindings_synthetic() -> None:
    client = TestClient(app)
    synthetic_state = {
        "grammar_id": "japanese2",
        "memo": "beta-multi-synth",
        "newnum": 9,
        "basenum": 5,
        "history": "",
        "base": [
            None,
            ["x2-1", "V", [], [], "x2-1", ["Agent:x4-1", "Theme:x8-1"], "", ""],
            ["x5-1", "N", [], ["beta#5#Agent(x2-1)"], "β5", ["Kind:betaA"], "", ""],
            ["x6-1", "N", [], ["beta#6#Theme(x2-1)"], "β6", ["Kind:betaB"], "", ""],
            ["x4-1", "N", [], [], "x4-1", ["Name:targetA"], "", ""],
            ["x8-1", "N", [], [], "x8-1", ["Name:targetB"], "", ""],
        ],
    }
    response = client.post("/v1/semantics/sr", json={"state": synthetic_state})
    assert response.status_code == 200
    rows = response.json()["truth_conditional_meaning"]
    assert any(
        row["object_id"] == 4
        and row["layer"] == 1
        and "Kind:betaA" in row["properties"]
        for row in rows
    )
    assert any(
        row["object_id"] == 8
        and row["layer"] == 1
        and "Kind:betaB" in row["properties"]
        for row in rows
    )
    assert not any(row["object_id"] in {5, 6} for row in rows)
