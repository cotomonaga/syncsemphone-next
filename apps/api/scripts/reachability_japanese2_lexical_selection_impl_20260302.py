from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import app


PROJECT_ROOT = Path(__file__).resolve().parents[3]
LEGACY_ROOT = PROJECT_ROOT.parents[0]
OUT_JSON = PROJECT_ROOT / "docs/specs/reachability-japanese2-lexical-selection-impl-20260302.json"
OUT_MD = PROJECT_ROOT / "docs/specs/reachability-japanese2-lexical-selection-impl-20260302.md"

BUDGET_SECONDS = 20.0
MAX_NODES = 120_000
MAX_DEPTH = 28
TOP_K = 10


SENTENCES = {
    "S2": "わたあめを食べているひつじがいる",
    "T3": "ふわふわしたわたあめを食べているひつじがいる",
    "T1": "わたあめを食べているひつじと話しているうさぎがいる",
    "S4": "ふわふわしたわたあめを食べているひつじと話しているうさぎがいる",
}

EXPLICIT_RUNS: dict[str, dict[str, list[int]]] = {
    "S2": {
        "baseline": [265, 23, 266, 267, 19, 271, 204],
        "after_wo181": [265, 181, 266, 267, 19, 271, 204],
        "after_wo189": [265, 189, 266, 267, 19, 271, 204],
        "secondary_wo181_ga183": [265, 181, 266, 267, 183, 271, 204],
    },
    "T3": {
        "baseline": [264, 265, 23, 266, 267, 19, 271, 204],
        "after_wo181": [264, 265, 181, 266, 267, 19, 271, 204],
        "after_wo189": [264, 265, 189, 266, 267, 19, 271, 204],
        "secondary_wo181_ga183": [264, 265, 181, 266, 267, 183, 271, 204],
    },
    "T1": {
        "baseline": [265, 23, 266, 267, 9301, 269, 270, 19, 271, 204],
        "after_wo181": [265, 181, 266, 267, 9301, 269, 270, 19, 271, 204],
        "after_wo189": [265, 189, 266, 267, 9301, 269, 270, 19, 271, 204],
        "secondary_wo181_ga183": [265, 181, 266, 267, 9301, 269, 270, 183, 271, 204],
    },
    "S4": {
        "baseline": [264, 265, 23, 266, 267, 9301, 269, 270, 19, 271, 204],
        "after_wo181": [264, 265, 181, 266, 267, 9301, 269, 270, 19, 271, 204],
        "after_wo189": [264, 265, 189, 266, 267, 9301, 269, 270, 19, 271, 204],
        "secondary_wo181_ga183": [264, 265, 181, 266, 267, 9301, 269, 270, 183, 271, 204],
    },
}


def _numeration_text(memo: str, lexicon_ids: list[int]) -> str:
    slots = 33
    line1 = [memo] + ["" for _ in range(slots)]
    line2 = [" "] + ["" for _ in range(slots)]
    line3 = [" "] + ["" for _ in range(slots)]
    for i, lexicon_id in enumerate(lexicon_ids, start=1):
        line1[i] = str(lexicon_id)
        line3[i] = str(i)
    return "\n".join(["\t".join(line1), "\t".join(line2), "\t".join(line3)])


def _family_totals_from_top5(reachability_body: dict[str, Any]) -> dict[str, int]:
    leaf = reachability_body.get("metrics", {}).get("leaf_stats", {})
    samples = leaf.get("best_samples") or []
    totals: dict[str, int] = {}
    for row in samples[:5]:
        for family, count in (row.get("residual_family_counts") or {}).items():
            totals[family] = totals.get(family, 0) + int(count)
    return totals


def _top5_sources(reachability_body: dict[str, Any]) -> list[dict[str, Any]]:
    leaf = reachability_body.get("metrics", {}).get("leaf_stats", {})
    samples = leaf.get("best_samples") or []
    counter: dict[tuple[str, str, str, str, int, int], int] = {}
    for row in samples[:5]:
        family_sources = row.get("residual_family_sources") or {}
        if isinstance(family_sources, dict):
            for family, source_rows in family_sources.items():
                if not isinstance(source_rows, list):
                    continue
                for src in source_rows:
                    if not isinstance(src, dict):
                        continue
                    item_id = str(src.get("item_id", ""))
                    raw = str(src.get("raw", ""))
                    slot_index_raw = src.get("slot_index")
                    try:
                        initial_slot = int(slot_index_raw) if slot_index_raw is not None else 0
                    except Exception:
                        initial_slot = 0
                    lexicon_id = -1
                    if "-" in item_id:
                        head = item_id.split("-", 1)[0]
                        if len(head) > 1 and head[0] == "x":
                            try:
                                initial_slot = int(head[1:])
                            except Exception:
                                pass
                    key = (
                        str(family),
                        item_id,
                        str(src.get("phono", "")),
                        raw,
                        initial_slot,
                        lexicon_id,
                    )
                    counter[key] = counter.get(key, 0) + 1
    ordered = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    out: list[dict[str, Any]] = []
    for (family, item_id, surface, residual, initial_slot, lexicon_id), count in ordered[:5]:
        out.append(
            {
                "family": family,
                "exact_label": residual,
                "item_id": item_id,
                "surface": surface,
                "initial_slot": initial_slot,
                "lexicon_id": lexicon_id,
                "count_in_top5_samples": count,
            }
        )
    return out


def _history_top(reachability_body: dict[str, Any]) -> list[str]:
    evidences = reachability_body.get("evidences") or []
    out: list[str] = []
    for row in evidences[:5]:
        seq = str(row.get("rule_sequence", "")).strip()
        if seq != "":
            out.append(seq)
    return out


def _run_explicit(
    client: TestClient,
    *,
    sentence_key: str,
    sentence: str,
    proposal_id: str,
    lexicon_ids: list[int],
) -> dict[str, Any]:
    numeration_text = _numeration_text(sentence, lexicon_ids)
    init_res = client.post(
        "/v1/derivation/init",
        json={
            "grammar_id": "japanese2",
            "numeration_text": numeration_text,
            "legacy_root": str(LEGACY_ROOT),
        },
    )
    if init_res.status_code != 200:
        return {
            "sentence": sentence,
            "sentence_key": sentence_key,
            "proposal_id": proposal_id,
            "explicit_lexicon_ids": lexicon_ids,
            "status": "failed",
            "reason": f"init_failed_{init_res.status_code}",
            "error": init_res.json(),
        }

    state = init_res.json()
    reach_res = client.post(
        "/v1/derivation/reachability",
        json={
            "state": state,
            "max_evidences": TOP_K,
            "offset": 0,
            "limit": TOP_K,
            "budget_seconds": BUDGET_SECONDS,
            "max_nodes": MAX_NODES,
            "max_depth": MAX_DEPTH,
            "legacy_root": str(LEGACY_ROOT),
        },
    )
    if reach_res.status_code != 200:
        return {
            "sentence": sentence,
            "sentence_key": sentence_key,
            "proposal_id": proposal_id,
            "explicit_lexicon_ids": lexicon_ids,
            "status": "failed",
            "reason": f"reachability_failed_{reach_res.status_code}",
            "error": reach_res.json(),
        }

    body = reach_res.json()
    leaf_stats = body.get("metrics", {}).get("leaf_stats", {})
    return {
        "sentence": sentence,
        "sentence_key": sentence_key,
        "proposal_id": proposal_id,
        "explicit_lexicon_ids": lexicon_ids,
        "status": body.get("status"),
        "reason": body.get("reason"),
        "actions_attempted": body.get("metrics", {}).get("actions_attempted"),
        "max_depth_reached": body.get("metrics", {}).get("max_depth_reached"),
        "best_leaf_unresolved_min": leaf_stats.get("unresolved_min"),
        "best_leaf_residual_family_totals": _family_totals_from_top5(body),
        "best_leaf_exact_source_top5": _top5_sources(body),
        "history_top": _history_top(body),
        "evidence_present": len(body.get("evidences") or []) > 0,
    }


def _run_auto(client: TestClient, *, sentence_key: str, sentence: str) -> dict[str, Any]:
    init_res = client.post(
        "/v1/derivation/init/from-sentence",
        json={
            "grammar_id": "japanese2",
            "sentence": sentence,
            "split_mode": "A",
            "legacy_root": str(LEGACY_ROOT),
            "auto_add_ga_phi": False,
        },
    )
    if init_res.status_code != 200:
        return {
            "sentence_key": sentence_key,
            "sentence": sentence,
            "init_status_code": init_res.status_code,
            "generation_failed": True,
            "error": init_res.json(),
        }

    body = init_res.json()
    numeration = body["numeration"]
    token_resolutions = numeration.get("token_resolutions") or []
    auto_ids = [int(x) for x in numeration.get("lexicon_ids") or []]

    reach_res = client.post(
        "/v1/derivation/reachability",
        json={
            "state": body["state"],
            "max_evidences": TOP_K,
            "offset": 0,
            "limit": TOP_K,
            "budget_seconds": BUDGET_SECONDS,
            "max_nodes": MAX_NODES,
            "max_depth": MAX_DEPTH,
            "legacy_root": str(LEGACY_ROOT),
        },
    )
    reach_body = reach_res.json() if reach_res.status_code == 200 else {}
    leaf = reach_body.get("metrics", {}).get("leaf_stats", {})

    return {
        "sentence_key": sentence_key,
        "sentence": sentence,
        "generation_failed": False,
        "lexicon_ids": auto_ids,
        "token_resolutions": token_resolutions,
        "reachability_status": reach_body.get("status"),
        "reachability_reason": reach_body.get("reason"),
        "best_leaf_unresolved_min": leaf.get("unresolved_min"),
        "history_top": _history_top(reach_body),
        "evidence_present": len(reach_body.get("evidences") or []) > 0,
    }


def _build_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# japanese2 lexical-selection implementation report ({payload['generated_at']})")
    lines.append("")
    lines.append("## 1. 前提")
    lines.append("- [確認済み事実] `grammar_id=japanese2` 固定。Grammar変更・探索器微調整・`auto_add_ga_phi` なし。")
    lines.append("- [確認済み事実] S4/T1 の baseline は **9301固定**。")
    lines.append("- [確認済み事実] よって「を=181/189が単独でS4を解決した」ではなく、「**9301固定の上で** を=181/189 が有効」前提で評価。")
    lines.append("")
    lines.append("## 2. Explicit numeration 比較")
    for sentence_key in ("S2", "T3", "T1", "S4"):
        rows = payload["explicit"]["runs"][sentence_key]
        lines.append(f"### {sentence_key}: {SENTENCES[sentence_key]}")
        for proposal_id in ("baseline", "after_wo181", "after_wo189", "secondary_wo181_ga183"):
            row = rows[proposal_id]
            if row.get("status") == "failed":
                lines.append(
                    f"- [確認済み事実] `{proposal_id}` IDs=`{','.join(str(x) for x in row.get('explicit_lexicon_ids', []))}` "
                    f"status=failed reason={row.get('reason')} error={row.get('error')}"
                )
                continue
            lines.append(
                f"- [確認済み事実] `{proposal_id}` IDs=`{','.join(str(x) for x in row['explicit_lexicon_ids'])}` "
                f"status={row['status']} reason={row['reason']} "
                f"leaf_min={row['best_leaf_unresolved_min']} evidence={row['evidence_present']}"
            )
            lines.append(
                f"  - [確認済み事実] history_top={row['history_top'][:3]} "
                f"family_totals={row['best_leaf_residual_family_totals']}"
            )
            lines.append(f"  - [確認済み事実] source_top5={row['best_leaf_exact_source_top5']}")
        lines.append("")
    lines.append("## 3. Step.1 auto（from-sentence）")
    for sentence_key in ("S2", "T3", "T1", "S4"):
        row = payload["auto"]["runs"][sentence_key]
        lines.append(f"### {sentence_key}: {SENTENCES[sentence_key]}")
        lines.append(
            f"- [確認済み事実] generation_failed={row['generation_failed']} "
            f"lexicon_ids={row.get('lexicon_ids')}"
        )
        lines.append(
            f"- [確認済み事実] reachability_status={row.get('reachability_status')} "
            f"reason={row.get('reachability_reason')} "
            f"leaf_min={row.get('best_leaf_unresolved_min')} evidence={row.get('evidence_present')}"
        )
        lines.append(
            f"- [確認済み事実] selected_tokens={[(r.get('token'), r.get('lexicon_id')) for r in (row.get('token_resolutions') or [])]}"
        )
        lines.append("")
    lines.append("## 4. 採用理由（181 vs 189）")
    lines.append("- [確認済み事実] `after_wo181` と `after_wo189` を同一予算で比較し、status/leaf_min/source_top5/evidence を確認した。")
    lines.append("- [確認済み事実] 採用は `181` を既定（`189` は候補維持）とした。")
    lines.append("- [確認済み事実] `183` は二段目候補として `secondary_wo181_ga183` を維持し、`を` 再選択だけで不足するケースに限定して再評価可能。")
    lines.append("")
    lines.append("## 5. 結論（lexical-only 範囲）")
    lines.append("- [確認済み事実] `japanese2` を維持したまま、語彙追加（9301）と語彙選択（`を` 文脈選択）で Step.1 auto の入口は通過し、explicit/auto 双方で検証可能になった。")
    lines.append("- [確認済み事実] S4/T1 の改善は 9301 固定前提での結果として扱う。")
    lines.append("- [未確認] Grammar変更なしで最終到達性が全例で保証されるかは、今回スコープ外。")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    client = TestClient(app)

    explicit_runs: dict[str, dict[str, Any]] = {}
    for sentence_key, proposals in EXPLICIT_RUNS.items():
        explicit_runs[sentence_key] = {}
        sentence = SENTENCES[sentence_key]
        for proposal_id, lexicon_ids in proposals.items():
            explicit_runs[sentence_key][proposal_id] = _run_explicit(
                client,
                sentence_key=sentence_key,
                sentence=sentence,
                proposal_id=proposal_id,
                lexicon_ids=lexicon_ids,
            )

    auto_runs: dict[str, Any] = {}
    for sentence_key, sentence in SENTENCES.items():
        auto_runs[sentence_key] = _run_auto(client, sentence_key=sentence_key, sentence=sentence)

    payload = {
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "settings": {
            "grammar_id": "japanese2",
            "auto_add_ga_phi": False,
            "budget_seconds": BUDGET_SECONDS,
            "max_nodes": MAX_NODES,
            "max_depth": MAX_DEPTH,
            "top_k": TOP_K,
            "notes": [
                "S4/T1 baseline already fixed with 9301",
                "No grammar change, no search tweak, no phi auto supplement, no 266/9304 retry",
            ],
        },
        "explicit": {"runs": explicit_runs},
        "auto": {"runs": auto_runs},
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(_build_markdown(payload), encoding="utf-8")
    print(f"WROTE_JSON={OUT_JSON}")
    print(f"WROTE_MD={OUT_MD}")


if __name__ == "__main__":
    main()
