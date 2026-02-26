from pathlib import Path

import pytest

from domain.numeration.generator import generate_numeration_from_sentence
from domain.numeration.init_builder import build_initial_derivation_state


class _StubTokenizer:
    def __init__(self, tokens: list[str]) -> None:
        self._tokens = tokens

    def tokenize(self, sentence: str, split_mode: str = "C") -> list[str]:
        return list(self._tokens)


def _legacy_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_generate_numeration_from_manual_tokens_for_imi03() -> None:
    generated = generate_numeration_from_sentence(
        grammar_id="imi03",
        sentence="ジョンがメアリを追いかけた",
        tokens=["ジョン", "が", "メアリ", "を", "追いかける", "た"],
        legacy_root=_legacy_root(),
    )
    assert generated.memo == "ジョンがメアリを追いかけた"
    assert generated.lexicon_ids == [60, 19, 103, 23, 187, 203]

    lines = generated.numeration_text.splitlines()
    assert len(lines) == 3
    first_row = lines[0].split("\t")
    assert first_row[0] == "ジョンがメアリを追いかけた"
    assert first_row[1:7] == ["60", "19", "103", "23", "187", "203"]


def test_generate_numeration_from_sentence_uses_tokenizer_when_tokens_not_given() -> None:
    generated = generate_numeration_from_sentence(
        grammar_id="imi03",
        sentence="ジョンがメアリを追いかけた",
        legacy_root=_legacy_root(),
        tokenizer=_StubTokenizer(["ジョン", "が", "メアリ", "を", "追いかける", "た"]),
    )
    assert generated.lexicon_ids == [60, 19, 103, 23, 187, 203]
    state = build_initial_derivation_state(
        grammar_id="imi03",
        numeration_text=generated.numeration_text,
        legacy_root=_legacy_root(),
    )
    assert state.basenum == 6
    assert state.base[5][1] == "V"
    assert state.base[6][1] == "T"


def test_generate_numeration_prefers_richer_sync_feature_candidate() -> None:
    generated = generate_numeration_from_sentence(
        grammar_id="imi03",
        sentence="追いかける",
        tokens=["追いかける"],
        legacy_root=_legacy_root(),
    )
    # 追いかけるは 133 と 187 が候補だが、sync/se が豊富な 187 を優先する。
    assert generated.token_resolutions[0].candidate_lexicon_ids[:2] == [187, 133]
    assert generated.lexicon_ids == [187]


def test_generate_numeration_raises_for_unknown_token() -> None:
    with pytest.raises(ValueError, match="Unknown token"):
        generate_numeration_from_sentence(
            grammar_id="imi03",
            sentence="未知語",
            tokens=["未知語"],
            legacy_root=_legacy_root(),
        )
