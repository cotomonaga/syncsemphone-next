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
    assert "title" in features[0]
    assert features[0]["title"] != ""

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


def test_reference_lexicon_summary_and_items() -> None:
    client = TestClient(app)

    summary_response = client.get(f"/v1/reference/grammars/imi03/lexicon-summary?legacy_root={_legacy_root()}")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["grammar_id"] == "imi03"
    assert summary["entry_count"] > 0
    assert summary["legacy_grammar_no"] == 5
    assert summary["legacy_lexicon_cgi_url"].endswith("lexicon.cgi?grammar=5")
    assert len(summary["category_counts"]) > 0

    items_response = client.get(
        f"/v1/reference/grammars/imi03/lexicon-items?page=1&page_size=15&legacy_root={_legacy_root()}"
    )
    assert items_response.status_code == 200
    items = items_response.json()
    assert items["grammar_id"] == "imi03"
    assert items["category_filter"] is None
    assert items["page"] == 1
    assert items["page_size"] == 15
    assert items["total_count"] >= 15
    assert len(items["items"]) == 15
    first = items["items"][0]
    assert "lexicon_id" in first
    assert "entry" in first
    assert "sync_features" in first
    assert "semantics" in first

    category_response = client.get(
        f"/v1/reference/grammars/imi03/lexicon-items?page=1&page_size=50&category=N&legacy_root={_legacy_root()}"
    )
    assert category_response.status_code == 200
    category_items = category_response.json()
    assert category_items["category_filter"] == "N"
    assert category_items["total_count"] > 0
    assert len(category_items["items"]) > 0
    assert all(item["category"] == "N" for item in category_items["items"])


def test_reference_lexicon_items_by_ids() -> None:
    client = TestClient(app)
    response = client.post(
        f"/v1/reference/grammars/imi03/lexicon-items/by-ids?legacy_root={_legacy_root()}",
        json={"ids": [309, 309, 204, 999999]},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["grammar_id"] == "imi03"
    assert payload["requested_count"] == 3
    assert payload["found_count"] == 2
    assert 999999 in payload["missing_ids"]
    items_by_id = {item["lexicon_id"]: item for item in payload["items"]}
    assert items_by_id[999999]["found"] is False
    assert items_by_id[309]["found"] is True
    assert items_by_id[204]["found"] is True


def test_reference_merge_rules_and_rule_compare() -> None:
    client = TestClient(app)

    rules_response = client.get(f"/v1/reference/grammars/imi03/merge-rules?legacy_root={_legacy_root()}")
    assert rules_response.status_code == 200
    rules = rules_response.json()
    assert len(rules) > 0
    assert any(row["rule_name"] == "RH-Merge" for row in rules)
    assert any(row["rule_name"] == "LH-Merge" for row in rules)

    rh_rule_number = next(row["rule_number"] for row in rules if row["rule_name"] == "RH-Merge")
    compare_response = client.get(
        f"/v1/reference/grammars/imi03/rule-compare/{rh_rule_number}?legacy_root={_legacy_root()}"
    )
    assert compare_response.status_code == 200
    compare = compare_response.json()
    assert compare["rule_name"] == "RH-Merge"
    assert compare["perl_file_name"].endswith(".pl")
    assert "rule_name == \"RH-Merge\"" in compare["python_source_text"]
