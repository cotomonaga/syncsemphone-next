from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from domain.lexicon.legacy_loader import load_legacy_lexicon
from domain.lexicon.models import LexiconEntry
from domain.numeration.parser import NUMERATION_SLOT_COUNT


_IGNORED_CHARS = {" ", "　", "。", "．", ".", "、", "，", ",", "!", "！", "?", "？"}


def _normalize_token(token: str) -> str:
    return "".join(ch for ch in token.strip() if ch not in _IGNORED_CHARS)


class MorphTokenizer(Protocol):
    def tokenize(self, sentence: str, split_mode: str = "C") -> list[str]:
        raise NotImplementedError


class SudachiMorphTokenizer:
    def __init__(self, dictionary: str = "core") -> None:
        try:
            from sudachipy import dictionary as sudachi_dictionary  # type: ignore
        except Exception as exc:  # pragma: no cover - import environment dependent
            raise ValueError(
                "SudachiPy is not available. Install SudachiPy and SudachiDict-core."
            ) from exc
        self._tokenizer = sudachi_dictionary.Dictionary(dict=dictionary).create()
        self._split_mode = {
            "A": self._tokenizer.SplitMode.A,
            "B": self._tokenizer.SplitMode.B,
            "C": self._tokenizer.SplitMode.C,
        }

    def tokenize(self, sentence: str, split_mode: str = "C") -> list[str]:
        mode = self._split_mode.get(split_mode.upper())
        if mode is None:
            raise ValueError(f"Unsupported split_mode: {split_mode}. Use A/B/C.")
        out: list[str] = []
        for morpheme in self._tokenizer.tokenize(sentence, mode):
            dictionary_form = morpheme.dictionary_form()
            surface = dictionary_form if dictionary_form and dictionary_form != "*" else morpheme.surface()
            normalized = _normalize_token(surface)
            if normalized != "":
                out.append(normalized)
        if not out:
            raise ValueError("Sentence tokenization produced no tokens")
        return out


@dataclass(frozen=True)
class TokenResolution:
    token: str
    lexicon_id: int
    candidate_lexicon_ids: list[int]


@dataclass(frozen=True)
class GeneratedNumeration:
    memo: str
    lexicon_ids: list[int]
    token_resolutions: list[TokenResolution]
    numeration_text: str


def _phono_variants(phono: str) -> list[str]:
    out: list[str] = []
    normalized = _normalize_token(phono)
    if normalized != "":
        out.append(normalized)
    stripped = normalized.strip("-")
    if stripped != "" and stripped != normalized:
        out.append(stripped)
    return out


def _build_surface_index(lexicon: dict[int, LexiconEntry]) -> dict[str, list[int]]:
    index: dict[str, list[int]] = {}
    for lexicon_id, entry in lexicon.items():
        surfaces: list[str] = []
        entry_surface = _normalize_token(entry.entry)
        if entry_surface != "":
            surfaces.append(entry_surface)
        surfaces.extend(_phono_variants(entry.phono))
        for surface in surfaces:
            index.setdefault(surface, []).append(lexicon_id)
    return index


def _is_silent_phono(entry: LexiconEntry) -> bool:
    normalized = _normalize_token(entry.phono).strip("-")
    return normalized in {"", "φ", "zero"}


def _candidate_sort_key(
    grammar_id: str,
    token: str,
    lexicon_id: int,
    lexicon: dict[int, LexiconEntry],
) -> tuple[int, int, int, int, int, int, int, int, int]:
    entry = lexicon[lexicon_id]
    token_norm = _normalize_token(token)
    entry_norm = _normalize_token(entry.entry)
    phono_norm = _normalize_token(entry.phono).strip("-")

    entry_exact = 1 if entry_norm == token_norm else 0
    phono_exact = 1 if phono_norm == token_norm else 0
    non_silent = 0 if _is_silent_phono(entry) else 1
    pred_count = len(entry.predicates)
    has_feature_17 = any(",17," in feature for feature in entry.sync_features)
    has_l_feature = any(
        len(feature.split(",")) > 1 and feature.split(",")[1].endswith("L")
        for feature in entry.sync_features
    )
    has_j_merge_feature = any("J-Merge" in feature for feature in entry.sync_features)
    imi_mode = grammar_id.startswith("imi")

    # 既存 .num に寄せるため、まず可視音形を優先し、次に文法片の傾向に合わせて選ぶ。
    return (
        -entry_exact,
        -non_silent,
        -phono_exact,
        -(1 if (imi_mode and has_feature_17) else 0),
        1 if (imi_mode and has_l_feature) else 0,
        1 if (imi_mode and has_j_merge_feature) else 0,
        pred_count,
        -len(entry.sync_features),
        lexicon_id,
    )


def _resolve_token(
    grammar_id: str,
    token: str,
    *,
    surface_index: dict[str, list[int]],
    lexicon: dict[int, LexiconEntry],
) -> TokenResolution:
    normalized = _normalize_token(token)
    if normalized == "":
        raise ValueError("Empty token is not allowed")
    candidates = surface_index.get(normalized, [])
    if not candidates:
        raise ValueError(f"Unknown token for lexicon lookup: {token}")
    deduped = sorted(
        set(candidates),
        key=lambda lexicon_id: _candidate_sort_key(grammar_id, normalized, lexicon_id, lexicon),
    )
    return TokenResolution(
        token=normalized,
        lexicon_id=deduped[0],
        candidate_lexicon_ids=deduped,
    )


def _build_numeration_text(*, memo: str, lexicon_ids: list[int]) -> str:
    if len(lexicon_ids) > NUMERATION_SLOT_COUNT:
        raise ValueError(
            f"Too many tokens for numeration slots: {len(lexicon_ids)} > {NUMERATION_SLOT_COUNT}"
        )
    line1 = [memo] + ["" for _ in range(NUMERATION_SLOT_COUNT)]
    line2 = [" "] + ["" for _ in range(NUMERATION_SLOT_COUNT)]
    line3 = [" "] + ["" for _ in range(NUMERATION_SLOT_COUNT)]
    for i, lexicon_id in enumerate(lexicon_ids, start=1):
        line1[i] = str(lexicon_id)
        line3[i] = str(i)
    return "\n".join(["\t".join(line1), "\t".join(line2), "\t".join(line3)])


def generate_numeration_from_sentence(
    *,
    grammar_id: str,
    sentence: str,
    legacy_root: Path,
    tokens: list[str] | None = None,
    split_mode: str = "C",
    tokenizer: MorphTokenizer | None = None,
) -> GeneratedNumeration:
    memo = sentence.strip()
    if memo == "":
        raise ValueError("sentence must not be empty")

    lexicon = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=grammar_id)
    surface_index = _build_surface_index(lexicon)

    if tokens is None:
        active_tokenizer = tokenizer or SudachiMorphTokenizer(dictionary="core")
        token_values = active_tokenizer.tokenize(sentence, split_mode=split_mode)
    else:
        token_values = tokens

    resolutions: list[TokenResolution] = []
    for token in token_values:
        normalized = _normalize_token(token)
        if normalized == "":
            continue
        resolutions.append(
            _resolve_token(
                grammar_id=grammar_id,
                token=normalized,
                surface_index=surface_index,
                lexicon=lexicon,
            )
        )

    if not resolutions:
        raise ValueError("No valid tokens were resolved from input")

    lexicon_ids = [resolution.lexicon_id for resolution in resolutions]
    numeration_text = _build_numeration_text(memo=memo, lexicon_ids=lexicon_ids)

    return GeneratedNumeration(
        memo=memo,
        lexicon_ids=lexicon_ids,
        token_resolutions=resolutions,
        numeration_text=numeration_text,
    )
