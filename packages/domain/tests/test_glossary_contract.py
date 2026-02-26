import json
from pathlib import Path


def _specs_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "docs/specs"


def test_glossary_contract_sections_and_terms_exist() -> None:
    specs = _specs_dir()
    glossary_text = (specs / "glossary-ja.md").read_text(encoding="utf-8")
    contract = json.loads((specs / "glossary-contract-ja.json").read_text(encoding="utf-8"))

    assert contract.get("version") == "v1"
    required_sections = contract.get("required_sections", [])
    required_terms = contract.get("required_terms", [])
    assert isinstance(required_sections, list)
    assert isinstance(required_terms, list)

    missing_sections = [section for section in required_sections if section not in glossary_text]
    missing_terms = [term for term in required_terms if term not in glossary_text]

    assert missing_sections == [], f"Missing glossary sections: {missing_sections}"
    assert missing_terms == [], f"Missing glossary terms: {missing_terms}"
