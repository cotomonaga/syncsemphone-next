import { useEffect, useMemo, useState } from "react";
import { apiDelete, apiGet, apiPost, apiPut } from "./api";
import type {
  LexiconCommitResponse,
  LexiconExportResponse,
  LexiconExtItem,
  LexiconExtItemResponse,
  LexiconExtItemsResponse,
  LexiconImportResponse,
  LexiconValidateResponse,
  LexiconVersionDiffResponse,
  LexiconVersionsResponse,
  NoteCurrentResponse,
  NoteRevisionResponse,
  NoteRevisionsResponse,
  NumLinkItem,
  NumLinksResponse,
  ValueDictionaryItem,
  ValueDictionaryKind,
  ValueDictionaryListResponse,
  ValueDictionaryUsageResponse
} from "./types";

type LexiconWorkbenchProps = {
  grammarId: string;
};

type LexiconTab = "dictionary" | "numlinks" | "notes" | "versions" | "importexport";

const VALUE_KINDS: ValueDictionaryKind[] = [
  "category",
  "predicate",
  "sync_feature",
  "idslot",
  "semantic"
];

const EMPTY_ITEM: LexiconExtItem = {
  lexicon_id: null,
  entry: "",
  phono: "",
  category: "",
  predicates: [],
  sync_features: [],
  idslot: "",
  semantics: [],
  note: ""
};

function parsePredicateValue(value: string): string[] {
  const parts = value.split("|");
  if (parts.length !== 3) {
    return ["", "", ""];
  }
  return [parts[0], parts[1], parts[2]];
}

function normalizePredicateValue(parts: string[]): string {
  const row = [parts[0] || "", parts[1] || "", parts[2] || ""];
  return row.join("|");
}

function uniqueSorted(rows: string[]): string[] {
  return [...new Set(rows.filter((row) => row.trim() !== "").map((row) => row.trim()))].sort((a, b) =>
    a.localeCompare(b, "ja")
  );
}

export default function LexiconWorkbench({ grammarId }: LexiconWorkbenchProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [itemsPage, setItemsPage] = useState<LexiconExtItemsResponse | null>(null);
  const [selectedLexiconId, setSelectedLexiconId] = useState<number | null>(null);
  const [isNewItem, setIsNewItem] = useState(false);
  const [draft, setDraft] = useState<LexiconExtItem>(EMPTY_ITEM);

  const [dictionaryKind, setDictionaryKind] = useState<ValueDictionaryKind>("category");
  const [dictionaryItems, setDictionaryItems] = useState<ValueDictionaryItem[]>([]);
  const [selectedDictionaryId, setSelectedDictionaryId] = useState<number | null>(null);
  const [dictionaryUsage, setDictionaryUsage] = useState<ValueDictionaryUsageResponse | null>(null);
  const [dictionaryCreateValue, setDictionaryCreateValue] = useState("");
  const [dictionaryMetadataText, setDictionaryMetadataText] = useState("{}");
  const [dictionaryReplaceTargetId, setDictionaryReplaceTargetId] = useState<number | null>(null);

  const [numLinks, setNumLinks] = useState<NumLinkItem[]>([]);
  const [numLinkForm, setNumLinkForm] = useState({
    num_path: "",
    memo: "",
    slot_no: "",
    idx_value: "",
    comment: ""
  });

  const [noteMarkdown, setNoteMarkdown] = useState("");
  const [noteAuthor, setNoteAuthor] = useState("researcher");
  const [noteSummary, setNoteSummary] = useState("");
  const [noteUpdatedAt, setNoteUpdatedAt] = useState<string | null>(null);
  const [noteRevisions, setNoteRevisions] = useState<NoteRevisionsResponse["items"]>([]);
  const [selectedRevisionBody, setSelectedRevisionBody] = useState<NoteRevisionResponse | null>(null);

  const [versionItems, setVersionItems] = useState<LexiconVersionsResponse["items"]>([]);
  const [versionOffset, setVersionOffset] = useState(0);
  const [selectedRevisionId, setSelectedRevisionId] = useState("");
  const [diffFormat, setDiffFormat] = useState<"csv" | "yaml">("csv");
  const [versionDiffText, setVersionDiffText] = useState("");

  const [importExportFormat, setImportExportFormat] = useState<"yaml" | "csv">("yaml");
  const [importExportText, setImportExportText] = useState("");
  const [yamlInput, setYamlInput] = useState("");
  const [yamlErrors, setYamlErrors] = useState<string[]>([]);
  const [csvPreview, setCsvPreview] = useState("");
  const [commitMessage, setCommitMessage] = useState("");
  const [runCompatibility, setRunCompatibility] = useState(true);
  const [activeTab, setActiveTab] = useState<LexiconTab>("dictionary");

  const dictionaryByKind = useMemo(() => {
    const map = new Map<ValueDictionaryKind, string[]>();
    for (const kind of VALUE_KINDS) {
      map.set(kind, []);
    }
    for (const row of dictionaryItems) {
      if (!map.has(row.kind)) {
        map.set(row.kind, []);
      }
      map.get(row.kind)?.push(row.display_value);
    }
    for (const [kind, rows] of map.entries()) {
      map.set(kind, uniqueSorted(rows));
    }
    return map;
  }, [dictionaryItems]);

  const listDerivedOptions = useMemo(() => {
    const categories: string[] = [];
    const predicates: string[] = [];
    const syncFeatures: string[] = [];
    const idslots: string[] = [];
    const semantics: string[] = [];
    for (const row of itemsPage?.items || []) {
      if (row.category) {
        categories.push(row.category);
      }
      if (row.idslot) {
        idslots.push(row.idslot);
      }
      for (const pred of row.predicates || []) {
        predicates.push(normalizePredicateValue(pred));
      }
      for (const feature of row.sync_features || []) {
        syncFeatures.push(feature);
      }
      for (const semantic of row.semantics || []) {
        semantics.push(semantic);
      }
    }
    return {
      categories: uniqueSorted(categories),
      predicates: uniqueSorted(predicates),
      syncFeatures: uniqueSorted(syncFeatures),
      idslots: uniqueSorted(idslots),
      semantics: uniqueSorted(semantics)
    };
  }, [itemsPage]);

  const options = useMemo(() => {
    const fromDictionary = {
      categories: dictionaryByKind.get("category") || [],
      predicates: dictionaryByKind.get("predicate") || [],
      syncFeatures: dictionaryByKind.get("sync_feature") || [],
      idslots: dictionaryByKind.get("idslot") || [],
      semantics: dictionaryByKind.get("semantic") || []
    };
    return {
      categories: uniqueSorted([...fromDictionary.categories, ...listDerivedOptions.categories]),
      predicates: uniqueSorted([...fromDictionary.predicates, ...listDerivedOptions.predicates]),
      syncFeatures: uniqueSorted([...fromDictionary.syncFeatures, ...listDerivedOptions.syncFeatures]),
      idslots: uniqueSorted([...fromDictionary.idslots, ...listDerivedOptions.idslots]),
      semantics: uniqueSorted([...fromDictionary.semantics, ...listDerivedOptions.semantics])
    };
  }, [dictionaryByKind, listDerivedOptions]);

  async function runTask(task: () => Promise<void>) {
    setLoading(true);
    setError("");
    setMessage("");
    try {
      await task();
    } catch (taskError) {
      setError(taskError instanceof Error ? taskError.message : "操作に失敗しました。");
    } finally {
      setLoading(false);
    }
  }

  async function refreshItems(nextPage = page, nextQuery = query) {
    const response = await apiGet<LexiconExtItemsResponse>(
      `/v1/lexicon/${grammarId}/items?page=${nextPage}&page_size=50&q=${encodeURIComponent(nextQuery)}`
    );
    setItemsPage(response);
    setPage(response.page);
  }

  async function refreshDictionary(kind: ValueDictionaryKind = dictionaryKind) {
    const response = await apiGet<ValueDictionaryListResponse>(`/v1/lexicon/value-dictionary?kind=${kind}`);
    setDictionaryItems(response.items);
  }

  async function loadItem(lexiconId: number) {
    const response = await apiGet<LexiconExtItemResponse>(`/v1/lexicon/${grammarId}/items/${lexiconId}`);
    setDraft(response.item);
    setSelectedLexiconId(lexiconId);
    setIsNewItem(false);
  }

  async function refreshSelectedItemSidePanels(lexiconId: number | null) {
    if (lexiconId === null) {
      setNumLinks([]);
      setNoteMarkdown("");
      setNoteRevisions([]);
      setNoteUpdatedAt(null);
      return;
    }
    const [numLinksResponse, noteCurrent, noteRevisionsResponse] = await Promise.all([
      apiGet<NumLinksResponse>(`/v1/lexicon/${grammarId}/items/${lexiconId}/num-links`),
      apiGet<NoteCurrentResponse>(`/v1/lexicon/${grammarId}/items/${lexiconId}/notes`),
      apiGet<NoteRevisionsResponse>(`/v1/lexicon/${grammarId}/items/${lexiconId}/notes/revisions`)
    ]);
    setNumLinks(numLinksResponse.items);
    setNoteMarkdown(noteCurrent.markdown);
    setNoteUpdatedAt(noteCurrent.updated_at || null);
    setNoteRevisions(noteRevisionsResponse.items);
  }

  async function refreshVersions(nextOffset = versionOffset) {
    const response = await apiGet<LexiconVersionsResponse>(
      `/v1/lexicon/${grammarId}/versions?limit=20&offset=${nextOffset}`
    );
    setVersionItems(response.items);
  }

  useEffect(() => {
    void runTask(async () => {
      await Promise.all([refreshItems(1, ""), refreshVersions(0)]);
      try {
        await refreshDictionary("category");
      } catch {
        setDictionaryItems([]);
        setMessage("メタDB未設定のため、バリュー辞書機能は利用できません。");
      }
      setVersionOffset(0);
      setQuery("");
      setSelectedLexiconId(null);
      setIsNewItem(false);
      setDraft(EMPTY_ITEM);
      setSelectedRevisionBody(null);
      setSelectedRevisionId("");
      setVersionDiffText("");
      setNumLinks([]);
      setNoteMarkdown("");
      setNoteRevisions([]);
      setNoteUpdatedAt(null);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [grammarId]);

  useEffect(() => {
    void runTask(async () => {
      try {
        await refreshDictionary(dictionaryKind);
      } catch {
        setDictionaryItems([]);
        setMessage("メタDB未設定のため、バリュー辞書機能は利用できません。");
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dictionaryKind]);

  async function handleSelectItem(lexiconId: number) {
    await runTask(async () => {
      await loadItem(lexiconId);
      await refreshSelectedItemSidePanels(lexiconId);
      setMessage(`語彙項目 ${lexiconId} を読み込みました。`);
    });
  }

  function startNewItem() {
    const nextId =
      Math.max(0, ...(itemsPage?.items || []).map((row) => Number(row.lexicon_id || 0))) + 1;
    setDraft({ ...EMPTY_ITEM, lexicon_id: nextId });
    setSelectedLexiconId(null);
    setIsNewItem(true);
    setNumLinks([]);
    setNoteMarkdown("");
    setNoteRevisions([]);
    setNoteUpdatedAt(null);
    setSelectedRevisionBody(null);
  }

  async function handleSaveItem() {
    await runTask(async () => {
      if (isNewItem) {
        const response = await apiPost<LexiconExtItemResponse>(`/v1/lexicon/${grammarId}/items`, draft);
        const savedId = Number(response.item.lexicon_id);
        setSelectedLexiconId(savedId);
        setIsNewItem(false);
        setDraft(response.item);
        await refreshItems(page, query);
        await refreshSelectedItemSidePanels(savedId);
        setMessage(`語彙項目 ${savedId} を作成しました。`);
      } else {
        const currentId = Number(draft.lexicon_id || selectedLexiconId);
        if (!currentId) {
          throw new Error("保存対象の語彙IDがありません。");
        }
        const response = await apiPut<LexiconExtItemResponse>(
          `/v1/lexicon/${grammarId}/items/${currentId}`,
          draft
        );
        setDraft(response.item);
        await refreshItems(page, query);
        await refreshSelectedItemSidePanels(currentId);
        setMessage(`語彙項目 ${currentId} を更新しました。`);
      }
    });
  }

  async function handleDeleteItem() {
    const currentId = Number(draft.lexicon_id || selectedLexiconId);
    if (!currentId) {
      setError("削除対象の語彙IDがありません。");
      return;
    }
    await runTask(async () => {
      await apiDelete<{ deleted: boolean }>(`/v1/lexicon/${grammarId}/items/${currentId}`);
      await refreshItems(page, query);
      setSelectedLexiconId(null);
      setIsNewItem(false);
      setDraft(EMPTY_ITEM);
      setNumLinks([]);
      setNoteMarkdown("");
      setNoteRevisions([]);
      setNoteUpdatedAt(null);
      setMessage(`語彙項目 ${currentId} を削除しました。`);
    });
  }

  function updateDraftField<K extends keyof LexiconExtItem>(key: K, value: LexiconExtItem[K]) {
    setDraft((prev) => ({ ...prev, [key]: value }));
  }

  function updatePredicateRow(index: number, value: string) {
    const next = [...draft.predicates];
    next[index] = parsePredicateValue(value);
    updateDraftField("predicates", next);
  }

  function updateStringRow(kind: "sync_features" | "semantics", index: number, value: string) {
    const next = [...draft[kind]];
    next[index] = value;
    updateDraftField(kind, next);
  }

  function addStringRow(kind: "sync_features" | "semantics", defaultValue = "") {
    updateDraftField(kind, [...draft[kind], defaultValue]);
  }

  function removeStringRow(kind: "sync_features" | "semantics", index: number) {
    updateDraftField(
      kind,
      draft[kind].filter((_, idx) => idx !== index)
    );
  }

  function addPredicateRow(defaultValue = "") {
    updateDraftField("predicates", [...draft.predicates, parsePredicateValue(defaultValue)]);
  }

  function removePredicateRow(index: number) {
    updateDraftField(
      "predicates",
      draft.predicates.filter((_, idx) => idx !== index)
    );
  }

  async function handleCreateDictionaryValue() {
    await runTask(async () => {
      let metadata: Record<string, unknown> = {};
      if (dictionaryMetadataText.trim() !== "") {
        metadata = JSON.parse(dictionaryMetadataText);
      }
      await apiPost<ValueDictionaryItem>("/v1/lexicon/value-dictionary", {
        kind: dictionaryKind,
        display_value: dictionaryCreateValue,
        metadata_json: metadata
      });
      await refreshDictionary(dictionaryKind);
      setDictionaryCreateValue("");
      setMessage("バリュー辞書に追加しました。");
    });
  }

  async function handleUpdateDictionaryValue() {
    if (selectedDictionaryId === null) {
      return;
    }
    await runTask(async () => {
      const selected = dictionaryItems.find((row) => row.id === selectedDictionaryId);
      if (!selected) {
        throw new Error("更新対象の辞書値が見つかりません。");
      }
      let metadata: Record<string, unknown> = selected.metadata_json || {};
      if (dictionaryMetadataText.trim() !== "") {
        metadata = JSON.parse(dictionaryMetadataText);
      }
      await apiPut<ValueDictionaryItem>(`/v1/lexicon/value-dictionary/${selectedDictionaryId}`, {
        display_value: selected.display_value,
        metadata_json: metadata
      });
      await refreshDictionary(dictionaryKind);
      setMessage("バリュー辞書を更新しました。");
    });
  }

  async function handleDeleteDictionaryValue() {
    if (selectedDictionaryId === null) {
      return;
    }
    await runTask(async () => {
      await apiDelete<{ deleted: boolean }>(`/v1/lexicon/value-dictionary/${selectedDictionaryId}`);
      await refreshDictionary(dictionaryKind);
      setSelectedDictionaryId(null);
      setDictionaryUsage(null);
      setMessage("バリュー辞書を削除しました。");
    });
  }

  async function handleLoadDictionaryUsage() {
    if (selectedDictionaryId === null) {
      return;
    }
    await runTask(async () => {
      const usage = await apiGet<ValueDictionaryUsageResponse>(
        `/v1/lexicon/value-dictionary/${selectedDictionaryId}/usages`
      );
      setDictionaryUsage(usage);
    });
  }

  async function handleReplaceDictionaryValue() {
    if (selectedDictionaryId === null || dictionaryReplaceTargetId === null) {
      return;
    }
    await runTask(async () => {
      await apiPost<{ replaced: boolean; changed_count: number }>(
        `/v1/lexicon/value-dictionary/${selectedDictionaryId}/replace`,
        {
          replacement_value_id: dictionaryReplaceTargetId
        }
      );
      await Promise.all([refreshDictionary(dictionaryKind), refreshItems(page, query)]);
      setDictionaryUsage(null);
      setMessage("辞書値を一括置換しました。");
    });
  }

  async function handleCreateNumLink() {
    const currentId = Number(draft.lexicon_id || selectedLexiconId);
    if (!currentId) {
      return;
    }
    await runTask(async () => {
      await apiPost<NumLinkItem>(`/v1/lexicon/${grammarId}/items/${currentId}/num-links`, {
        num_path: numLinkForm.num_path,
        memo: numLinkForm.memo,
        slot_no: numLinkForm.slot_no.trim() === "" ? null : Number(numLinkForm.slot_no),
        idx_value: numLinkForm.idx_value,
        comment: numLinkForm.comment
      });
      await refreshSelectedItemSidePanels(currentId);
      setNumLinkForm({
        num_path: "",
        memo: "",
        slot_no: "",
        idx_value: "",
        comment: ""
      });
      setMessage("num紐付けを追加しました。");
    });
  }

  async function handleUpdateNumLink(row: NumLinkItem) {
    const currentId = Number(draft.lexicon_id || selectedLexiconId);
    if (!currentId) {
      return;
    }
    await runTask(async () => {
      await apiPut<NumLinkItem>(`/v1/lexicon/${grammarId}/items/${currentId}/num-links/${row.id}`, {
        memo: row.memo,
        slot_no: row.slot_no ?? null,
        idx_value: row.idx_value,
        comment: row.comment
      });
      await refreshSelectedItemSidePanels(currentId);
      setMessage("num紐付けを更新しました。");
    });
  }

  async function handleDeleteNumLink(linkId: number) {
    const currentId = Number(draft.lexicon_id || selectedLexiconId);
    if (!currentId) {
      return;
    }
    await runTask(async () => {
      await apiDelete<{ deleted: boolean }>(
        `/v1/lexicon/${grammarId}/items/${currentId}/num-links/${linkId}`
      );
      await refreshSelectedItemSidePanels(currentId);
      setMessage("num紐付けを削除しました。");
    });
  }

  async function handleSaveNote() {
    const currentId = Number(draft.lexicon_id || selectedLexiconId);
    if (!currentId) {
      return;
    }
    await runTask(async () => {
      const response = await apiPut<NoteCurrentResponse>(`/v1/lexicon/${grammarId}/items/${currentId}/notes`, {
        markdown: noteMarkdown,
        author: noteAuthor,
        change_summary: noteSummary
      });
      setNoteUpdatedAt(response.updated_at || null);
      await refreshSelectedItemSidePanels(currentId);
      setNoteSummary("");
      setMessage("研究メモを保存しました。");
    });
  }

  async function handleOpenRevision(revisionId: number) {
    const currentId = Number(draft.lexicon_id || selectedLexiconId);
    if (!currentId) {
      return;
    }
    await runTask(async () => {
      const response = await apiGet<NoteRevisionResponse>(
        `/v1/lexicon/${grammarId}/items/${currentId}/notes/revisions/${revisionId}`
      );
      setSelectedRevisionBody(response);
    });
  }

  async function handleRestoreRevision(revisionId: number) {
    const currentId = Number(draft.lexicon_id || selectedLexiconId);
    if (!currentId) {
      return;
    }
    await runTask(async () => {
      const response = await apiPost<NoteCurrentResponse>(
        `/v1/lexicon/${grammarId}/items/${currentId}/notes/revisions/${revisionId}/restore`,
        {}
      );
      setNoteMarkdown(response.markdown);
      setNoteUpdatedAt(response.updated_at || null);
      await refreshSelectedItemSidePanels(currentId);
      setMessage("履歴を復元しました。");
    });
  }

  async function handleLoadDiff() {
    if (!selectedRevisionId) {
      return;
    }
    await runTask(async () => {
      const response = await apiGet<LexiconVersionDiffResponse>(
        `/v1/lexicon/${grammarId}/versions/${selectedRevisionId}/diff?format=${diffFormat}`
      );
      setVersionDiffText(response.diff_text);
    });
  }

  async function handleLoadImportExport() {
    await runTask(async () => {
      const response = await apiGet<LexiconExportResponse>(
        `/v1/lexicon/${grammarId}?format=${importExportFormat}`
      );
      setImportExportText(response.content_text);
      if (response.format === "yaml") {
        setYamlInput(response.content_text);
      }
      setYamlErrors([]);
      setCsvPreview("");
      setCommitMessage("");
      setMessage("Lexiconを読み込みました。");
    });
  }

  async function handleValidateYaml() {
    await runTask(async () => {
      const response = await apiPost<LexiconValidateResponse>(`/v1/lexicon/${grammarId}/validate`, {
        yaml_text: yamlInput
      });
      setYamlErrors(response.errors);
      if (response.valid) {
        setImportExportText(response.normalized_yaml_text);
        setCsvPreview(response.preview_csv_text);
      } else {
        setCsvPreview("");
      }
      setMessage(response.valid ? "YAMLは妥当です。" : "YAMLにエラーがあります。");
    });
  }

  async function handleImportYaml() {
    await runTask(async () => {
      const response = await apiPost<LexiconImportResponse>(`/v1/lexicon/${grammarId}/import`, {
        yaml_text: yamlInput
      });
      setImportExportText(response.normalized_yaml_text);
      setCsvPreview(response.csv_text);
      setYamlErrors([]);
      setMessage("YAMLをCSVへ変換しました。");
    });
  }

  async function handleCommitYaml() {
    await runTask(async () => {
      const response = await apiPost<LexiconCommitResponse>(`/v1/lexicon/${grammarId}/commit`, {
        yaml_text: yamlInput,
        run_compatibility_tests: runCompatibility
      });
      setImportExportText(response.normalized_yaml_text);
      setCsvPreview(response.committed_csv_text);
      setYamlErrors(response.errors);
      setCommitMessage(response.message);
      await refreshItems(page, query);
      setMessage("Lexiconを保存しました。");
    });
  }

  const selectedDictionaryItem = dictionaryItems.find((row) => row.id === selectedDictionaryId) || null;
  const hasSelectedItem = Number(draft.lexicon_id || selectedLexiconId || 0) > 0;

  return (
    <div className="lexicon-workbench" data-testid="lexicon-workbench">
      <div className="lexicon-workbench-header">
        <h2>7. 語彙の編集</h2>
        <p className="hint">語彙項目中心の3ペイン。選択式編集・辞書管理・研究メモ/num紐付けを統合しています。</p>
      </div>

      {error && <p className="alert">{error}</p>}
      {message && <p className="hint">{message}</p>}

      <div className="lexicon-three-pane">
        <section className="lexicon-pane">
          <div className="lexicon-pane-header">
            <h3>語彙項目一覧</h3>
            <button type="button" onClick={() => void runTask(() => refreshItems(page, query))} disabled={loading}>
              再読込
            </button>
          </div>
          <div className="row">
            <input
              aria-label="Lexicon Search"
              placeholder="entry/phono/id で検索"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <button
              type="button"
              disabled={loading}
              onClick={() => {
                void runTask(async () => {
                  await refreshItems(1, query);
                });
              }}
            >
              検索
            </button>
            <button type="button" disabled={loading} onClick={startNewItem}>
              新規
            </button>
          </div>
          <div className="inspect-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>id</th>
                  <th>entry</th>
                  <th>category</th>
                </tr>
              </thead>
              <tbody>
                {(itemsPage?.items || []).map((row) => {
                  const isActive = Number(row.lexicon_id) === Number(draft.lexicon_id || selectedLexiconId);
                  return (
                    <tr
                      key={`lex-row-${row.lexicon_id}`}
                      className={isActive ? "lexicon-row-active" : ""}
                      onClick={() => {
                        void handleSelectItem(Number(row.lexicon_id));
                      }}
                    >
                      <td>{row.lexicon_id}</td>
                      <td>{row.entry}</td>
                      <td>{row.category}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="row">
            <button
              type="button"
              disabled={loading || page <= 1}
              onClick={() => {
                void runTask(async () => {
                  await refreshItems(page - 1, query);
                });
              }}
            >
              前へ
            </button>
            <span className="mono">
              page {itemsPage?.page || page} /{" "}
              {itemsPage ? Math.max(1, Math.ceil(itemsPage.total_count / itemsPage.page_size)) : "-"}
            </span>
            <button
              type="button"
              disabled={
                loading ||
                !itemsPage ||
                itemsPage.page >= Math.max(1, Math.ceil(itemsPage.total_count / itemsPage.page_size))
              }
              onClick={() => {
                void runTask(async () => {
                  await refreshItems(page + 1, query);
                });
              }}
            >
              次へ
            </button>
          </div>
        </section>

        <section className="lexicon-pane">
          <div className="lexicon-pane-header">
            <h3>語彙項目編集</h3>
            <div className="row">
              <button type="button" onClick={() => void handleSaveItem()} disabled={loading}>
                保存
              </button>
              <button type="button" onClick={() => void handleDeleteItem()} disabled={loading || !hasSelectedItem}>
                削除
              </button>
            </div>
          </div>

          <div className="form-grid">
            <label>
              lexicon_id
              <input
                aria-label="lexicon-id-input"
                type="number"
                value={draft.lexicon_id ?? ""}
                onChange={(event) => updateDraftField("lexicon_id", Number(event.target.value))}
                disabled={!isNewItem}
              />
            </label>
            <label>
              entry
              <input
                aria-label="lexicon-entry-input"
                value={draft.entry}
                onChange={(event) => updateDraftField("entry", event.target.value)}
              />
            </label>
            <label>
              phono
              <input
                aria-label="lexicon-phono-input"
                value={draft.phono}
                onChange={(event) => updateDraftField("phono", event.target.value)}
              />
            </label>
            <label>
              category
              <select
                aria-label="lexicon-category-select"
                value={draft.category}
                onChange={(event) => updateDraftField("category", event.target.value)}
              >
                <option value="">(選択)</option>
                {options.categories.map((row) => (
                  <option key={`opt-category-${row}`} value={row}>
                    {row}
                  </option>
                ))}
              </select>
            </label>
            <label>
              idslot
              <select
                aria-label="lexicon-idslot-select"
                value={draft.idslot}
                onChange={(event) => updateDraftField("idslot", event.target.value)}
              >
                <option value="">(選択)</option>
                {options.idslots.map((row) => (
                  <option key={`opt-idslot-${row}`} value={row}>
                    {row}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="lexicon-multi-field">
            <div className="lexicon-multi-header">
              <h4>predicates</h4>
              <button type="button" onClick={() => addPredicateRow(options.predicates[0] || "")} disabled={loading}>
                追加
              </button>
            </div>
            {draft.predicates.length === 0 ? (
              <p className="hint">未設定</p>
            ) : (
              draft.predicates.map((row, idx) => (
                <div className="row" key={`pred-row-${idx}`}>
                  <select
                    aria-label={`predicate-select-${idx}`}
                    value={normalizePredicateValue(row)}
                    onChange={(event) => updatePredicateRow(idx, event.target.value)}
                  >
                    <option value="">(選択)</option>
                    {options.predicates.map((opt) => (
                      <option key={`predicate-opt-${opt}`} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>
                  <button type="button" onClick={() => removePredicateRow(idx)} disabled={loading}>
                    削除
                  </button>
                </div>
              ))
            )}
          </div>

          <div className="lexicon-multi-field">
            <div className="lexicon-multi-header">
              <h4>sync_features</h4>
              <button
                type="button"
                onClick={() => addStringRow("sync_features", options.syncFeatures[0] || "")}
                disabled={loading}
              >
                追加
              </button>
            </div>
            {draft.sync_features.length === 0 ? (
              <p className="hint">未設定</p>
            ) : (
              draft.sync_features.map((row, idx) => (
                <div className="row" key={`sync-row-${idx}`}>
                  <select
                    aria-label={`sync-feature-select-${idx}`}
                    value={row}
                    onChange={(event) => updateStringRow("sync_features", idx, event.target.value)}
                  >
                    <option value="">(選択)</option>
                    {options.syncFeatures.map((opt) => (
                      <option key={`sync-opt-${opt}`} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>
                  <button type="button" onClick={() => removeStringRow("sync_features", idx)} disabled={loading}>
                    削除
                  </button>
                </div>
              ))
            )}
          </div>

          <div className="lexicon-multi-field">
            <div className="lexicon-multi-header">
              <h4>semantics</h4>
              <button
                type="button"
                onClick={() => addStringRow("semantics", options.semantics[0] || "")}
                disabled={loading}
              >
                追加
              </button>
            </div>
            {draft.semantics.length === 0 ? (
              <p className="hint">未設定</p>
            ) : (
              draft.semantics.map((row, idx) => (
                <div className="row" key={`sem-row-${idx}`}>
                  <select
                    aria-label={`semantic-select-${idx}`}
                    value={row}
                    onChange={(event) => updateStringRow("semantics", idx, event.target.value)}
                  >
                    <option value="">(選択)</option>
                    {options.semantics.map((opt) => (
                      <option key={`sem-opt-${opt}`} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>
                  <button type="button" onClick={() => removeStringRow("semantics", idx)} disabled={loading}>
                    削除
                  </button>
                </div>
              ))
            )}
          </div>

          <label>
            note
            <textarea
              aria-label="lexicon-note-input"
              rows={4}
              value={draft.note}
              onChange={(event) => updateDraftField("note", event.target.value)}
            />
          </label>
        </section>

        <section className="lexicon-pane">
          <div className="row lexicon-tab-row">
            <button
              type="button"
              className={activeTab === "dictionary" ? "renew-step-btn active" : "renew-step-btn"}
              onClick={() => setActiveTab("dictionary")}
            >
              辞書
            </button>
            <button
              type="button"
              className={activeTab === "numlinks" ? "renew-step-btn active" : "renew-step-btn"}
              onClick={() => setActiveTab("numlinks")}
            >
              num紐付け
            </button>
            <button
              type="button"
              className={activeTab === "notes" ? "renew-step-btn active" : "renew-step-btn"}
              onClick={() => setActiveTab("notes")}
            >
              研究メモ
            </button>
            <button
              type="button"
              className={activeTab === "versions" ? "renew-step-btn active" : "renew-step-btn"}
              onClick={() => setActiveTab("versions")}
            >
              版管理
            </button>
            <button
              type="button"
              className={activeTab === "importexport" ? "renew-step-btn active" : "renew-step-btn"}
              onClick={() => setActiveTab("importexport")}
            >
              CSV/YAML
            </button>
          </div>

          {activeTab === "dictionary" && (
            <div data-testid="lexicon-dictionary-tab">
              <h3>バリュー辞書</h3>
              <div className="row">
                <label>
                  kind
                  <select
                    aria-label="dictionary-kind-select"
                    value={dictionaryKind}
                    onChange={(event) => setDictionaryKind(event.target.value as ValueDictionaryKind)}
                  >
                    {VALUE_KINDS.map((kind) => (
                      <option key={`dict-kind-${kind}`} value={kind}>
                        {kind}
                      </option>
                    ))}
                  </select>
                </label>
                <button type="button" onClick={() => void runTask(() => refreshDictionary(dictionaryKind))} disabled={loading}>
                  更新
                </button>
              </div>
              <div className="inspect-table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>id</th>
                      <th>value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dictionaryItems.map((row) => (
                      <tr
                        key={`dict-row-${row.id}`}
                        className={selectedDictionaryId === row.id ? "lexicon-row-active" : ""}
                        onClick={() => {
                          setSelectedDictionaryId(row.id);
                          setDictionaryMetadataText(JSON.stringify(row.metadata_json || {}, null, 2));
                        }}
                      >
                        <td>{row.id}</td>
                        <td>{row.display_value}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <label>
                新規値
                <input
                  aria-label="dictionary-new-value"
                  value={dictionaryCreateValue}
                  onChange={(event) => setDictionaryCreateValue(event.target.value)}
                />
              </label>
              <label>
                metadata(JSON)
                <textarea
                  aria-label="dictionary-metadata-input"
                  rows={3}
                  value={dictionaryMetadataText}
                  onChange={(event) => setDictionaryMetadataText(event.target.value)}
                />
              </label>
              <div className="row">
                <button type="button" onClick={() => void handleCreateDictionaryValue()} disabled={loading || !dictionaryCreateValue.trim()}>
                  追加
                </button>
                <button type="button" onClick={() => void handleUpdateDictionaryValue()} disabled={loading || selectedDictionaryId === null}>
                  更新
                </button>
                <button type="button" onClick={() => void handleDeleteDictionaryValue()} disabled={loading || selectedDictionaryId === null}>
                  削除
                </button>
              </div>
              <div className="row">
                <button type="button" onClick={() => void handleLoadDictionaryUsage()} disabled={loading || selectedDictionaryId === null}>
                  使用件数
                </button>
                <select
                  aria-label="dictionary-replace-target"
                  value={dictionaryReplaceTargetId ?? ""}
                  onChange={(event) =>
                    setDictionaryReplaceTargetId(event.target.value ? Number(event.target.value) : null)
                  }
                >
                  <option value="">(置換先)</option>
                  {dictionaryItems
                    .filter((row) => row.id !== selectedDictionaryId)
                    .map((row) => (
                      <option key={`dict-replace-${row.id}`} value={row.id}>
                        {row.display_value}
                      </option>
                    ))}
                </select>
                <button
                  type="button"
                  onClick={() => void handleReplaceDictionaryValue()}
                  disabled={loading || selectedDictionaryId === null || dictionaryReplaceTargetId === null}
                >
                  一括置換
                </button>
              </div>
              {selectedDictionaryItem && (
                <p className="hint">選択中: {selectedDictionaryItem.display_value}</p>
              )}
              {dictionaryUsage && (
                <pre className="mono">
                  total_usages: {dictionaryUsage.total_usages}
                  {"\n"}
                  {JSON.stringify(dictionaryUsage.usages_by_grammar, null, 2)}
                </pre>
              )}
            </div>
          )}

          {activeTab === "numlinks" && (
            <div data-testid="lexicon-numlinks-tab">
              <h3>num紐付け</h3>
              {!hasSelectedItem ? (
                <p className="hint">語彙項目を選択してください。</p>
              ) : (
                <>
                  <div className="form-grid">
                    <label>
                      num_path
                      <input
                        aria-label="num-link-path-input"
                        value={numLinkForm.num_path}
                        onChange={(event) => setNumLinkForm((prev) => ({ ...prev, num_path: event.target.value }))}
                      />
                    </label>
                    <label>
                      memo
                      <input
                        value={numLinkForm.memo}
                        onChange={(event) => setNumLinkForm((prev) => ({ ...prev, memo: event.target.value }))}
                      />
                    </label>
                    <label>
                      slot
                      <input
                        value={numLinkForm.slot_no}
                        onChange={(event) => setNumLinkForm((prev) => ({ ...prev, slot_no: event.target.value }))}
                      />
                    </label>
                    <label>
                      idx
                      <input
                        value={numLinkForm.idx_value}
                        onChange={(event) => setNumLinkForm((prev) => ({ ...prev, idx_value: event.target.value }))}
                      />
                    </label>
                  </div>
                  <label>
                    comment
                    <textarea
                      rows={2}
                      value={numLinkForm.comment}
                      onChange={(event) => setNumLinkForm((prev) => ({ ...prev, comment: event.target.value }))}
                    />
                  </label>
                  <button type="button" onClick={() => void handleCreateNumLink()} disabled={loading || !numLinkForm.num_path.trim()}>
                    追加
                  </button>
                  <div className="inspect-table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>path</th>
                          <th>memo</th>
                          <th>slot/idx</th>
                          <th>操作</th>
                        </tr>
                      </thead>
                      <tbody>
                        {numLinks.map((row) => (
                          <tr key={`num-link-${row.id}`}>
                            <td>{row.num_path}</td>
                            <td>{row.memo}</td>
                            <td>
                              {row.slot_no ?? "-"} / {row.idx_value || "-"}
                            </td>
                            <td>
                              <button type="button" onClick={() => void handleUpdateNumLink(row)} disabled={loading}>
                                保存
                              </button>
                              <button type="button" onClick={() => void handleDeleteNumLink(row.id)} disabled={loading}>
                                削除
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </div>
          )}

          {activeTab === "notes" && (
            <div data-testid="lexicon-notes-tab">
              <h3>研究メモ</h3>
              {!hasSelectedItem ? (
                <p className="hint">語彙項目を選択してください。</p>
              ) : (
                <>
                  <label>
                    markdown
                    <textarea
                      aria-label="note-markdown-input"
                      rows={7}
                      value={noteMarkdown}
                      onChange={(event) => setNoteMarkdown(event.target.value)}
                    />
                  </label>
                  <div className="row">
                    <label>
                      author
                      <input
                        value={noteAuthor}
                        onChange={(event) => setNoteAuthor(event.target.value)}
                      />
                    </label>
                    <label>
                      change summary
                      <input
                        value={noteSummary}
                        onChange={(event) => setNoteSummary(event.target.value)}
                      />
                    </label>
                  </div>
                  <div className="row">
                    <button type="button" onClick={() => void handleSaveNote()} disabled={loading}>
                      保存
                    </button>
                    <span className="mono">{noteUpdatedAt ? `updated: ${noteUpdatedAt}` : "updated: -"}</span>
                  </div>
                  <div className="inspect-table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>rev</th>
                          <th>author</th>
                          <th>summary</th>
                          <th>操作</th>
                        </tr>
                      </thead>
                      <tbody>
                        {noteRevisions.map((row) => (
                          <tr key={`note-rev-${row.id}`}>
                            <td>{row.revision_no}</td>
                            <td>{row.author}</td>
                            <td>{row.change_summary}</td>
                            <td>
                              <button type="button" onClick={() => void handleOpenRevision(row.id)} disabled={loading}>
                                表示
                              </button>
                              <button type="button" onClick={() => void handleRestoreRevision(row.id)} disabled={loading}>
                                復元
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {selectedRevisionBody && (
                    <pre className="mono">{selectedRevisionBody.markdown}</pre>
                  )}
                </>
              )}
            </div>
          )}

          {activeTab === "versions" && (
            <div data-testid="lexicon-versions-tab">
              <h3>CSV/YAML 版管理</h3>
              <div className="row">
                <button
                  type="button"
                  onClick={() => {
                    const next = Math.max(0, versionOffset - 20);
                    setVersionOffset(next);
                    void runTask(() => refreshVersions(next));
                  }}
                  disabled={loading || versionOffset === 0}
                >
                  前へ
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const next = versionOffset + 20;
                    setVersionOffset(next);
                    void runTask(() => refreshVersions(next));
                  }}
                  disabled={loading}
                >
                  次へ
                </button>
              </div>
              <div className="inspect-table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>revision</th>
                      <th>author</th>
                      <th>message</th>
                    </tr>
                  </thead>
                  <tbody>
                    {versionItems.map((row) => (
                      <tr
                        key={`version-${row.revision_id}`}
                        className={selectedRevisionId === row.revision_id ? "lexicon-row-active" : ""}
                        onClick={() => setSelectedRevisionId(row.revision_id)}
                      >
                        <td>{row.revision_id.slice(0, 12)}</td>
                        <td>{row.author}</td>
                        <td>{row.message}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="row">
                <select
                  aria-label="version-diff-format"
                  value={diffFormat}
                  onChange={(event) => setDiffFormat(event.target.value as "csv" | "yaml")}
                >
                  <option value="csv">csv</option>
                  <option value="yaml">yaml</option>
                </select>
                <button type="button" onClick={() => void handleLoadDiff()} disabled={loading || !selectedRevisionId}>
                  差分を表示
                </button>
              </div>
              <pre className="mono" data-testid="lexicon-version-diff-output">{versionDiffText}</pre>
            </div>
          )}

          {activeTab === "importexport" && (
            <div data-testid="lexicon-importexport-tab">
              <h3>CSV/YAML 入出力</h3>
              <div className="row">
                <select
                  aria-label="lexicon-import-export-format"
                  value={importExportFormat}
                  onChange={(event) => setImportExportFormat(event.target.value as "yaml" | "csv")}
                >
                  <option value="yaml">yaml</option>
                  <option value="csv">csv</option>
                </select>
                <button type="button" onClick={() => void handleLoadImportExport()} disabled={loading}>
                  読込
                </button>
              </div>
              <pre className="mono" data-testid="lexicon-importexport-output">{importExportText}</pre>
              <label>
                YAML入力
                <textarea
                  aria-label="lexicon-yaml-input"
                  rows={6}
                  value={yamlInput}
                  onChange={(event) => setYamlInput(event.target.value)}
                />
              </label>
              <div className="row">
                <button type="button" onClick={() => void handleValidateYaml()} disabled={loading || !yamlInput.trim()}>
                  Validate
                </button>
                <button type="button" onClick={() => void handleImportYaml()} disabled={loading || !yamlInput.trim()}>
                  Import
                </button>
                <button type="button" onClick={() => void handleCommitYaml()} disabled={loading || !yamlInput.trim()}>
                  Commit
                </button>
              </div>
              <label>
                <input
                  type="checkbox"
                  checked={runCompatibility}
                  onChange={(event) => setRunCompatibility(event.target.checked)}
                />
                compatibility test を実行
              </label>
              {yamlErrors.length > 0 && <pre className="mono">{yamlErrors.join("\n")}</pre>}
              <p className="hint">{commitMessage}</p>
              <pre className="mono" data-testid="lexicon-csv-preview-output">{csvPreview}</pre>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
