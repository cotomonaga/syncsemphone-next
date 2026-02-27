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


@dataclass(frozen=True)
class MorphemeAnalysis:
    token: str
    surface: str
    dictionary_form: str
    pos_major: str
    conjugation_form: str


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

    def _resolve_mode(self, split_mode: str) -> object:
        mode = self._split_mode.get(split_mode.upper())
        if mode is None:
            raise ValueError(f"Unsupported split_mode: {split_mode}. Use A/B/C.")
        return mode

    def _analyze(self, sentence: str, split_mode: str = "C") -> list[MorphemeAnalysis]:
        mode = self._resolve_mode(split_mode)
        out: list[MorphemeAnalysis] = []
        for morpheme in self._tokenizer.tokenize(sentence, mode):
            surface_raw = morpheme.surface()
            surface = _normalize_token(surface_raw)
            dictionary_form_raw = morpheme.dictionary_form()
            dictionary_form = (
                dictionary_form_raw
                if dictionary_form_raw and dictionary_form_raw != "*"
                else surface_raw
            )
            token = _normalize_token(dictionary_form)
            if token == "":
                continue
            pos = morpheme.part_of_speech()
            pos_major = pos[0] if len(pos) > 0 else ""
            conjugation_form = pos[5] if len(pos) > 5 else ""
            out.append(
                MorphemeAnalysis(
                    token=token,
                    surface=surface,
                    dictionary_form=_normalize_token(dictionary_form),
                    pos_major=pos_major,
                    conjugation_form=conjugation_form,
                )
            )
        return out

    def _adjective_stem(self, row: MorphemeAnalysis) -> str:
        if row.dictionary_form.endswith("い") and len(row.dictionary_form) > 1:
            return row.dictionary_form[:-1]
        if row.surface.endswith("い") and len(row.surface) > 1:
            return row.surface[:-1]
        base = row.surface if row.surface != "" else row.token
        return base

    def _tokens_with_tense_supplements(self, rows: list[MorphemeAnalysis]) -> list[str]:
        out: list[str] = []
        i = 0
        while i < len(rows):
            row = rows[i]
            next_row = rows[i + 1] if i + 1 < len(rows) else None

            # 形容詞 + た => 語幹 + かった（例: かわい + かった）
            if (
                row.pos_major == "形容詞"
                and next_row is not None
                and next_row.pos_major == "助動詞"
                and next_row.dictionary_form == "た"
            ):
                stem = self._adjective_stem(row)
                if stem != "":
                    out.append(stem)
                out.append("かった")
                i += 2
                continue

            # 文末形容詞（終止）=> 語幹 + い（例: かわい + い）
            if row.pos_major == "形容詞" and "終止形" in row.conjugation_form:
                stem = self._adjective_stem(row)
                if stem != "" and stem != row.token:
                    out.append(stem)
                    out.append("い")
                    i += 1
                    continue

            # だ + た => だった
            if (
                row.pos_major == "助動詞"
                and row.dictionary_form == "だ"
                and next_row is not None
                and next_row.pos_major == "助動詞"
                and next_row.dictionary_form == "た"
            ):
                out.append("だった")
                i += 2
                continue

            # です + た => でした
            if (
                row.pos_major == "助動詞"
                and row.dictionary_form == "です"
                and next_row is not None
                and next_row.pos_major == "助動詞"
                and next_row.dictionary_form == "た"
            ):
                out.append("でした")
                i += 2
                continue

            out.append(row.token)

            # 「いる」は V 語彙と T 語彙（る）に分ける運用を優先する。
            if row.dictionary_form == "いる" and row.pos_major == "動詞" and "終止形" in row.conjugation_form:
                out.append("る")

            i += 1

        return out

    def tokenize(self, sentence: str, split_mode: str = "C") -> list[str]:
        out = self._tokens_with_tense_supplements(self._analyze(sentence, split_mode=split_mode))
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
