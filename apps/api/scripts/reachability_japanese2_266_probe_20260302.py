#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import shutil
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import sys
from typing import Any

API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DOMAIN_SRC = PROJECT_ROOT / "packages" / "domain" / "src"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))
if str(DOMAIN_SRC) not in sys.path:
    sys.path.insert(0, str(DOMAIN_SRC))

from app.api.v1.derivation import (  # noqa: E402
    DerivationReachabilityRequest,
    _search_reachability,
)
from domain.grammar.profiles import get_grammar_profile, resolve_rule_versions  # noqa: E402
from domain.lexicon.legacy_loader import load_legacy_lexicon  # noqa: E402
from domain.lexicon.models import LexiconEntry  # noqa: E402
from domain.numeration.init_builder import build_initial_derivation_state  # noqa: E402
from domain.numeration.parser import NUMERATION_SLOT_COUNT  # noqa: E402

STATUS_CONFIRMED = "確認済み事実"
STATUS_UNCONFIRMED = "未確認"
STATUS_GUESS = "推測"

GRAMMAR_ID = "japanese2"

SENTENCES = {
    "S2": "わたあめを食べているひつじがいる",
    "S3": "ひつじと話しているうさぎがいる",
    "S4": "ふわふわしたわたあめを食べているひつじと話しているうさぎがいる",
    "T1": "わたあめを食べているひつじと話しているうさぎがいる",
    "T2": "ふわふわしたひつじと話しているうさぎがいる",
    "T3": "ふわふわしたわたあめを食べているひつじがいる",
}

BASELINE = {
    "S2": [265, 23, 266, 267, 19, 271, 204],
    "S3": [267, 268, 269, 270, 19, 271, 204],
    "S4": [264, 265, 23, 266, 267, 268, 269, 270, 19, 271, 204],
    "T1": [265, 23, 266, 267, 268, 269, 270, 19, 271, 204],
    "T2": [264, 267, 268, 269, 270, 19, 271, 204],
    "T3": [264, 265, 23, 266, 267, 19, 271, 204],
}

# User-specified probe rows (verbatim TSV lines)
NEW_LEXICON_ROWS = [
    "9201\t食べている\t食べている\tV\t0 \t\t\t\t1\t2,17,N,,,left,head\t\t\t\t\tid\t4 \tTheme\t2,33,wo\tAgent\t2,33,ga\t食べる\tT\tAspect\tprogressive\t\t\t\t\tprobe-266-sy17-left-head\t0",
    "9202\t食べている\t食べている\tV\t0 \t\t\t\t1\t2,17,N,,,right,nonhead\t\t\t\t\tid\t4 \tTheme\t2,33,wo\tAgent\t2,33,ga\t食べる\tT\tAspect\tprogressive\t\t\t\t\tprobe-266-sy17-right-nonhead\t0",
]


@dataclass(frozen=True)
class RunConfig:
    budget_seconds: float = 20.0
    max_nodes: int = 120000
    max_depth: int = 28
    top_k: int = 10


def _normalize_token(token: str) -> str:
    return token.strip().replace("　", "").replace(" ", "")


def _phono_variants(phono: str) -> list[str]:
    out: list[str] = []
    normalized = _normalize_token(phono)
    if normalized:
        out.append(normalized)
    stripped = normalized.strip("-")
    if stripped and stripped != normalized:
        out.append(stripped)
    return out


def _line_map_by_id(path: Path) -> dict[int, str]:
    out: dict[int, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        cols = line.split("\t")
        try:
            lid = int(cols[0].strip())
        except Exception:
            continue
        out[lid] = line
    return out


def _ids_from_new_rows(rows: list[str]) -> set[int]:
    out: set[int] = set()
    for row in rows:
        cols = row.split("\t")
        if not cols:
            continue
        raw = cols[0].strip()
        if raw.isdigit():
            out.add(int(raw))
    return out


def _build_numeration_text(memo: str, lexicon_ids: list[int]) -> str:
    line1 = [memo] + ["" for _ in range(NUMERATION_SLOT_COUNT)]
    line2 = [" "] + ["" for _ in range(NUMERATION_SLOT_COUNT)]
    line3 = [" "] + ["" for _ in range(NUMERATION_SLOT_COUNT)]
    for i, lid in enumerate(lexicon_ids, start=1):
        if i > NUMERATION_SLOT_COUNT:
            break
        line1[i] = str(lid)
        line3[i] = str(i)
    return "\n".join(["\t".join(line1), "\t".join(line2), "\t".join(line3)])


def _replace_one_slot(ids: list[int], old_id: int, new_id: int) -> list[int]:
    out = list(ids)
    done = False
    for i, lid in enumerate(out):
        if lid == old_id:
            out[i] = new_id
            done = True
            break
    if not done:
        raise ValueError(f"old_id={old_id} not found: {ids}")
    return out


def _build_surface_index(lexicon: dict[int, LexiconEntry]) -> dict[str, list[int]]:
    idx: dict[str, list[int]] = defaultdict(list)
    for lid, entry in lexicon.items():
        forms: set[str] = set()
        en = _normalize_token(entry.entry)
        if en:
            forms.add(en)
        for ph in _phono_variants(entry.phono):
            if ph:
                forms.add(ph)
        for f in sorted(forms):
            idx[f].append(lid)
    return dict(idx)


def _source_files_for_id(lid: int, j2_map: dict[int, str], all_map: dict[int, str]) -> list[str]:
    out: list[str] = []
    if lid in j2_map:
        out.append("japanese2/japanese2.csv")
    if lid in all_map:
        out.append("lexicon-all.csv")
    return out


def _make_temp_legacy_root(*, legacy_root: Path, required_ids: set[int], new_rows: list[str]) -> Path:
    tmp_root = Path(tempfile.mkdtemp(prefix="j2_266_probe_"))

    for child in legacy_root.iterdir():
        dst = tmp_root / child.name
        if child.name == "japanese2":
            continue
        try:
            dst.symlink_to(child, target_is_directory=child.is_dir())
        except Exception:
            if child.is_dir():
                shutil.copytree(child, dst)
            else:
                shutil.copy2(child, dst)

    src_j2 = legacy_root / "japanese2"
    dst_j2 = tmp_root / "japanese2"
    dst_j2.mkdir(parents=True, exist_ok=True)
    for child in src_j2.iterdir():
        if child.name == "japanese2.csv":
            continue
        dst = dst_j2 / child.name
        try:
            dst.symlink_to(child, target_is_directory=child.is_dir())
        except Exception:
            if child.is_dir():
                shutil.copytree(child, dst)
            else:
                shutil.copy2(child, dst)

    j2_map = _line_map_by_id(legacy_root / "japanese2" / "japanese2.csv")
    all_map = _line_map_by_id(legacy_root / "lexicon-all.csv")

    out_lines: list[str] = []
    for lid in sorted(required_ids):
        if lid in j2_map:
            out_lines.append(j2_map[lid])
        elif lid in all_map:
            out_lines.append(all_map[lid])

    out_lines.extend(new_rows)
    (dst_j2 / "japanese2.csv").write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return tmp_root


def _aggregate_residual_families(samples: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for sample in samples:
        for key, value in (sample.get("residual_family_counts") or {}).items():
            counter[key] += int(value)
    return dict(sorted(counter.items(), key=lambda row: (-row[1], row[0])))


def _build_initial_item_map(*, state: Any, lexicon_ids: list[int], lexicon: dict[int, LexiconEntry]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for slot_index in range(1, state.basenum + 1):
        item = state.base[slot_index]
        if item == "zero" or not isinstance(item, list):
            continue
        item_id = str(item[0]) if len(item) > 0 else ""
        lid = lexicon_ids[slot_index - 1] if slot_index - 1 < len(lexicon_ids) else None
        entry = lexicon.get(lid) if lid is not None else None
        mapping[item_id] = {
            "initial_slot": slot_index,
            "lexicon_id": lid,
            "surface": entry.entry if entry is not None else "",
            "phono": entry.phono if entry is not None else "",
            "category": entry.category if entry is not None else "",
        }
    return mapping


def _flatten_exact_sources_top(
    *,
    samples: list[dict[str, Any]],
    initial_item_map: dict[str, dict[str, Any]],
    top_n: int = 5,
) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    attrs: dict[str, dict[str, Any]] = {}
    for sample in samples[:5]:
        for family, rows in (sample.get("residual_family_sources") or {}).items():
            for row in rows:
                item_id = str(row.get("item_id", ""))
                init = initial_item_map.get(item_id, {})
                key = "|".join(
                    [
                        family,
                        str(row.get("raw", "")),
                        item_id,
                        str(init.get("initial_slot", "")),
                        str(init.get("surface", "")),
                    ]
                )
                counter[key] += 1
                attrs[key] = {
                    "family": family,
                    "exact_label": str(row.get("raw", "")),
                    "item_id": item_id,
                    "surface": str(init.get("surface", row.get("phono", ""))),
                    "initial_slot": init.get("initial_slot"),
                    "current_slot": str(row.get("slot_index", "")),
                    "lexicon_id": init.get("lexicon_id"),
                }
    out: list[dict[str, Any]] = []
    for key, count in counter.most_common(top_n):
        row = dict(attrs[key])
        row["count_in_top5_samples"] = int(count)
        out.append(row)
    return out


def _source_set(rows: list[dict[str, Any]]) -> set[str]:
    out: set[str] = set()
    for row in rows:
        out.add(
            f"{row.get('family','')}|{row.get('exact_label','')}|{row.get('item_id','')}|{row.get('surface','')}"
        )
    return out


def _diff_run(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    b = before["metrics"]
    a = after["metrics"]
    keys = sorted(set(b["best_leaf_residual_family_totals"].keys()) | set(a["best_leaf_residual_family_totals"].keys()))
    fam_delta = {
        k: int(a["best_leaf_residual_family_totals"].get(k, 0)) - int(b["best_leaf_residual_family_totals"].get(k, 0))
        for k in keys
    }
    return {
        "best_leaf_unresolved_min_before": b["best_leaf_unresolved_min"],
        "best_leaf_unresolved_min_after": a["best_leaf_unresolved_min"],
        "best_leaf_unresolved_min_delta": (
            int(a["best_leaf_unresolved_min"]) - int(b["best_leaf_unresolved_min"])
            if isinstance(a["best_leaf_unresolved_min"], int) and isinstance(b["best_leaf_unresolved_min"], int)
            else None
        ),
        "family_delta": fam_delta,
        "source_disappeared_top5": sorted(_source_set(b["best_leaf_exact_source_top5"]) - _source_set(a["best_leaf_exact_source_top5"])),
        "source_appeared_top5": sorted(_source_set(a["best_leaf_exact_source_top5"]) - _source_set(b["best_leaf_exact_source_top5"])),
        "fact_status": STATUS_CONFIRMED,
    }


def _run_case(
    *,
    legacy_root: Path,
    sentence_key: str,
    sentence: str,
    proposal_id: str,
    lexicon_ids: list[int],
    config: RunConfig,
) -> dict[str, Any]:
    numeration_text = _build_numeration_text(f"{sentence_key}:{proposal_id}", lexicon_ids)
    state = build_initial_derivation_state(
        grammar_id=GRAMMAR_ID,
        numeration_text=numeration_text,
        legacy_root=legacy_root,
    )
    lexicon = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=GRAMMAR_ID)
    initial_item_map = _build_initial_item_map(state=state, lexicon_ids=lexicon_ids, lexicon=lexicon)

    profile = resolve_rule_versions(profile=get_grammar_profile(GRAMMAR_ID), legacy_root=legacy_root)
    req = DerivationReachabilityRequest(
        state=state,
        max_evidences=20,
        budget_seconds=config.budget_seconds,
        max_nodes=config.max_nodes,
        max_depth=config.max_depth,
        return_process_text=False,
    )
    internal = _search_reachability(
        request=req,
        legacy_root=legacy_root,
        rh_version=profile.rh_merge_version,
        lh_version=profile.lh_merge_version,
        search_signature_mode="structural",
    )

    best_leaf_samples = (internal.leaf_stats.get("best_samples") or [])[: config.top_k]
    best_mid_samples = (internal.leaf_stats.get("best_mid_state_samples") or [])[: config.top_k]
    history_top: list[str] = []
    for ev in internal.evidences[:3]:
        history_top.append(" ".join(f"([{s.left_id} {s.right_id}] {s.rule_name})" for s in ev.steps))

    return {
        "sentence_key": sentence_key,
        "sentence": sentence,
        "proposal_id": proposal_id,
        "explicit_lexicon_ids": list(lexicon_ids),
        "metrics": {
            "status": internal.status,
            "reason": internal.reason,
            "actions_attempted": internal.actions_attempted,
            "max_depth_reached": internal.max_depth_reached,
            "best_leaf_unresolved_min": internal.leaf_stats.get("unresolved_min"),
            "best_leaf_residual_family_totals": _aggregate_residual_families(best_leaf_samples),
            "best_mid_residual_family_totals": _aggregate_residual_families(best_mid_samples),
            "best_leaf_exact_source_top5": _flatten_exact_sources_top(
                samples=best_leaf_samples,
                initial_item_map=initial_item_map,
                top_n=5,
            ),
            "history_top": history_top,
            "fact_status": STATUS_CONFIRMED,
        },
    }


def _engine_usable_check(*, temp_root: Path, lid: int) -> dict[str, Any]:
    ids = [lid]
    if lid != 204:
        ids.append(204)
    else:
        ids.append(19)
    try:
        state = build_initial_derivation_state(
            grammar_id=GRAMMAR_ID,
            numeration_text=_build_numeration_text(f"engine_check:{lid}", ids),
            legacy_root=temp_root,
        )
        profile = resolve_rule_versions(profile=get_grammar_profile(GRAMMAR_ID), legacy_root=temp_root)
        req = DerivationReachabilityRequest(
            state=state,
            max_evidences=1,
            budget_seconds=0.1,
            max_nodes=200,
            max_depth=6,
            return_process_text=False,
        )
        _search_reachability(
            request=req,
            legacy_root=temp_root,
            rh_version=profile.rh_merge_version,
            lh_version=profile.lh_merge_version,
            search_signature_mode="structural",
        )
        return {"engine_usable": True, "error": None, "fact_status": STATUS_CONFIRMED}
    except Exception as exc:
        return {"engine_usable": False, "error": str(exc), "fact_status": STATUS_CONFIRMED}


def _build_candidate_pool(
    *,
    legacy_root: Path,
    temp_root: Path,
    surfaces: list[str],
) -> dict[str, list[dict[str, Any]]]:
    all_lex = load_legacy_lexicon(legacy_root=legacy_root, grammar_id="imi01")
    j2_lex = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=GRAMMAR_ID)
    temp_j2_lex = load_legacy_lexicon(legacy_root=temp_root, grammar_id=GRAMMAR_ID)
    all_idx = _build_surface_index(all_lex)
    j2_idx = _build_surface_index(j2_lex)
    temp_idx = _build_surface_index(temp_j2_lex)
    j2_map = _line_map_by_id(legacy_root / "japanese2" / "japanese2.csv")
    all_map = _line_map_by_id(legacy_root / "lexicon-all.csv")

    out: dict[str, list[dict[str, Any]]] = {}
    for surface in surfaces:
        key = _normalize_token(surface)
        ids = sorted(set(all_idx.get(key, [])) | set(j2_idx.get(key, [])) | set(temp_idx.get(key, [])))
        rows: list[dict[str, Any]] = []
        for lid in ids:
            entry = temp_j2_lex.get(lid)
            if entry is None:
                continue
            chk = _engine_usable_check(temp_root=temp_root, lid=lid)
            rows.append(
                {
                    "lexicon_id": lid,
                    "entry": entry.entry,
                    "surface": surface,
                    "category": entry.category,
                    "idslot": entry.idslot,
                    "sync_features": list(entry.sync_features),
                    "semantics": list(entry.semantics),
                    "engine_usable": chk["engine_usable"],
                    "lookup_deployable": lid in set(j2_idx.get(key, [])),
                    "source_files": _source_files_for_id(lid, j2_map=j2_map, all_map=all_map),
                    "engine_check_error": chk["error"],
                    "fact_status": STATUS_CONFIRMED,
                }
            )
        out[surface] = rows
    return out


def _markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# japanese2 lexical-only probe 266 ({payload['generated_at']})")
    lines.append("")
    lines.append("## 1. 結論")
    lines.append("")
    lines.append(
        f"- [確認済み事実] 固定条件: grammar_id={payload['config']['grammar_id']}, explicit numeration, auto_add_ga_phi={payload['config']['auto_add_ga_phi']}, "
        f"budget_seconds={payload['config']['budget_seconds']}, max_nodes={payload['config']['max_nodes']}, max_depth={payload['config']['max_depth']}, top_k={payload['config']['top_k']}"
    )
    lines.append(
        f"- [確認済み事実] S2 266差し替え: 9201 delta={payload['yes_no']['q1']['S2_9201_delta']}, 9202 delta={payload['yes_no']['q1']['S2_9202_delta']}"
    )
    lines.append(
        f"- [確認済み事実] T3 266差し替え: 9201 delta={payload['yes_no']['q2']['T3_9201_delta']}, 9202 delta={payload['yes_no']['q2']['T3_9202_delta']}"
    )
    lines.append(
        f"- [確認済み事実] S4 266+171 併用: 9201+171 delta={payload['yes_no']['q3']['S4_9201_171_delta']}, 9202+171 delta={payload['yes_no']['q3']['S4_9202_171_delta']}"
    )
    lines.append("")

    lines.append("## 2. 266 新規 lexical item probe")
    lines.append("")
    for sk in ("S2", "T3", "T1", "S4"):
        lines.append(f"### {sk}: {payload['sentences'][sk]}")
        base = payload["runs"][sk]["baseline"]
        lines.append(f"- [確認済み事実] baseline IDs: `{','.join(str(x) for x in base['explicit_lexicon_ids'])}`")
        lines.append(f"- [確認済み事実] baseline metrics: {base['metrics']}")
        for pid in ("probe_9201", "probe_9202"):
            row = payload["runs"][sk][pid]
            lines.append(f"- [確認済み事実] {pid} IDs: `{','.join(str(x) for x in row['explicit_lexicon_ids'])}`")
            lines.append(f"- [確認済み事実] {pid} metrics: {row['metrics']}")
            lines.append(f"- [確認済み事実] {pid} diff: {payload['diff'][sk][pid]}")
        lines.append("")

    lines.append("## 3. T1/T3/S4 の 266-only 比較")
    lines.append("")
    for sk in ("T1", "T3", "S4"):
        lines.append(f"- [確認済み事実] {sk} probe_9201 diff: {payload['diff'][sk]['probe_9201']}")
        lines.append(f"- [確認済み事実] {sk} probe_9202 diff: {payload['diff'][sk]['probe_9202']}")
    lines.append("")

    lines.append("## 4. 171 併用比較")
    lines.append("")
    for sk in ("T1", "S4"):
        for pid in ("probe_9201_171", "probe_9202_171"):
            row = payload["runs"][sk][pid]
            lines.append(f"- [確認済み事実] {sk} {pid} IDs: `{','.join(str(x) for x in row['explicit_lexicon_ids'])}`")
            lines.append(f"- [確認済み事実] {sk} {pid} metrics: {row['metrics']}")
            lines.append(f"- [確認済み事実] {sk} {pid} diff: {payload['diff'][sk][pid]}")
    lines.append("")

    lines.append("## 5. 264 candidate pool")
    lines.append("")
    rows = payload["candidate_pool"]["ふわふわした"]
    if not rows:
        lines.append("- [確認済み事実] ふわふわした 候補なし")
    else:
        lines.append("| lexicon_id | entry | category | idslot | engine_usable | lookup_deployable | source_files |")
        lines.append("|---:|---|---|---|---|---|---|")
        for r in rows:
            lines.append(
                f"| {r['lexicon_id']} | {r['entry']} | {r['category']} | {r['idslot']} | {r['engine_usable']} | {r['lookup_deployable']} | {','.join(r['source_files'])} |"
            )
    lines.append("")
    if payload["probe_264_alternatives"]:
        for row in payload["probe_264_alternatives"]:
            lines.append(f"- [確認済み事実] 264 alternative run: {row}")
    else:
        lines.append("- [確認済み事実] 264 同表層 engine-usable 代替候補は存在しないため、1スロット差し替えは not_run。")
    lines.append("")

    lines.append("## 6. yes/no")
    lines.append("")
    lines.append(f"- [確認済み事実] Q1: {payload['yes_no']['q1']['answer']} ({payload['yes_no']['q1']['basis']})")
    lines.append(f"- [確認済み事実] Q2: {payload['yes_no']['q2']['answer']} ({payload['yes_no']['q2']['basis']})")
    lines.append(f"- [確認済み事実] Q3: {payload['yes_no']['q3']['answer']} ({payload['yes_no']['q3']['basis']})")
    lines.append("")

    lines.append("## 7. 未確認事項")
    lines.append("")
    lines.append("- [未確認] 有限予算観測のため、unknown を unreachable と断定できない。")
    lines.append("- [未確認] tree/process は現行抽出で本レポートに未掲載（history と residual source を代替記録）。")
    return "\n".join(lines) + "\n"


def main() -> None:
    legacy_root = PROJECT_ROOT.parent
    config = RunConfig()

    # Required IDs
    required_ids: set[int] = set()
    for ids in BASELINE.values():
        required_ids.update(ids)
    required_ids.update({171})
    required_ids.update(_ids_from_new_rows(NEW_LEXICON_ROWS))

    # Add candidate IDs for target surfaces
    target_surfaces = ["ふわふわした", "食べている", "と", "話している", "いる", "る", "φ"]

    def harvest_ids(path: Path, surfaces: list[str]) -> set[int]:
        out: set[int] = set()
        with path.open(encoding="utf-8") as f:
            r = csv.reader(f, delimiter="\t")
            for row in r:
                if not row:
                    continue
                try:
                    lid = int((row[0] if len(row) > 0 else "").strip())
                except Exception:
                    continue
                entry = _normalize_token(row[1] if len(row) > 1 else "")
                phono = _normalize_token(row[2] if len(row) > 2 else "")
                for s in surfaces:
                    ss = _normalize_token(s)
                    if entry == ss or phono == ss or phono.strip("-") == ss:
                        out.add(lid)
                        break
        return out

    required_ids.update(harvest_ids(legacy_root / "lexicon-all.csv", target_surfaces))
    required_ids.update(harvest_ids(legacy_root / "japanese2" / "japanese2.csv", target_surfaces))

    temp_root = _make_temp_legacy_root(
        legacy_root=legacy_root,
        required_ids=required_ids,
        new_rows=NEW_LEXICON_ROWS,
    )

    candidate_pool = _build_candidate_pool(
        legacy_root=legacy_root,
        temp_root=temp_root,
        surfaces=target_surfaces,
    )

    runs: dict[str, dict[str, Any]] = {}
    diffs: dict[str, dict[str, Any]] = {}

    for sk in ("S2", "S3", "S4", "T1", "T2", "T3"):
        sentence = SENTENCES[sk]
        base = _run_case(
            legacy_root=temp_root,
            sentence_key=sk,
            sentence=sentence,
            proposal_id="baseline",
            lexicon_ids=BASELINE[sk],
            config=config,
        )
        runs[sk] = {"baseline": base}
        diffs[sk] = {}

        # 266-only probes where 266 exists
        if 266 in BASELINE[sk]:
            p9201_ids = _replace_one_slot(BASELINE[sk], 266, 9201)
            p9202_ids = _replace_one_slot(BASELINE[sk], 266, 9202)
            p9201 = _run_case(
                legacy_root=temp_root,
                sentence_key=sk,
                sentence=sentence,
                proposal_id="probe_9201",
                lexicon_ids=p9201_ids,
                config=config,
            )
            p9202 = _run_case(
                legacy_root=temp_root,
                sentence_key=sk,
                sentence=sentence,
                proposal_id="probe_9202",
                lexicon_ids=p9202_ids,
                config=config,
            )
            runs[sk]["probe_9201"] = p9201
            runs[sk]["probe_9202"] = p9202
            diffs[sk]["probe_9201"] = _diff_run(base, p9201)
            diffs[sk]["probe_9202"] = _diff_run(base, p9202)

            # 171 combination where 268 exists (after 266 probe)
            if 268 in BASELINE[sk]:
                p9201_171_ids = _replace_one_slot(p9201_ids, 268, 171)
                p9202_171_ids = _replace_one_slot(p9202_ids, 268, 171)
                p9201_171 = _run_case(
                    legacy_root=temp_root,
                    sentence_key=sk,
                    sentence=sentence,
                    proposal_id="probe_9201_171",
                    lexicon_ids=p9201_171_ids,
                    config=config,
                )
                p9202_171 = _run_case(
                    legacy_root=temp_root,
                    sentence_key=sk,
                    sentence=sentence,
                    proposal_id="probe_9202_171",
                    lexicon_ids=p9202_171_ids,
                    config=config,
                )
                runs[sk]["probe_9201_171"] = p9201_171
                runs[sk]["probe_9202_171"] = p9202_171
                diffs[sk]["probe_9201_171"] = _diff_run(base, p9201_171)
                diffs[sk]["probe_9202_171"] = _diff_run(base, p9202_171)

    # 264 alternatives (if exist)
    probe_264_alternatives: list[dict[str, Any]] = []
    c264 = [r for r in candidate_pool["ふわふわした"] if bool(r["engine_usable"]) and int(r["lexicon_id"]) != 264]
    for cand in c264:
        cand_id = int(cand["lexicon_id"])
        for sk in ("T2", "T3", "S4"):
            if 264 not in BASELINE[sk]:
                continue
            ids = _replace_one_slot(BASELINE[sk], 264, cand_id)
            if ids == BASELINE[sk]:
                continue
            run = _run_case(
                legacy_root=temp_root,
                sentence_key=sk,
                sentence=SENTENCES[sk],
                proposal_id=f"probe_264_to_{cand_id}",
                lexicon_ids=ids,
                config=config,
            )
            probe_264_alternatives.append(
                {
                    "sentence_key": sk,
                    "new_id": cand_id,
                    "explicit_lexicon_ids": ids,
                    "metrics": run["metrics"],
                    "diff": _diff_run(runs[sk]["baseline"], run),
                    "fact_status": STATUS_CONFIRMED,
                }
            )

    # yes/no (within current experiment scope)
    q1_s2_9201 = diffs["S2"]["probe_9201"]["best_leaf_unresolved_min_delta"] if "probe_9201" in diffs["S2"] else None
    q1_s2_9202 = diffs["S2"]["probe_9202"]["best_leaf_unresolved_min_delta"] if "probe_9202" in diffs["S2"] else None
    q2_t3_9201 = diffs["T3"]["probe_9201"]["best_leaf_unresolved_min_delta"] if "probe_9201" in diffs["T3"] else None
    q2_t3_9202 = diffs["T3"]["probe_9202"]["best_leaf_unresolved_min_delta"] if "probe_9202" in diffs["T3"] else None
    q3_s4_9201_171 = diffs["S4"]["probe_9201_171"]["best_leaf_unresolved_min_delta"] if "probe_9201_171" in diffs["S4"] else None
    q3_s4_9202_171 = diffs["S4"]["probe_9202_171"]["best_leaf_unresolved_min_delta"] if "probe_9202_171" in diffs["S4"] else None

    yes_no = {
        "q1": {
            "question": "266の新規1行でS2 leaf_min 1->0 になるか",
            "answer": "yes" if (q1_s2_9201 == -1 or q1_s2_9202 == -1) else "no",
            "basis": "S2 baseline vs probe_9201/probe_9202 の leaf_min 差分",
            "S2_9201_delta": q1_s2_9201,
            "S2_9202_delta": q1_s2_9202,
            "fact_status": STATUS_CONFIRMED,
        },
        "q2": {
            "question": "266新規1行でT3(264+266パケット)を縮めるか",
            "answer": "yes" if ((q2_t3_9201 is not None and q2_t3_9201 < 0) or (q2_t3_9202 is not None and q2_t3_9202 < 0)) else "no",
            "basis": "T3 baseline vs probe_9201/probe_9202 の leaf_min 差分",
            "T3_9201_delta": q2_t3_9201,
            "T3_9202_delta": q2_t3_9202,
            "fact_status": STATUS_CONFIRMED,
        },
        "q3": {
            "question": "266修正+171併用でS4改善するか",
            "answer": "yes" if ((q3_s4_9201_171 is not None and q3_s4_9201_171 < 0) or (q3_s4_9202_171 is not None and q3_s4_9202_171 < 0)) else "no",
            "basis": "S4 baseline vs probe_9201_171/probe_9202_171 の leaf_min 差分 + source差分",
            "S4_9201_171_delta": q3_s4_9201_171,
            "S4_9202_171_delta": q3_s4_9202_171,
            "fact_status": STATUS_CONFIRMED,
        },
    }

    payload = {
        "generated_at": date.today().isoformat(),
        "config": {
            "grammar_id": GRAMMAR_ID,
            "auto_add_ga_phi": False,
            "budget_seconds": config.budget_seconds,
            "max_nodes": config.max_nodes,
            "max_depth": config.max_depth,
            "top_k": config.top_k,
            "fact_status": STATUS_CONFIRMED,
        },
        "sentences": SENTENCES,
        "baseline": BASELINE,
        "new_lexicon_rows": NEW_LEXICON_ROWS,
        "candidate_pool": candidate_pool,
        "runs": runs,
        "diff": diffs,
        "probe_264_alternatives": probe_264_alternatives,
        "yes_no": yes_no,
        "code_refs": {
            "se_24": "packages/domain/src/domain/derivation/execute.py#L373-L374",
            "se_33": "packages/domain/src/domain/derivation/execute.py#L395-L409",
            "sy_17": "packages/domain/src/domain/derivation/execute.py#L800-L820",
            "eval_17": "packages/domain/src/domain/derivation/execute.py#L69-L97",
            "fact_status": STATUS_CONFIRMED,
        },
        "temp_legacy_root": str(temp_root),
    }

    out_json = PROJECT_ROOT / "docs/specs/reachability-japanese2-266-probe-20260302.json"
    out_md = PROJECT_ROOT / "docs/specs/reachability-japanese2-266-probe-20260302.md"
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(_markdown(payload), encoding="utf-8")
    print(f"Wrote JSON: {out_json}")
    print(f"Wrote Markdown: {out_md}")


if __name__ == "__main__":
    main()
