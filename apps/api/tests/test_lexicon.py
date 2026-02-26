from pathlib import Path
import tempfile

from fastapi.testclient import TestClient

from app.main import app


def _legacy_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_lexicon_get_yaml_imi03() -> None:
    client = TestClient(app)
    response = client.get(
        "/v1/lexicon/imi03",
        params={"format": "yaml", "legacy_root": str(_legacy_root())},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["grammar_id"] == "imi03"
    assert body["format"] == "yaml"
    assert body["entry_count"] > 0
    assert body["lexicon_path"].endswith("lexicon-all.csv")
    assert 'grammar_id: "imi03"' in body["content_text"]
    assert "entries:" in body["content_text"]


def test_lexicon_get_csv_japanese2() -> None:
    client = TestClient(app)
    response = client.get(
        "/v1/lexicon/japanese2",
        params={"format": "csv", "legacy_root": str(_legacy_root())},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["grammar_id"] == "japanese2"
    assert body["format"] == "csv"
    assert body["entry_count"] > 0
    assert body["lexicon_path"].endswith("japanese2.csv")
    assert "\t" in body["content_text"]


def test_lexicon_get_returns_400_for_unknown_grammar() -> None:
    client = TestClient(app)
    response = client.get(
        "/v1/lexicon/unknown",
        params={"format": "yaml", "legacy_root": str(_legacy_root())},
    )

    assert response.status_code == 400
    assert "Unsupported grammar_id" in response.json()["detail"]


def test_lexicon_validate_yaml_success() -> None:
    client = TestClient(app)
    yaml_text = """
meta:
  grammar_id: "imi03"
entries:
  - no: 60
    entry: "ジョン"
    phono: "ジョン"
    category: "N"
    predication: []
    sync:
      - "3,53,target,id"
    idslot: "id"
    semantics:
      -
        attr: "Name"
        value: "ジョン"
    note: "固有名"
"""
    response = client.post(
        "/v1/lexicon/imi03/validate",
        json={"yaml_text": yaml_text},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["entry_count"] == 1
    assert body["errors"] == []
    assert "\t" in body["preview_csv_text"]


def test_lexicon_validate_yaml_failure() -> None:
    client = TestClient(app)
    response = client.post(
        "/v1/lexicon/imi03/validate",
        json={"yaml_text": "entries: not-a-list"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert body["errors"]


def test_lexicon_import_yaml_returns_csv_preview() -> None:
    client = TestClient(app)
    yaml_text = """
entries:
  - no: 1
    entry: "x"
    phono: "x"
    category: "N"
    predication: []
    sync: []
    idslot: "id"
    semantics: []
    note: ""
"""
    response = client.post(
        "/v1/lexicon/imi03/import",
        json={"yaml_text": yaml_text},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["entry_count"] == 1
    assert "\t" in body["csv_text"]


def test_lexicon_import_yaml_returns_400_when_invalid() -> None:
    client = TestClient(app)
    response = client.post(
        "/v1/lexicon/imi03/import",
        json={"yaml_text": "entries: []\nmeta: 1"},
    )
    assert response.status_code == 400


def test_lexicon_commit_yaml_success_without_compatibility_tests() -> None:
    client = TestClient(app)
    with tempfile.TemporaryDirectory() as tmpdir:
        legacy_root = Path(tmpdir)
        seed_row = "\t".join(
            [
                "1",
                "old",
                "old",
                "N",
                "0",
                "",
                "",
                "",
                "0",
                "",
                "",
                "",
                "",
                "",
                "id",
                "0",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "0",
            ]
        )
        (legacy_root / "lexicon-all.csv").write_text(seed_row + "\n", encoding="utf-8")

        yaml_text = """
entries:
  - no: 1
    entry: "new"
    phono: "new"
    category: "N"
    predication: []
    sync: []
    idslot: "id"
    semantics: []
    note: ""
"""
        response = client.post(
            "/v1/lexicon/imi03/commit",
            json={
                "yaml_text": yaml_text,
                "legacy_root": str(legacy_root),
                "run_compatibility_tests": False,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["committed"] is True
        assert body["rolled_back"] is False
        assert body["compatibility_passed"] is True
        assert Path(body["backup_path"]).exists()
        assert "new" in (legacy_root / "lexicon-all.csv").read_text(encoding="utf-8")
