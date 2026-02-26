from domain.lexicon.importer import build_lexicon_csv_text, validate_lexicon_yaml_text
from domain.lexicon.models import LexiconEntry


def test_build_lexicon_csv_text_produces_30_columns() -> None:
    csv_text = build_lexicon_csv_text(
        {
            60: LexiconEntry(
                lexicon_id=60,
                entry="ジョン",
                phono="ジョン",
                category="N",
                predicates=[],
                sync_features=["3,53,target,id"],
                idslot="id",
                semantics=["Name:ジョン"],
                note="[固有名]",
            )
        }
    )
    line = csv_text.splitlines()[0]
    assert len(line.split("\t")) == 30
    assert line.split("\t")[0] == "60"


def test_validate_lexicon_yaml_text_success() -> None:
    yaml_text = """
meta:
  grammar_id: "imi03"
  source_csv: "lexicon-all.csv"
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
    result = validate_lexicon_yaml_text(grammar_id="imi03", yaml_text=yaml_text)
    assert result.valid is True
    assert result.entry_count == 1
    assert result.errors == []
    assert "meta:" in result.normalized_yaml_text
    assert "\t" in result.preview_csv_text


def test_validate_lexicon_yaml_text_detects_mismatch() -> None:
    yaml_text = """
meta:
  grammar_id: "japanese2"
entries: []
"""
    result = validate_lexicon_yaml_text(grammar_id="imi03", yaml_text=yaml_text)
    assert result.valid is False
    assert any("mismatch" in err for err in result.errors)


def test_validate_lexicon_yaml_text_rejects_predication_overflow() -> None:
    yaml_text = """
entries:
  - no: 1
    entry: "x"
    phono: "x"
    category: "N"
    predication:
      - ["a", "b", "c"]
      - ["d", "e", "f"]
    sync: []
    idslot: "id"
    semantics: []
    note: ""
"""
    result = validate_lexicon_yaml_text(grammar_id="imi03", yaml_text=yaml_text)
    assert result.valid is False
    assert any("predication supports at most 1" in err for err in result.errors)
