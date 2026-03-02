from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from domain.grammar.rule_catalog import load_rule_catalog
from domain.lexicon.legacy_loader import load_legacy_lexicon
from domain.lexicon.models import LexiconEntry
from domain.numeration.parser import NUMERATION_SLOT_COUNT


_IGNORED_CHARS = {" ", "　", "。", "．", ".", "、", "，", ",", "!", "！", "?", "？"}
_JAPANESE2_ONLY_SYNC_FEATURE_CODES = {"1L", "2L", "3L"}
_RULE_NAME_MARKERS = (
    "RH-Merge",
    "LH-Merge",
    "J-Merge",
    "P-Merge",
    "rel-Merge",
    "property-Merge",
    "property-no",
    "property-da",
    "sase1",
    "sase2",
    "rare1",
    "rare2",
    "Pickup",
    "Landing",
    "Partitioning",
    "zero-Merge",
)


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
            next2_row = rows[i + 2] if i + 2 < len(rows) else None

            # X + する + た => Xした（例: ふわふわ + する + た => ふわふわした）
            if (
                next_row is not None
                and next2_row is not None
                and next_row.pos_major == "動詞"
                and next_row.dictionary_form == "する"
                and next2_row.pos_major == "助動詞"
                and next2_row.dictionary_form == "た"
            ):
                combined = _normalize_token(f"{row.surface}{next_row.surface}{next2_row.surface}")
                if combined != "":
                    out.append(combined)
                    i += 3
                    continue

            # 動詞 + て + いる => 動詞連用 + ている（例: 食べる + て + いる => 食べている）
            if (
                row.pos_major == "動詞"
                and next_row is not None
                and next2_row is not None
                and next_row.token == "て"
                and next2_row.pos_major == "動詞"
                and next2_row.dictionary_form == "いる"
            ):
                combined = _normalize_token(f"{row.surface}{next_row.surface}{next2_row.surface}")
                if combined != "":
                    out.append(combined)
                    i += 3
                    continue

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
    candidate_compatibility: list["CandidateCompatibility"]


@dataclass(frozen=True)
class CandidateCompatibility:
    lexicon_id: int
    compatible: bool
    reason_codes: list[str]
    missing_rule_names: list[str]
    referenced_rule_names: list[str]


@dataclass(frozen=True)
class GeneratedNumeration:
    memo: str
    lexicon_ids: list[int]
    token_resolutions: list[TokenResolution]
    numeration_text: str
    auto_supplements: list["AutoSupplement"]


@dataclass(frozen=True)
class AutoSupplement:
    kind: str
    lexicon_id: int
    entry: str
    count: int
    reason: str
    feature_code: str
    label: str
    demand_count: int
    provider_count: int


@dataclass(frozen=True)
class _PartnerRequirement:
    feature_code: str  # "25" or "33"
    label: str


def _extract_sync_feature_codes(entry: LexiconEntry) -> set[str]:
    codes: set[str] = set()
    for feature in entry.sync_features:
        parts = [part.strip() for part in feature.split(",")]
        if len(parts) > 1 and parts[1] != "":
            codes.add(parts[1])
    return codes


def _extract_referenced_rule_names(entry: LexiconEntry) -> list[str]:
    values = list(entry.sync_features) + list(entry.semantics)
    referenced: set[str] = set()
    for value in values:
        if value == "":
            continue
        for marker in _RULE_NAME_MARKERS:
            if marker in value:
                referenced.add(marker)
    return sorted(referenced)


def _infer_candidate_compatibility(
    *,
    grammar_id: str,
    entry: LexiconEntry,
    grammar_rule_names: set[str],
) -> CandidateCompatibility:
    reason_codes: list[str] = []
    missing_rule_names: list[str] = []
    referenced_rule_names = _extract_referenced_rule_names(entry)

    sync_codes = _extract_sync_feature_codes(entry)
    has_japanese2_only_code = any(
        code in _JAPANESE2_ONLY_SYNC_FEATURE_CODES for code in sync_codes
    )
    if has_japanese2_only_code and grammar_id != "japanese2":
        reason_codes.append("requires_japanese2_l_feature")

    if referenced_rule_names:
        missing = sorted(
            rule_name for rule_name in referenced_rule_names if rule_name not in grammar_rule_names
        )
        if missing:
            missing_rule_names.extend(missing)
            reason_codes.append("missing_required_rule")

    compatible = len(reason_codes) == 0
    return CandidateCompatibility(
        lexicon_id=entry.lexicon_id,
        compatible=compatible,
        reason_codes=reason_codes,
        missing_rule_names=missing_rule_names,
        referenced_rule_names=referenced_rule_names,
    )


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
    *,
    token_prev: str | None = None,
    token_next: str | None = None,
 ) -> tuple[int, ...]:
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
    # japanese2 の「本」は 227 を既定選択にして Num 要求(100)を避ける。
    japanese2_hon_priority = 0
    if grammar_id == "japanese2" and token_norm == "本":
        if lexicon_id == 227:
            japanese2_hon_priority = -1
        elif lexicon_id == 100:
            japanese2_hon_priority = 1

    # japanese2 の「と」は 171-lite(9301) を既定選択にし、Content:0,24 の副作用を避ける。
    japanese2_to_priority = 0
    if grammar_id == "japanese2" and token_norm == "と":
        if lexicon_id == 9301:
            japanese2_to_priority = -1
        elif lexicon_id == 171:
            japanese2_to_priority = 1

    # japanese2 の「を」は「...を食べている...」文脈で Z 系(181/189)を優先する。
    # 既定は 181(状況) を先に、次点で 189(Path) を試す。
    japanese2_wo_priority = 0
    if (
        grammar_id == "japanese2"
        and token_norm == "を"
        and _normalize_token(token_next or "") == "食べている"
    ):
        if lexicon_id == 181:
            japanese2_wo_priority = -2
        elif lexicon_id == 189:
            japanese2_wo_priority = -1
        elif lexicon_id in {23, 197, 297}:
            japanese2_wo_priority = 1

    # 既存 .num に寄せるため、まず可視音形を優先し、次に文法片の傾向に合わせて選ぶ。
    return (
        japanese2_wo_priority,
        japanese2_to_priority,
        japanese2_hon_priority,
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
    grammar_rule_names: set[str],
    token_prev: str | None = None,
    token_next: str | None = None,
) -> TokenResolution:
    normalized = _normalize_token(token)
    if normalized == "":
        raise ValueError("Empty token is not allowed")
    candidates = surface_index.get(normalized, [])
    if not candidates:
        raise ValueError(f"Unknown token for lexicon lookup: {token}")
    deduped = sorted(
        set(candidates),
        key=lambda lexicon_id: _candidate_sort_key(
            grammar_id,
            normalized,
            lexicon_id,
            lexicon,
            token_prev=token_prev,
            token_next=token_next,
        ),
    )
    compatibilities = [
        _infer_candidate_compatibility(
            grammar_id=grammar_id,
            entry=lexicon[lexicon_id],
            grammar_rule_names=grammar_rule_names,
        )
        for lexicon_id in deduped
    ]
    compatible_ids = [
        row.lexicon_id
        for row in compatibilities
        if row.compatible
    ]
    selected_lexicon_id = compatible_ids[0] if compatible_ids else deduped[0]
    return TokenResolution(
        token=normalized,
        lexicon_id=selected_lexicon_id,
        candidate_lexicon_ids=deduped,
        candidate_compatibility=compatibilities,
    )


def _extract_partner_requirements(entry: LexiconEntry) -> list[_PartnerRequirement]:
    requirements: list[_PartnerRequirement] = []
    for semantic in entry.semantics:
        _, _, raw_value = semantic.partition(":")
        value = raw_value.strip()
        if value == "" or "," not in value:
            continue
        parts = value.split(",")
        if len(parts) < 3:
            continue
        feature_code = parts[1].strip()
        label = parts[2].strip()
        if feature_code in {"25", "33"} and label != "":
            requirements.append(_PartnerRequirement(feature_code=feature_code, label=label))
    return requirements


def _extract_partner_capabilities(entry: LexiconEntry) -> tuple[set[str], set[str]]:
    plain: set[str] = set()
    labeled: set[str] = set()
    for feature in entry.sync_features:
        value = feature.strip()
        if value == "":
            continue
        if "," not in value or not any(ch.isdigit() for ch in value.split(",", 1)[1]):
            plain.add(value)
            continue
        parts = value.split(",")
        if len(parts) < 3:
            continue
        code = parts[1].strip()
        label = parts[2].strip()
        if code in {"11", "12"} and label != "":
            labeled.add(label)
    return plain, labeled


def _requirement_is_satisfied(
    requirement: _PartnerRequirement,
    *,
    plain_capabilities: set[str],
    labeled_capabilities: set[str],
) -> bool:
    if requirement.feature_code == "25":
        return requirement.label in plain_capabilities
    if requirement.feature_code == "33":
        return requirement.label in labeled_capabilities
    return False


def _optimize_partner_friendly_selection(
    resolutions: list[TokenResolution],
    *,
    lexicon: dict[int, LexiconEntry],
) -> list[int]:
    if len(resolutions) <= 1:
        return [resolution.lexicon_id for resolution in resolutions]

    candidate_ids_by_slot: list[list[int]] = []
    candidate_rank_by_slot: list[dict[int, int]] = []
    for resolution in resolutions:
        compatible_ids = [
            row.lexicon_id
            for row in resolution.candidate_compatibility
            if row.compatible
        ]
        allowed_ids = compatible_ids if compatible_ids else resolution.candidate_lexicon_ids
        deduped = list(dict.fromkeys(allowed_ids or [resolution.lexicon_id]))
        if resolution.lexicon_id not in deduped:
            deduped.insert(0, resolution.lexicon_id)
        candidate_ids_by_slot.append(deduped)
        candidate_rank_by_slot.append({lexicon_id: idx for idx, lexicon_id in enumerate(deduped)})

    capabilities_cache: dict[int, tuple[set[str], set[str]]] = {}
    requirements_cache: dict[int, list[_PartnerRequirement]] = {}

    def _capabilities_for(lexicon_id: int) -> tuple[set[str], set[str]]:
        if lexicon_id not in capabilities_cache:
            entry = lexicon.get(lexicon_id)
            if entry is None:
                capabilities_cache[lexicon_id] = (set(), set())
            else:
                capabilities_cache[lexicon_id] = _extract_partner_capabilities(entry)
        return capabilities_cache[lexicon_id]

    def _requirements_for(lexicon_id: int) -> list[_PartnerRequirement]:
        if lexicon_id not in requirements_cache:
            entry = lexicon.get(lexicon_id)
            if entry is None:
                requirements_cache[lexicon_id] = []
            else:
                requirements_cache[lexicon_id] = _extract_partner_requirements(entry)
        return requirements_cache[lexicon_id]

    original_selected = [resolution.lexicon_id for resolution in resolutions]
    selected = original_selected[:]

    def _score(assignment: list[int]) -> tuple[int, int, int, int]:
        impossible_count = 0
        unsatisfied_count = 0
        for slot, lexicon_id in enumerate(assignment):
            requirements = _requirements_for(lexicon_id)
            if not requirements:
                continue
            for requirement in requirements:
                satisfied_now = False
                for other_slot, other_lexicon_id in enumerate(assignment):
                    if other_slot == slot:
                        continue
                    plain, labeled = _capabilities_for(other_lexicon_id)
                    if _requirement_is_satisfied(
                        requirement,
                        plain_capabilities=plain,
                        labeled_capabilities=labeled,
                    ):
                        satisfied_now = True
                        break
                if satisfied_now:
                    continue
                unsatisfied_count += 1

                satisfiable_by_candidates = False
                for other_slot, candidate_ids in enumerate(candidate_ids_by_slot):
                    if other_slot == slot:
                        continue
                    for candidate_id in candidate_ids:
                        plain, labeled = _capabilities_for(candidate_id)
                        if _requirement_is_satisfied(
                            requirement,
                            plain_capabilities=plain,
                            labeled_capabilities=labeled,
                        ):
                            satisfiable_by_candidates = True
                            break
                    if satisfiable_by_candidates:
                        break
                if not satisfiable_by_candidates:
                    impossible_count += 1

        change_penalty = sum(
            1 for idx, lexicon_id in enumerate(assignment) if lexicon_id != original_selected[idx]
        )
        rank_penalty = sum(
            candidate_rank_by_slot[idx].get(lexicon_id, len(candidate_ids_by_slot[idx]))
            for idx, lexicon_id in enumerate(assignment)
        )
        return impossible_count, unsatisfied_count, change_penalty, rank_penalty

    improved = True
    max_rounds = max(1, len(candidate_ids_by_slot) * 2)
    rounds = 0
    while improved and rounds < max_rounds:
        improved = False
        rounds += 1
        current_score = _score(selected)
        for slot, candidate_ids in enumerate(candidate_ids_by_slot):
            if len(candidate_ids) <= 1:
                continue
            best_id = selected[slot]
            best_score = current_score
            for candidate_id in candidate_ids:
                if candidate_id == selected[slot]:
                    continue
                trial = selected[:]
                trial[slot] = candidate_id
                score = _score(trial)
                if score < best_score:
                    best_score = score
                    best_id = candidate_id
            if best_id != selected[slot]:
                selected[slot] = best_id
                current_score = best_score
                improved = True

    return selected


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


def _count_ga_feature33_requirements_and_providers(
    *,
    lexicon_ids: list[int],
    lexicon: dict[int, LexiconEntry],
) -> tuple[int, int]:
    demand_count = 0
    provider_count = 0
    for lexicon_id in lexicon_ids:
        entry = lexicon.get(lexicon_id)
        if entry is None:
            continue

        for requirement in _extract_partner_requirements(entry):
            if requirement.feature_code == "33" and requirement.label == "ga":
                demand_count += 1

        _, labeled = _extract_partner_capabilities(entry)
        if "ga" in labeled:
            provider_count += 1
    return demand_count, provider_count


def generate_numeration_from_sentence(
    *,
    grammar_id: str,
    sentence: str,
    legacy_root: Path,
    tokens: list[str] | None = None,
    split_mode: str = "C",
    tokenizer: MorphTokenizer | None = None,
    auto_add_ga_phi: bool = False,
) -> GeneratedNumeration:
    memo = sentence.strip()
    if memo == "":
        raise ValueError("sentence must not be empty")

    lexicon = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=grammar_id)
    grammar_rule_names = {
        row.name for row in load_rule_catalog(grammar_id=grammar_id, legacy_root=legacy_root)
    }
    surface_index = _build_surface_index(lexicon)

    if tokens is None:
        active_tokenizer = tokenizer or SudachiMorphTokenizer(dictionary="core")
        token_values = active_tokenizer.tokenize(sentence, split_mode=split_mode)
    else:
        token_values = tokens

    normalized_tokens: list[str] = []
    for token in token_values:
        normalized = _normalize_token(token)
        if normalized != "":
            normalized_tokens.append(normalized)

    resolutions: list[TokenResolution] = []
    for index, normalized in enumerate(normalized_tokens):
        prev_token = normalized_tokens[index - 1] if index > 0 else None
        next_token = normalized_tokens[index + 1] if index + 1 < len(normalized_tokens) else None
        resolutions.append(
            _resolve_token(
                grammar_id=grammar_id,
                token=normalized,
                surface_index=surface_index,
                lexicon=lexicon,
                grammar_rule_names=grammar_rule_names,
                token_prev=prev_token,
                token_next=next_token,
            )
        )

    if not resolutions:
        raise ValueError("No valid tokens were resolved from input")

    optimized_lexicon_ids = _optimize_partner_friendly_selection(
        resolutions,
        lexicon=lexicon,
    )
    resolutions = [
        TokenResolution(
            token=resolution.token,
            lexicon_id=optimized_lexicon_ids[idx],
            candidate_lexicon_ids=resolution.candidate_lexicon_ids,
            candidate_compatibility=resolution.candidate_compatibility,
        )
        for idx, resolution in enumerate(resolutions)
    ]
    lexicon_ids = optimized_lexicon_ids[:]
    auto_supplements: list[AutoSupplement] = []

    if auto_add_ga_phi and grammar_id == "imi01":
        ga_phi_lexicon_id = 309
        ga_phi_entry = lexicon.get(ga_phi_lexicon_id)
        if ga_phi_entry is not None:
            demand_count, provider_count = _count_ga_feature33_requirements_and_providers(
                lexicon_ids=lexicon_ids,
                lexicon=lexicon,
            )
            deficit = max(0, demand_count - provider_count)
            remaining_slots = max(0, NUMERATION_SLOT_COUNT - len(lexicon_ids))
            add_count = min(deficit, remaining_slots)
            if add_count > 0:
                compatibility = _infer_candidate_compatibility(
                    grammar_id=grammar_id,
                    entry=ga_phi_entry,
                    grammar_rule_names=grammar_rule_names,
                )
                for _ in range(add_count):
                    lexicon_ids.append(ga_phi_lexicon_id)
                    resolutions.append(
                        TokenResolution(
                            token="φ",
                            lexicon_id=ga_phi_lexicon_id,
                            candidate_lexicon_ids=[ga_phi_lexicon_id],
                            candidate_compatibility=[compatibility],
                        )
                    )
                auto_supplements.append(
                    AutoSupplement(
                        kind="ga_feature33_gap_fill",
                        lexicon_id=ga_phi_lexicon_id,
                        entry=ga_phi_entry.entry,
                        count=add_count,
                        reason=(
                            "2,33,ga 要求数が 4,11,ga 供給数を上回るため、"
                            "不足分を φ(309) で補完しました。"
                        ),
                        feature_code="33",
                        label="ga",
                        demand_count=demand_count,
                        provider_count=provider_count,
                    )
                )

    numeration_text = _build_numeration_text(memo=memo, lexicon_ids=lexicon_ids)

    return GeneratedNumeration(
        memo=memo,
        lexicon_ids=lexicon_ids,
        token_resolutions=resolutions,
        numeration_text=numeration_text,
        auto_supplements=auto_supplements,
    )
