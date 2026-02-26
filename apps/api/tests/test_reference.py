from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def _legacy_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_reference_feature_docs_and_rule_docs_are_available() -> None:
    client = TestClient(app)

    features_response = client.get(f"/v1/reference/features?legacy_root={_legacy_root()}")
    assert features_response.status_code == 200
    features = features_response.json()
    assert len(features) > 0

    first_feature = features[0]["file_name"]
    feature_doc_response = client.get(
        f"/v1/reference/features/{first_feature}?legacy_root={_legacy_root()}"
    )
    assert feature_doc_response.status_code == 200
    assert len(feature_doc_response.json()["html_text"]) > 0

    rules_response = client.get(f"/v1/reference/rules/imi03?legacy_root={_legacy_root()}")
    assert rules_response.status_code == 200
    rules = rules_response.json()
    assert len(rules) > 0

    first_rule_file = rules[0]["file_name"]
    rule_doc_response = client.get(
        f"/v1/reference/rules/doc/{first_rule_file}?legacy_root={_legacy_root()}"
    )
    assert rule_doc_response.status_code == 200
    assert len(rule_doc_response.json()["html_text"]) > 0


def test_reference_rule_source_list_read_write(tmp_path: Path) -> None:
    client = TestClient(app)

    list_response = client.get(f"/v1/reference/grammars/imi03/rule-sources?legacy_root={_legacy_root()}")
    assert list_response.status_code == 200
    entries = list_response.json()
    assert len(entries) > 0

    rule_number = entries[0]["rule_number"]
    get_response = client.get(
        f"/v1/reference/grammars/imi03/rule-sources/{rule_number}?legacy_root={_legacy_root()}"
    )
    assert get_response.status_code == 200
    original_text = get_response.json()["source_text"]
    assert len(original_text) > 0

    update_root = tmp_path / "reference-edit-root"
    merge_rule_dir = update_root / "MergeRule"
    grammar_dir = update_root / "imi03"
    merge_rule_dir.mkdir(parents=True, exist_ok=True)
    grammar_dir.mkdir(parents=True, exist_ok=True)

    (grammar_dir / "imi03R.pl").write_text(
        "my @rule_set = ([ 'DummyRule', 'DummyRule_01', 2 ]);",
        encoding="utf-8",
    )
    (merge_rule_dir / "DummyRule_01.pl").write_text("sub dummy { return 1; }\n", encoding="utf-8")

    save_response = client.post(
        "/v1/reference/grammars/imi03/rule-sources/1",
        json={
            "legacy_root": str(update_root),
            "source_text": "sub dummy { return 2; }\n",
        },
    )
    assert save_response.status_code == 200
    saved = save_response.json()
    assert saved["source_text"] == "sub dummy { return 2; }\n"
    assert (merge_rule_dir / "DummyRule_01.pl").read_text(encoding="utf-8") == "sub dummy { return 2; }\n"
