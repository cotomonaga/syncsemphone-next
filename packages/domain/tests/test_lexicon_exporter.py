from pathlib import Path

from domain.lexicon.exporter import build_lexicon_yaml_text, export_legacy_lexicon_bundle
from domain.lexicon.models import LexiconEntry


def _legacy_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_build_lexicon_yaml_text_renders_structured_fields() -> None:
    entries = {
        60: LexiconEntry(
            lexicon_id=60,
            entry="ジョン",
            phono="ジョン",
            category="N",
            predicates=[("x1", "Agent", "Theme")],
            sync_features=["3,53,target,id"],
            idslot="id",
            semantics=["Name:ジョン", "Case:ga"],
            note="[固有名]",
        )
    }

    text = build_lexicon_yaml_text(
        grammar_id="imi03",
        source_csv="lexicon-all.csv",
        entries=entries,
        generated_at="2026-02-26T00:00:00Z",
    )

    assert 'grammar_id: "imi03"' in text
    assert 'source_csv: "lexicon-all.csv"' in text
    assert "  - no: 60" in text
    assert 'entry: "ジョン"' in text
    assert '      - ["x1", "Agent", "Theme"]' in text
    assert '        attr: "Name"' in text
    assert '        value: "ジョン"' in text
    assert 'note: "固有名"' in text


def test_export_legacy_lexicon_bundle_imi03_uses_lexicon_all() -> None:
    bundle = export_legacy_lexicon_bundle(legacy_root=_legacy_root(), grammar_id="imi03")

    assert bundle.lexicon_path.name == "lexicon-all.csv"
    assert bundle.entry_count > 0
    assert bundle.csv_text != ""
    assert "meta:" in bundle.yaml_text
    assert 'grammar_id: "imi03"' in bundle.yaml_text


def test_export_legacy_lexicon_bundle_japanese2_uses_japanese2_csv() -> None:
    bundle = export_legacy_lexicon_bundle(legacy_root=_legacy_root(), grammar_id="japanese2")

    assert bundle.lexicon_path.name == "japanese2.csv"
    assert "japanese2/" in str(bundle.lexicon_path)
    assert bundle.entry_count > 0
    assert "\t" in bundle.csv_text
    assert 'grammar_id: "japanese2"' in bundle.yaml_text
