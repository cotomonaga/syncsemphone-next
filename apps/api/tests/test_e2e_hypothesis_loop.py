from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def _legacy_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _load_num_file(relative_path: str) -> str:
    return (_legacy_root() / relative_path).read_text(encoding="utf-8")


def test_api_e2e_hypothesis_loop_imi03_a_b_c() -> None:
    client = TestClient(app)

    init_response = client.post(
        "/v1/derivation/init",
        json={
            "grammar_id": "imi03",
            "numeration_text": _load_num_file("imi03/set-numeration/04.num"),
            "legacy_root": str(_legacy_root()),
        },
    )
    assert init_response.status_code == 200
    t0 = init_response.json()

    # 実験A: _03 の候補集合（baseline）
    baseline_candidates = client.post(
        "/v1/derivation/candidates",
        json={
            "state": t0,
            "left": 5,
            "right": 6,
            "rh_merge_version": "03",
            "lh_merge_version": "03",
        },
    )
    assert baseline_candidates.status_code == 200
    assert [row["rule_name"] for row in baseline_candidates.json()] == [
        "RH-Merge",
        "LH-Merge",
        "zero-Merge",
    ]

    # 実験B: _04 へ差し替えた候補集合（right=T）
    swapped_candidates = client.post(
        "/v1/derivation/candidates",
        json={
            "state": t0,
            "left": 5,
            "right": 6,
            "rh_merge_version": "04",
            "lh_merge_version": "04",
        },
    )
    assert swapped_candidates.status_code == 200
    assert [row["rule_name"] for row in swapped_candidates.json()] == [
        "LH-Merge",
        "zero-Merge",
    ]

    # 実験C: execute -> tree/tree_cat -> lf/sr -> resume roundtrip
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
    t1 = t1_response.json()

    tree_response = client.post(
        "/v1/observation/tree",
        json={"state": t1, "mode": "tree"},
    )
    tree_cat_response = client.post(
        "/v1/observation/tree",
        json={"state": t1, "mode": "tree_cat"},
    )
    assert tree_response.status_code == 200
    assert tree_cat_response.status_code == 200
    assert "&lt;br&gt;-ta" in tree_response.json()["csv_text"]
    assert "T&lt;br&gt;-ta" in tree_cat_response.json()["csv_text"]

    lf_response = client.post("/v1/semantics/lf", json={"state": t1})
    sr_response = client.post("/v1/semantics/sr", json={"state": t1})
    assert lf_response.status_code == 200
    assert sr_response.status_code == 200
    lf_rows = lf_response.json()["list_representation"]
    sr_rows = sr_response.json()["truth_conditional_meaning"]
    assert any("Name:ジョン" in row["semantics"] for row in lf_rows)
    assert any(row["object_id"] == 1 and row["layer"] == 1 for row in sr_rows)

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

    restored_tree = client.post(
        "/v1/observation/tree",
        json={"state": restored, "mode": "tree"},
    )
    restored_tree_cat = client.post(
        "/v1/observation/tree",
        json={"state": restored, "mode": "tree_cat"},
    )
    assert restored_tree.status_code == 200
    assert restored_tree_cat.status_code == 200
    assert restored_tree.json()["csv_text"] == tree_response.json()["csv_text"]
    assert restored_tree_cat.json()["csv_text"] == tree_cat_response.json()["csv_text"]
