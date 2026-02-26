from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def _sample_num_text(memo: str = "sample") -> str:
    return f"{memo}\t60\t19\n\t\t\n\t1\t2\n"


def test_derivation_grammars_lists_known_profiles() -> None:
    client = TestClient(app)
    response = client.get("/v1/derivation/grammars")
    assert response.status_code == 200
    body = response.json()
    grammar_ids = {row["grammar_id"] for row in body}
    assert "imi03" in grammar_ids
    assert "japanese2" in grammar_ids


def test_numeration_files_load_compose_and_save(tmp_path: Path) -> None:
    client = TestClient(app)

    legacy_root = tmp_path
    set_dir = legacy_root / "imi03" / "set-numeration"
    set_dir.mkdir(parents=True, exist_ok=True)
    sample_path = set_dir / "01.num"
    sample_path.write_text(_sample_num_text("set-file"), encoding="utf-8")

    list_response = client.get(
        f"/v1/derivation/numeration/files?grammar_id=imi03&source=set&legacy_root={legacy_root}"
    )
    assert list_response.status_code == 200
    rows = list_response.json()
    assert len(rows) == 1
    assert rows[0]["file_name"] == "01.num"
    assert rows[0]["memo"] == "set-file"

    load_response = client.post(
        "/v1/derivation/numeration/load",
        json={
            "grammar_id": "imi03",
            "path": str(sample_path),
            "legacy_root": str(legacy_root),
        },
    )
    assert load_response.status_code == 200
    assert "set-file" in load_response.json()["numeration_text"]

    compose_response = client.post(
        "/v1/derivation/numeration/compose",
        json={
            "memo": "composed",
            "lexicon_ids": [60, 19, 103],
            "plus_values": ["", "", "target"],
            "idx_values": ["1", "2", "3"],
        },
    )
    assert compose_response.status_code == 200
    composed = compose_response.json()["numeration_text"]
    assert "composed" in composed
    assert "\t60\t19\t103" in composed

    save_response = client.post(
        "/v1/derivation/numeration/save",
        json={
            "grammar_id": "imi03",
            "numeration_text": composed,
            "legacy_root": str(legacy_root),
        },
    )
    assert save_response.status_code == 200
    saved_path = Path(save_response.json()["path"])
    assert saved_path.exists()

    list_saved_response = client.get(
        f"/v1/derivation/numeration/files?grammar_id=imi03&source=saved&legacy_root={legacy_root}"
    )
    assert list_saved_response.status_code == 200
    saved_rows = list_saved_response.json()
    assert len(saved_rows) == 1

