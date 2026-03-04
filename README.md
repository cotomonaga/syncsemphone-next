# syncsemphone-next

Migration workspace for the SyncSemPhone engine:
- Engine: FastAPI (Python)
- UI: React + TypeScript
- Method: DDD + TDD
- Terms (plain Japanese): `docs/specs/glossary-ja.md`

## Current Scope
- Grammar targets: imi01, imi02, imi03, japanese2
- Compatibility bar: practical parity with Perl reference outputs
- Current automated differential target: imi01/imi02/imi03 + japanese2(partial)
- japanese2 note: Perl側の rule番号体系（例: `sase1`）に合わせて rule番号↔rule名対応を導入済み。
  - 現状は candidates 差分と RH-Merge 候補全ペア + J-Merge 代表ペア + `sase1/sase2/rare1/rare2/property-Merge/rel-Merge/property-no/property-da/P-Merge/Partitioning` execute 差分まで自動化済み

## Quick Start (API)
```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
uvicorn app.main:app --reload
```

Perl資産はこのリポジトリ配下 `legacy/` に同梱されています。
`SYNCSEMPHONE_LEGACY_ROOT` を未設定の場合、API/Domain は `./legacy` を既定参照します。
（必要があれば `SYNCSEMPHONE_LEGACY_ROOT` で外部パスへ上書き可能）
`SYNCSEMPHONE_META_DB_URL`（または `DATABASE_URL`）を設定すると、Lexicon拡張API（value-dictionary / num-links / notes）がPostgreSQLを利用します。

## Quick Start (Web)
```bash
cd apps/web
npm install
npm run dev
```

既定では次の URL で利用します。
- API: `http://127.0.0.1:8000`
- Web: `http://127.0.0.1:5173`

この状態で、Legacy UI / Renewed UI の両方を同一リポジトリだけで起動できます。

## Test (API + Domain)
```bash
./scripts/test-all.sh
```

## Test (Web E2E / Playwright)
```bash
cd apps/web
npm run test:e2e
```

## UI Modes
- `Legacy UI（Perl互換検証）`
  - Perl版の導線に合わせた操作（numeration source, target選択, tree変換, resume など）を確認するための画面
- `Renewed UI（仮説検証）`
  - 左サイドメニュー + 上部ステップナビで、選択中ステップだけメイン表示する画面
  - 仮説検証ループを順に回しやすい運用向けUI

UI上部のトグルで `Legacy UI` / `Renewed UI` を切り替え可能です。

Manual replay by Playwright MCP:
- `docs/specs/playwright-mcp-manual-replay-ja.md`

## Implemented Endpoints
- `GET /v1/healthz`
- `POST /v1/derivation/init`
  - input: `grammar_id`, `numeration_text`, optional `legacy_root`
  - output: Perl `numeration_check` 相当の初期派生状態（`base`）
- `POST /v1/derivation/candidates`
  - input: `state`, `left`, `right`, optional `rh_merge_version`, `lh_merge_version`
  - output: 適用可能候補（rule_number は Perl `@rulename` 定義から解決）
- `POST /v1/derivation/execute`
  - input: `state`, (`rule_name` or `rule_number`), `left/right` (double規則用) または `check` (single規則用), optional `legacy_root`, `rh_merge_version`, `lh_merge_version`
  - output: 1手適用後の派生状態（現状は RH/LH + `sy/pr/sl/se` 主要分岐 + `α<sub>n</sub>` 追加、`se` feature `70/71` 対応を含む）
  - differential coverage: imi03 代表ケース + imi03多段探索 + imi01/imi02 T0全ペア + japanese2 RH候補全ペア + japanese2 J-Merge代表 + japanese2 `sase1/sase2/rare1/rare2/property-Merge/rel-Merge/property-no/property-da/P-Merge/Partitioning` + `se70/71` 合成ケース
- `POST /v1/derivation/resume/export`
  - input: `state`
  - output: Perl互換6行の `resume_text`
- `POST /v1/derivation/resume/import`
  - input: `resume_text`
  - output: 復元した派生状態
- `POST /v1/observation/tree`
  - input: `state`, `mode` (`tree` or `tree_cat`)
  - output: TreeDrawer互換のCSV行（`csv_lines`, `csv_text`）
- `POST /v1/semantics/lf`
  - input: `state`
  - output: `list_representation`（LFの一覧）と未解決トークン有無
- `POST /v1/semantics/sr`
  - input: `state`
  - output: `truth_conditional_meaning`（SR層の一覧）
- `GET /v1/lexicon/{grammar_id}?format=yaml|csv`
  - input: `grammar_id`, optional `format` (`yaml` default) and `legacy_root`
  - output: `lexicon_path`, `entry_count`, `content_text`（Perl互換CSVまたは編集用YAML）
- `POST /v1/lexicon/{grammar_id}/validate`
  - input: `yaml_text`, optional `source_csv`
  - output: `valid`, `errors`, `normalized_yaml_text`, `preview_csv_text`
- `POST /v1/lexicon/{grammar_id}/import`
  - input: `yaml_text`, optional `source_csv`
  - output: 変換済み `csv_text` と正規化 `normalized_yaml_text`（保存はまだ行わない）
- `POST /v1/lexicon/{grammar_id}/commit`
  - input: `yaml_text`, optional `source_csv`, optional `legacy_root`, `run_compatibility_tests` (default: true)
  - output: `committed/rolled_back`、`compatibility_passed`、`backup_path`、`committed_csv_text`、`stdout/stderr`
  - behavior: YAML検証後にCSVを原子的に保存し、互換テスト失敗時は自動 rollback
- `GET /v1/lexicon/{grammar_id}/items`
- `GET /v1/lexicon/{grammar_id}/items/{lexicon_id}`
- `POST /v1/lexicon/{grammar_id}/items`
- `PUT /v1/lexicon/{grammar_id}/items/{lexicon_id}`
- `DELETE /v1/lexicon/{grammar_id}/items/{lexicon_id}`
  - behavior: CSV正本を更新（互換テストは走らせず即時保存）
- `GET /v1/lexicon/value-dictionary`
- `POST /v1/lexicon/value-dictionary`
- `PUT /v1/lexicon/value-dictionary/{value_id}`
- `GET /v1/lexicon/value-dictionary/{value_id}/usages`
- `POST /v1/lexicon/value-dictionary/{value_id}/replace`
- `DELETE /v1/lexicon/value-dictionary/{value_id}`
  - behavior: 参照中削除は `409`
- `GET /v1/lexicon/{grammar_id}/items/{lexicon_id}/num-links`
- `POST /v1/lexicon/{grammar_id}/items/{lexicon_id}/num-links`
- `PUT /v1/lexicon/{grammar_id}/items/{lexicon_id}/num-links/{link_id}`
- `DELETE /v1/lexicon/{grammar_id}/items/{lexicon_id}/num-links/{link_id}`
- `GET /v1/lexicon/{grammar_id}/items/{lexicon_id}/notes`
- `PUT /v1/lexicon/{grammar_id}/items/{lexicon_id}/notes`
- `GET /v1/lexicon/{grammar_id}/items/{lexicon_id}/notes/revisions`
- `GET /v1/lexicon/{grammar_id}/items/{lexicon_id}/notes/revisions/{revision_id}`
- `POST /v1/lexicon/{grammar_id}/items/{lexicon_id}/notes/revisions/{revision_id}/restore`
- `GET /v1/lexicon/{grammar_id}/versions`
- `GET /v1/lexicon/{grammar_id}/versions/{revision_id}/diff`

### Additional Endpoints (Perl UI parity support)
- `GET /v1/derivation/grammars`
  - Perl `grammar-list.pl` を基に文法候補を返却
- `GET /v1/derivation/rules/{grammar_id}`
  - 文法ごとの rule番号/名前一覧を返却
- `GET /v1/derivation/numeration/files?grammar_id=...&source=set|saved`
  - `set-numeration` / `numeration` 配下の `.num` 一覧を返却
- `POST /v1/derivation/numeration/load`
  - `.num` ファイルを読み込んで `numeration_text` を返却
- `POST /v1/derivation/numeration/save`
  - `numeration` 配下へ `.num` を保存
- `POST /v1/derivation/numeration/compose`
  - `memo + lexicon_ids + plus/idx` から `.num` 3行テキストを生成
- `GET /v1/reference/features`
- `GET /v1/reference/features/{file_name}`
- `GET /v1/reference/rules/{grammar_id}`
- `GET /v1/reference/rules/doc/{file_name}`
  - `features/*.html` と `MergeRule/*.html` をUI参照用に提供
