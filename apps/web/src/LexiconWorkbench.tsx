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
  focusLexiconId?: number | null;
  focusLexiconNonce?: number;
};

type LexiconTopTab = "items" | "edit" | "dictionary" | "importexport";
type ListSortKey = "lexicon_id" | "entry" | "category";
type SortOrder = "asc" | "desc";

const VALUE_KINDS: ValueDictionaryKind[] = [
  "category",
  "predicate",
  "sync_feature",
  "idslot",
  "semantic"
];

const MERGE_RULE_IDSLOT_VALUES = [
  "id",
  "zero",
  "rel",
  "0,24",
  "2,22",
  "2,24",
  "2,27,target"
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

function normalizeIdslotValue(value: string): string {
  return value.trim().replace(/,+$/, "");
}

function normalizeDictionaryValue(kind: ValueDictionaryKind, value: string): string {
  if (kind === "idslot") {
    return normalizeIdslotValue(value);
  }
  return value.trim();
}

function uniqueSorted(rows: string[]): string[] {
  return [...new Set(rows.filter((row) => row.trim() !== "").map((row) => row.trim()))].sort((a, b) =>
    a.localeCompare(b, "ja")
  );
}

function markdownInline(text: string): string {
  return text.replace(/`([^`]+)`/g, "<code>$1</code>");
}

function renderMarkdownPreview(markdown: string): Array<JSX.Element> {
  const normalized = markdown.replace(/\r\n/g, "\n");
  const lines = normalized.split("\n");
  const elements: Array<JSX.Element> = [];
  let listItems: string[] = [];
  let inCode = false;
  let codeLines: string[] = [];
  let key = 0;

  const flushList = () => {
    if (listItems.length === 0) {
      return;
    }
    const rows = [...listItems];
    listItems = [];
    elements.push(
      <ul key={`md-list-${key++}`}>
        {rows.map((row, index) => (
          <li key={`md-list-item-${key}-${index}`} dangerouslySetInnerHTML={{ __html: markdownInline(row) }} />
        ))}
      </ul>
    );
  };

  const flushCode = () => {
    if (codeLines.length === 0) {
      return;
    }
    const body = codeLines.join("\n");
    codeLines = [];
    elements.push(
      <pre key={`md-code-${key++}`} className="mono">
        {body}
      </pre>
    );
  };

  for (const rawLine of lines) {
    const line = rawLine ?? "";
    const trimmed = line.trim();
    if (trimmed.startsWith("```")) {
      if (inCode) {
        flushCode();
        inCode = false;
      } else {
        flushList();
        inCode = true;
      }
      continue;
    }
    if (inCode) {
      codeLines.push(line);
      continue;
    }
    if (trimmed === "") {
      flushList();
      elements.push(<div key={`md-empty-${key++}`} className="lexicon-md-gap" />);
      continue;
    }
    if (trimmed.startsWith("- ")) {
      listItems.push(trimmed.slice(2));
      continue;
    }
    flushList();
    if (trimmed.startsWith("### ")) {
      elements.push(<h5 key={`md-h3-${key++}`}>{trimmed.slice(4)}</h5>);
      continue;
    }
    if (trimmed.startsWith("## ")) {
      elements.push(<h4 key={`md-h2-${key++}`}>{trimmed.slice(3)}</h4>);
      continue;
    }
    if (trimmed.startsWith("# ")) {
      elements.push(<h3 key={`md-h1-${key++}`}>{trimmed.slice(2)}</h3>);
      continue;
    }
    elements.push(<p key={`md-p-${key++}`} dangerouslySetInnerHTML={{ __html: markdownInline(trimmed) }} />);
  }
  flushList();
  if (inCode) {
    flushCode();
  }
  if (elements.length === 0) {
    elements.push(
      <p key="md-empty-default" className="hint">
        研究メモを入力すると、ここにMarkdownプレビューが表示されます。
      </p>
    );
  }
  return elements;
}

function extractLexiconScopedDiff(rawText: string, lexiconId: number, format: "csv" | "yaml"): string {
  if (!rawText.trim() || lexiconId <= 0) {
    return rawText;
  }
  if (format === "csv") {
    const csvPattern = new RegExp(`^\\s*${lexiconId}\\s*(?:\\t|,)`);
    const rows = rawText.split(/\r?\n/).filter((line) => csvPattern.test(line));
    if (rows.length > 0) {
      return rows.join("\n");
    }
    return rawText;
  }
  const lines = rawText.split(/\r?\n/);
  const start = lines.findIndex((line) =>
    /^\s*-?\s*lexicon_id:\s*\d+/.test(line) && line.includes(`lexicon_id: ${lexiconId}`)
  );
  if (start < 0) {
    return rawText;
  }
  let end = start + 1;
  while (end < lines.length) {
    const line = lines[end];
    if (/^\s*-?\s*lexicon_id:\s*\d+/.test(line) && !line.includes(`lexicon_id: ${lexiconId}`)) {
      break;
    }
    end += 1;
  }
  return lines.slice(start, end).join("\n");
}

export default function LexiconWorkbench({
  grammarId,
  focusLexiconId = null,
  focusLexiconNonce = 0
}: LexiconWorkbenchProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [sortKey, setSortKey] = useState<ListSortKey>("lexicon_id");
  const [sortOrder, setSortOrder] = useState<SortOrder>("asc");
  const [itemsPage, setItemsPage] = useState<LexiconExtItemsResponse | null>(null);
  const [selectedListLexiconId, setSelectedListLexiconId] = useState<number | null>(null);
  const [selectedLexiconId, setSelectedLexiconId] = useState<number | null>(null);
  const [isNewItem, setIsNewItem] = useState(false);
  const [draft, setDraft] = useState<LexiconExtItem>(EMPTY_ITEM);
  const [activeTopTab, setActiveTopTab] = useState<LexiconTopTab>("items");
  const [grammarIdslotValues, setGrammarIdslotValues] = useState<string[]>([]);

  const [dictionaryKind, setDictionaryKind] = useState<ValueDictionaryKind>("category");
  const [dictionaryItems, setDictionaryItems] = useState<ValueDictionaryItem[]>([]);
  const [dictionarySource, setDictionarySource] = useState<"db" | "lexicon_fallback">("db");
  const [selectedDictionaryId, setSelectedDictionaryId] = useState<number | null>(null);
  const [dictionaryUsage, setDictionaryUsage] = useState<ValueDictionaryUsageResponse | null>(null);
  const [dictionaryCreateValue, setDictionaryCreateValue] = useState("");
  const [dictionaryReplaceTargetId, setDictionaryReplaceTargetId] = useState<number | null>(null);
  const [semanticDictionaryOptions, setSemanticDictionaryOptions] = useState<string[]>([]);

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
  const [isWorkbenchReady, setIsWorkbenchReady] = useState(false);

  const dictionaryByKind = useMemo(() => {
    const map = new Map<ValueDictionaryKind, string[]>();
    for (const kind of VALUE_KINDS) {
      map.set(kind, []);
    }
    for (const row of dictionaryItems) {
      if (!map.has(row.kind)) {
        map.set(row.kind, []);
      }
      if (row.kind === "idslot") {
        map.get(row.kind)?.push(normalizeIdslotValue(row.display_value));
      } else {
        map.get(row.kind)?.push(row.display_value);
      }
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
        idslots.push(normalizeIdslotValue(row.idslot));
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

  const idslotAllowSet = useMemo(() => {
    return new Set(
      uniqueSorted([
        ...MERGE_RULE_IDSLOT_VALUES.map((row) => normalizeIdslotValue(row)),
        ...grammarIdslotValues.map((row) => normalizeIdslotValue(row))
      ])
    );
  }, [grammarIdslotValues]);

  const options = useMemo(() => {
    const fromDictionary = {
      categories: dictionaryByKind.get("category") || [],
      predicates: dictionaryByKind.get("predicate") || [],
      syncFeatures: dictionaryByKind.get("sync_feature") || [],
      idslots: dictionaryByKind.get("idslot") || [],
      semantics: semanticDictionaryOptions
    };
    const draftIdslot = normalizeIdslotValue(draft.idslot);
    const mergedIdslots = uniqueSorted([
      ...fromDictionary.idslots.map((row) => normalizeIdslotValue(row)),
      ...listDerivedOptions.idslots.map((row) => normalizeIdslotValue(row)),
      ...grammarIdslotValues.map((row) => normalizeIdslotValue(row)),
      draftIdslot
    ]);
    return {
      categories: uniqueSorted([...fromDictionary.categories, ...listDerivedOptions.categories]),
      predicates: uniqueSorted([...fromDictionary.predicates, ...listDerivedOptions.predicates]),
      syncFeatures: uniqueSorted([...fromDictionary.syncFeatures, ...listDerivedOptions.syncFeatures]),
      idslots: mergedIdslots.filter(
        (row) => row !== "" && (idslotAllowSet.has(row) || (draftIdslot !== "" && row === draftIdslot))
      ),
      semantics: uniqueSorted([...fromDictionary.semantics, ...draft.semantics])
    };
  }, [
    dictionaryByKind,
    draft.idslot,
    draft.semantics,
    grammarIdslotValues,
    idslotAllowSet,
    listDerivedOptions,
    semanticDictionaryOptions
  ]);

  const selectedDictionaryItem = dictionaryItems.find((row) => row.id === selectedDictionaryId) || null;
  const dictionaryInputNormalized = normalizeDictionaryValue(dictionaryKind, dictionaryCreateValue);
  const selectedDictionaryValueNormalized = selectedDictionaryItem
    ? normalizeDictionaryValue(selectedDictionaryItem.kind, selectedDictionaryItem.display_value)
    : "";
  const hasDictionaryDuplicate = dictionaryItems.some(
    (row) =>
      normalizeDictionaryValue(row.kind, row.display_value) === dictionaryInputNormalized &&
      (selectedDictionaryItem === null || row.id !== selectedDictionaryItem.id)
  );
  const canCreateDictionaryValue =
    dictionaryInputNormalized !== "" &&
    !dictionaryItems.some((row) => normalizeDictionaryValue(row.kind, row.display_value) === dictionaryInputNormalized);
  const canUpdateDictionaryValue =
    selectedDictionaryItem !== null &&
    dictionaryInputNormalized !== "" &&
    dictionaryInputNormalized !== selectedDictionaryValueNormalized &&
    !hasDictionaryDuplicate;

  const currentLexiconId = Number(draft.lexicon_id || selectedLexiconId || 0);
  const hasSelectedItem = currentLexiconId > 0;

  const effectiveVersionItems = useMemo(() => {
    if (versionItems.length > 0) {
      return versionItems;
    }
    return [
      {
        revision_id: "working-tree-current",
        author: "local",
        date: new Date().toISOString(),
        message: "current csv snapshot"
      }
    ];
  }, [versionItems]);

  const scopedVersionDiff = useMemo(
    () => extractLexiconScopedDiff(versionDiffText, currentLexiconId, diffFormat),
    [currentLexiconId, diffFormat, versionDiffText]
  );

  function sortArrow(key: ListSortKey): string {
    if (sortKey !== key) {
      return "⇅";
    }
    return sortOrder === "asc" ? "▲" : "▼";
  }

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

  async function refreshItems(
    nextPage = page,
    nextQuery = query,
    nextSort: ListSortKey = sortKey,
    nextOrder: SortOrder = sortOrder
  ) {
    const response = await apiGet<LexiconExtItemsResponse>(
      `/v1/lexicon/${grammarId}/items?page=${nextPage}&page_size=50&q=${encodeURIComponent(nextQuery)}&sort=${nextSort}&order=${nextOrder}`
    );
    setItemsPage(response);
    setPage(response.page);
  }

  async function refreshAllIdslotValues() {
    let nextPage = 1;
    const values = new Set<string>();
    while (true) {
      const response = await apiGet<LexiconExtItemsResponse>(
        `/v1/lexicon/${grammarId}/items?page=${nextPage}&page_size=300&q=&sort=lexicon_id&order=asc`
      );
      for (const row of response.items) {
        if (row.idslot) {
          values.add(normalizeIdslotValue(row.idslot));
        }
      }
      const totalPages = Math.max(1, Math.ceil(response.total_count / response.page_size));
      if (nextPage >= totalPages) {
        break;
      }
      nextPage += 1;
    }
    setGrammarIdslotValues(uniqueSorted([...values]));
  }

  async function refreshDictionary(kind: ValueDictionaryKind = dictionaryKind) {
    const response = await apiGet<ValueDictionaryListResponse>(`/v1/lexicon/value-dictionary?kind=${kind}`);
    setDictionaryItems(response.items);
    setDictionarySource(response.source || "db");
  }

  async function refreshSemanticDictionaryOptions() {
    const response = await apiGet<ValueDictionaryListResponse>("/v1/lexicon/value-dictionary?kind=semantic");
    setSemanticDictionaryOptions(uniqueSorted(response.items.map((row) => row.display_value)));
  }

  async function loadItem(lexiconId: number) {
    const response = await apiGet<LexiconExtItemResponse>(`/v1/lexicon/${grammarId}/items/${lexiconId}`);
    setDraft({ ...response.item, idslot: normalizeIdslotValue(response.item.idslot || "") });
    setSelectedLexiconId(lexiconId);
    setSelectedListLexiconId(lexiconId);
    setIsNewItem(false);
  }

  async function refreshSelectedItemSidePanels(lexiconId: number | null) {
    if (lexiconId === null) {
      setNumLinks([]);
      setNoteMarkdown("");
      setNoteRevisions([]);
      setNoteUpdatedAt(null);
      setSelectedRevisionBody(null);
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
    setIsWorkbenchReady(false);
    void runTask(async () => {
      await Promise.all([
        refreshItems(1, "", "lexicon_id", "asc"),
        refreshVersions(0),
        refreshAllIdslotValues(),
        refreshSemanticDictionaryOptions()
      ]);
      try {
        await refreshDictionary("category");
      } catch {
        setDictionaryItems([]);
        setSemanticDictionaryOptions([]);
        setMessage("メタDB未設定のため、バリュー辞書機能は利用できません。");
      }
      setVersionOffset(0);
      setQuery("");
      setSortKey("lexicon_id");
      setSortOrder("asc");
      setSelectedListLexiconId(null);
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
      setActiveTopTab("items");
      setIsWorkbenchReady(true);
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

  useEffect(() => {
    if (!isWorkbenchReady || focusLexiconId === null || focusLexiconId <= 0) {
      return;
    }
    void runTask(async () => {
      await loadItem(focusLexiconId);
      await refreshSelectedItemSidePanels(focusLexiconId);
      setActiveTopTab("edit");
      setMessage(`語彙項目 ${focusLexiconId} を読み込みました。`);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusLexiconId, focusLexiconNonce, isWorkbenchReady]);

  async function handleSearchItems() {
    await runTask(async () => {
      await refreshItems(1, query, sortKey, sortOrder);
    });
  }

  async function handleToggleSort(nextSort: ListSortKey) {
    const nextOrder: SortOrder = sortKey === nextSort && sortOrder === "asc" ? "desc" : "asc";
    setSortKey(nextSort);
    setSortOrder(nextOrder);
    await runTask(async () => {
      await refreshItems(1, query, nextSort, nextOrder);
    });
  }

  async function openItemForEdit(lexiconId: number) {
    await runTask(async () => {
      await loadItem(lexiconId);
      await refreshSelectedItemSidePanels(lexiconId);
      setActiveTopTab("edit");
      setMessage(`語彙項目 ${lexiconId} を読み込みました。`);
    });
  }

  async function startNewItem() {
    await runTask(async () => {
      const latest = await apiGet<LexiconExtItemsResponse>(
        `/v1/lexicon/${grammarId}/items?page=1&page_size=1&q=&sort=lexicon_id&order=desc`
      );
      const nextId = Number(latest.items[0]?.lexicon_id || 0) + 1;
      setDraft({ ...EMPTY_ITEM, lexicon_id: nextId });
      setSelectedLexiconId(null);
      setSelectedListLexiconId(null);
      setIsNewItem(true);
      setNumLinks([]);
      setNoteMarkdown("");
      setNoteRevisions([]);
      setNoteUpdatedAt(null);
      setSelectedRevisionBody(null);
      setVersionDiffText("");
      setActiveTopTab("edit");
    });
  }

  async function handleSaveItem() {
    await runTask(async () => {
      const normalizedDraft = { ...draft, idslot: normalizeIdslotValue(draft.idslot || "") };
      if (isNewItem) {
        const response = await apiPost<LexiconExtItemResponse>(`/v1/lexicon/${grammarId}/items`, normalizedDraft);
        const savedId = Number(response.item.lexicon_id);
        setSelectedLexiconId(savedId);
        setSelectedListLexiconId(savedId);
        setIsNewItem(false);
        setDraft({ ...response.item, idslot: normalizeIdslotValue(response.item.idslot || "") });
        await Promise.all([
          refreshItems(page, query, sortKey, sortOrder),
          refreshSelectedItemSidePanels(savedId),
          refreshAllIdslotValues()
        ]);
        setMessage(`語彙項目 ${savedId} を作成しました。`);
      } else {
        const currentId = Number(draft.lexicon_id || selectedLexiconId);
        if (!currentId) {
          throw new Error("保存対象の語彙IDがありません。");
        }
        const response = await apiPut<LexiconExtItemResponse>(
          `/v1/lexicon/${grammarId}/items/${currentId}`,
          normalizedDraft
        );
        setDraft({ ...response.item, idslot: normalizeIdslotValue(response.item.idslot || "") });
        await Promise.all([
          refreshItems(page, query, sortKey, sortOrder),
          refreshSelectedItemSidePanels(currentId),
          refreshAllIdslotValues()
        ]);
        setMessage(`語彙項目 ${currentId} を更新しました。`);
      }
    });
  }

  async function handleDeleteItem() {
    const targetId = Number(draft.lexicon_id || selectedLexiconId);
    if (!targetId) {
      setError("削除対象の語彙IDがありません。");
      return;
    }
    await runTask(async () => {
      await apiDelete<{ deleted: boolean }>(`/v1/lexicon/${grammarId}/items/${targetId}`);
      await Promise.all([refreshItems(page, query, sortKey, sortOrder), refreshAllIdslotValues()]);
      setSelectedLexiconId(null);
      setSelectedListLexiconId(null);
      setIsNewItem(false);
      setDraft(EMPTY_ITEM);
      setNumLinks([]);
      setNoteMarkdown("");
      setNoteRevisions([]);
      setNoteUpdatedAt(null);
      setSelectedRevisionBody(null);
      setVersionDiffText("");
      setMessage(`語彙項目 ${targetId} を削除しました。`);
    });
  }

  function updateDraftField<K extends keyof LexiconExtItem>(key: K, value: LexiconExtItem[K]) {
    if (key === "idslot") {
      setDraft((prev) => ({ ...prev, [key]: normalizeIdslotValue(String(value || "")) as LexiconExtItem[K] }));
      return;
    }
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
      const normalizedDisplayValue = normalizeDictionaryValue(dictionaryKind, dictionaryCreateValue);
      await apiPost<ValueDictionaryItem>("/v1/lexicon/value-dictionary", {
        kind: dictionaryKind,
        display_value: normalizedDisplayValue,
        metadata_json: {}
      });
      await Promise.all([refreshDictionary(dictionaryKind), refreshAllIdslotValues(), refreshSemanticDictionaryOptions()]);
      setDictionaryCreateValue("");
      setSelectedDictionaryId(null);
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
      const normalizedDisplayValue = normalizeDictionaryValue(selected.kind, dictionaryCreateValue);
      await apiPut<ValueDictionaryItem>(`/v1/lexicon/value-dictionary/${selectedDictionaryId}`, {
        display_value: normalizedDisplayValue,
        metadata_json: selected.metadata_json || {}
      });
      await Promise.all([refreshDictionary(dictionaryKind), refreshAllIdslotValues(), refreshSemanticDictionaryOptions()]);
      setMessage("バリュー辞書を更新しました。");
    });
  }

  async function handleDeleteDictionaryValue() {
    if (selectedDictionaryId === null) {
      return;
    }
    await runTask(async () => {
      await apiDelete<{ deleted: boolean }>(`/v1/lexicon/value-dictionary/${selectedDictionaryId}`);
      await Promise.all([refreshDictionary(dictionaryKind), refreshAllIdslotValues(), refreshSemanticDictionaryOptions()]);
      setSelectedDictionaryId(null);
      setDictionaryCreateValue("");
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
      await Promise.all([
        refreshDictionary(dictionaryKind),
        refreshItems(page, query, sortKey, sortOrder),
        refreshAllIdslotValues(),
        refreshSemanticDictionaryOptions()
      ]);
      setDictionaryReplaceTargetId(null);
      setDictionaryUsage(null);
      setMessage("辞書値を一括置換しました。");
    });
  }

  async function handleCreateNumLink() {
    if (!hasSelectedItem) {
      return;
    }
    await runTask(async () => {
      await apiPost<NumLinkItem>(`/v1/lexicon/${grammarId}/items/${currentLexiconId}/num-links`, {
        num_path: numLinkForm.num_path,
        memo: numLinkForm.memo,
        slot_no: numLinkForm.slot_no.trim() === "" ? null : Number(numLinkForm.slot_no),
        idx_value: numLinkForm.idx_value,
        comment: numLinkForm.comment
      });
      await refreshSelectedItemSidePanels(currentLexiconId);
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
    if (!hasSelectedItem) {
      return;
    }
    await runTask(async () => {
      await apiPut<NumLinkItem>(`/v1/lexicon/${grammarId}/items/${currentLexiconId}/num-links/${row.id}`, {
        memo: row.memo,
        slot_no: row.slot_no ?? null,
        idx_value: row.idx_value,
        comment: row.comment
      });
      await refreshSelectedItemSidePanels(currentLexiconId);
      setMessage("num紐付けを更新しました。");
    });
  }

  async function handleDeleteNumLink(linkId: number) {
    if (!hasSelectedItem) {
      return;
    }
    await runTask(async () => {
      await apiDelete<{ deleted: boolean }>(`/v1/lexicon/${grammarId}/items/${currentLexiconId}/num-links/${linkId}`);
      await refreshSelectedItemSidePanels(currentLexiconId);
      setMessage("num紐付けを削除しました。");
    });
  }

  async function handleSaveNote() {
    if (!hasSelectedItem) {
      return;
    }
    await runTask(async () => {
      const response = await apiPut<NoteCurrentResponse>(`/v1/lexicon/${grammarId}/items/${currentLexiconId}/notes`, {
        markdown: noteMarkdown,
        author: noteAuthor,
        change_summary: noteSummary
      });
      setNoteUpdatedAt(response.updated_at || null);
      await refreshSelectedItemSidePanels(currentLexiconId);
      setNoteSummary("");
      setMessage("研究メモを保存しました。");
    });
  }

  async function handleOpenRevision(revisionId: number) {
    if (!hasSelectedItem) {
      return;
    }
    await runTask(async () => {
      const response = await apiGet<NoteRevisionResponse>(
        `/v1/lexicon/${grammarId}/items/${currentLexiconId}/notes/revisions/${revisionId}`
      );
      setSelectedRevisionBody(response);
    });
  }

  async function handleRestoreRevision(revisionId: number) {
    if (!hasSelectedItem) {
      return;
    }
    await runTask(async () => {
      const response = await apiPost<NoteCurrentResponse>(
        `/v1/lexicon/${grammarId}/items/${currentLexiconId}/notes/revisions/${revisionId}/restore`,
        {}
      );
      setNoteMarkdown(response.markdown);
      setNoteUpdatedAt(response.updated_at || null);
      await refreshSelectedItemSidePanels(currentLexiconId);
      setMessage("履歴を復元しました。");
    });
  }

  async function handleLoadDiff() {
    if (!selectedRevisionId) {
      return;
    }
    await runTask(async () => {
      if (selectedRevisionId === "working-tree-current") {
        const response = await apiGet<LexiconExportResponse>(`/v1/lexicon/${grammarId}?format=${diffFormat}`);
        setVersionDiffText(response.content_text);
        return;
      }
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
      await Promise.all([
        refreshItems(page, query, sortKey, sortOrder),
        refreshVersions(versionOffset),
        refreshAllIdslotValues()
      ]);
      setMessage("Lexiconを保存しました。");
    });
  }

  return (
    <div className="lexicon-workbench" data-testid="lexicon-workbench">
      <div className="lexicon-workbench-header">
        <h2>語彙の編集</h2>
        <p className="hint">
          タブで「語彙項目一覧 / 語彙項目編集 / バリュー辞書 / CSV/YAML管理」を切り替えます。検索は
          <code>category:iA</code> 形式にも対応します。
        </p>
      </div>

      {error && <p className="alert">{error}</p>}
      {message && <p className="hint">{message}</p>}

      <div className="row lexicon-main-tab-row">
        <button
          type="button"
          className={activeTopTab === "items" ? "renew-step-btn active" : "renew-step-btn"}
          onClick={() => setActiveTopTab("items")}
        >
          語彙項目一覧
        </button>
        <button
          type="button"
          className={activeTopTab === "edit" ? "renew-step-btn active" : "renew-step-btn"}
          onClick={() => setActiveTopTab("edit")}
        >
          語彙項目編集
        </button>
        <button
          type="button"
          className={activeTopTab === "dictionary" ? "renew-step-btn active" : "renew-step-btn"}
          onClick={() => setActiveTopTab("dictionary")}
        >
          バリュー辞書
        </button>
        <button
          type="button"
          className={activeTopTab === "importexport" ? "renew-step-btn active" : "renew-step-btn"}
          onClick={() => setActiveTopTab("importexport")}
        >
          CSV/YAML管理
        </button>
      </div>

      {activeTopTab === "items" && (
        <section className="lexicon-pane" data-testid="lexicon-items-tab">
          <div className="lexicon-pane-header">
            <h3>語彙項目一覧</h3>
            <button
              type="button"
              onClick={() => void runTask(() => refreshItems(page, query, sortKey, sortOrder))}
              disabled={loading}
            >
              再読込
            </button>
          </div>
          <div className="row">
            <input
              aria-label="Lexicon Search"
              placeholder="entry/phono/id を部分一致検索。例: category:iA"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  void handleSearchItems();
                }
              }}
            />
            <button type="button" disabled={loading} onClick={() => void handleSearchItems()}>
              検索
            </button>
          </div>
          <div className="inspect-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>
                    <button
                      type="button"
                      className="lexicon-sort-btn"
                      onClick={() => void handleToggleSort("lexicon_id")}
                    >
                      id <span className="lexicon-sort-arrow">{sortArrow("lexicon_id")}</span>
                    </button>
                  </th>
                  <th>
                    <button type="button" className="lexicon-sort-btn" onClick={() => void handleToggleSort("entry")}>
                      entry <span className="lexicon-sort-arrow">{sortArrow("entry")}</span>
                    </button>
                  </th>
                  <th>
                    <button
                      type="button"
                      className="lexicon-sort-btn"
                      onClick={() => void handleToggleSort("category")}
                    >
                      category <span className="lexicon-sort-arrow">{sortArrow("category")}</span>
                    </button>
                  </th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {(itemsPage?.items || []).map((row) => {
                  const id = Number(row.lexicon_id);
                  const isActive = id === selectedListLexiconId;
                  return (
                    <tr
                      key={`lex-row-${row.lexicon_id}`}
                      className={isActive ? "lexicon-row-active" : ""}
                      onClick={() => setSelectedListLexiconId(id)}
                    >
                      <td>{row.lexicon_id}</td>
                      <td>{row.entry}</td>
                      <td>{row.category}</td>
                      <td className="lexicon-row-action-cell">
                        {isActive && (
                          <button
                            type="button"
                            className="lexicon-row-edit-btn"
                            disabled={loading}
                            onClick={(event) => {
                              event.stopPropagation();
                              void openItemForEdit(id);
                            }}
                          >
                            編集
                          </button>
                        )}
                      </td>
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
                  await refreshItems(page - 1, query, sortKey, sortOrder);
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
                  await refreshItems(page + 1, query, sortKey, sortOrder);
                });
              }}
            >
              次へ
            </button>
          </div>
        </section>
      )}

      {activeTopTab === "edit" && (
        <section className="lexicon-pane" data-testid="lexicon-edit-tab">
          <div className="lexicon-pane-header">
            <h3>語彙項目編集</h3>
            <div className="row">
              <button type="button" onClick={() => void startNewItem()} disabled={loading}>
                新規作成
              </button>
              <button type="button" onClick={() => void handleSaveItem()} disabled={loading}>
                保存
              </button>
              <button type="button" onClick={() => void handleDeleteItem()} disabled={loading || !hasSelectedItem}>
                削除
              </button>
            </div>
          </div>

          {!hasSelectedItem && !isNewItem && (
            <p className="hint">語彙項目一覧で項目を選択して「編集」を押すと、ここで詳細を編集できます。</p>
          )}

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
              id_slot
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

          <div className="lexicon-multi-field" data-testid="lexicon-numlinks-embedded">
            <div className="lexicon-multi-header">
              <h4>num紐付け</h4>
            </div>
            {!hasSelectedItem ? (
              <p className="hint">保存済みの語彙項目を選択すると設定できます。</p>
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
                <button
                  type="button"
                  onClick={() => void handleCreateNumLink()}
                  disabled={loading || !numLinkForm.num_path.trim()}
                >
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

          <div className="lexicon-multi-field" data-testid="lexicon-notes-embedded">
            <div className="lexicon-multi-header">
              <h4>研究メモ（Markdown）</h4>
            </div>
            {!hasSelectedItem ? (
              <p className="hint">保存済みの語彙項目を選択すると設定できます。</p>
            ) : (
              <>
                <div className="lexicon-note-editor-grid">
                  <label>
                    markdown
                    <textarea
                      aria-label="note-markdown-input"
                      rows={12}
                      value={noteMarkdown}
                      onChange={(event) => setNoteMarkdown(event.target.value)}
                    />
                  </label>
                  <div className="lexicon-markdown-preview">
                    <div className="lexicon-markdown-preview-title">プレビュー</div>
                    <div className="lexicon-markdown-preview-body">{renderMarkdownPreview(noteMarkdown)}</div>
                  </div>
                </div>
                <div className="row">
                  <label>
                    author
                    <input value={noteAuthor} onChange={(event) => setNoteAuthor(event.target.value)} />
                  </label>
                  <label>
                    change summary
                    <input value={noteSummary} onChange={(event) => setNoteSummary(event.target.value)} />
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
                {selectedRevisionBody && <pre className="mono">{selectedRevisionBody.markdown}</pre>}
              </>
            )}
          </div>

          <div className="lexicon-multi-field" data-testid="lexicon-item-versions-embedded">
            <div className="lexicon-multi-header">
              <h4>版管理（語彙項目単位）</h4>
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
            </div>
            <p className="hint">
              選択中語彙ID: {hasSelectedItem ? currentLexiconId : "(未選択)"} / 現在CSVを基準に版管理を開始しています。
            </p>
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
                  {effectiveVersionItems.map((row) => (
                    <tr
                      key={`version-${row.revision_id}`}
                      className={selectedRevisionId === row.revision_id ? "lexicon-row-active" : ""}
                      onClick={() => setSelectedRevisionId(row.revision_id)}
                    >
                      <td>{row.revision_id === "working-tree-current" ? "current" : row.revision_id.slice(0, 12)}</td>
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
            <pre className="mono" data-testid="lexicon-version-diff-output">
              {scopedVersionDiff}
            </pre>
          </div>
        </section>
      )}

      {activeTopTab === "dictionary" && (
        <section className="lexicon-pane" data-testid="lexicon-dictionary-tab">
          <div className="lexicon-pane-header">
            <h3>バリュー辞書</h3>
            <button type="button" onClick={() => void runTask(() => refreshDictionary(dictionaryKind))} disabled={loading}>
              更新
            </button>
          </div>
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
                      setDictionaryCreateValue(row.display_value);
                      setDictionaryReplaceTargetId(null);
                      setDictionaryUsage(null);
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
            値
            <input
              aria-label="dictionary-new-value"
              value={dictionaryCreateValue}
              onChange={(event) => setDictionaryCreateValue(event.target.value)}
            />
          </label>
          <div className="row">
            <button
              type="button"
              onClick={() => void handleCreateDictionaryValue()}
              disabled={loading || !canCreateDictionaryValue}
            >
              新規追加
            </button>
            <button
              type="button"
              onClick={() => void handleUpdateDictionaryValue()}
              disabled={loading || !canUpdateDictionaryValue}
            >
              更新
            </button>
            <button
              type="button"
              onClick={() => void handleDeleteDictionaryValue()}
              disabled={loading || selectedDictionaryId === null}
            >
              削除
            </button>
          </div>
          <div className="row">
            <button
              type="button"
              onClick={() => void handleLoadDictionaryUsage()}
              disabled={loading || selectedDictionaryId === null}
            >
              使用語彙を表示
            </button>
            <select
              aria-label="dictionary-replace-target"
              value={dictionaryReplaceTargetId ?? ""}
              onChange={(event) => setDictionaryReplaceTargetId(event.target.value ? Number(event.target.value) : null)}
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
            <p className="hint">
              選択中: {selectedDictionaryItem.display_value}
              {" / "}
              source: {dictionarySource}
            </p>
          )}
          {dictionaryUsage && (
            <>
              <p className="hint">
                total_usages: {dictionaryUsage.total_usages}
                {" / "}
                source: {dictionaryUsage.source || dictionarySource}
              </p>
              <div className="inspect-table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>grammar</th>
                      <th>lexicon_id</th>
                      <th>entry</th>
                      <th>category</th>
                      <th>matches</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dictionaryUsage.usage_lexicon_items.map((row) => (
                      <tr key={`dict-usage-${row.grammar_id}-${row.lexicon_id}`}>
                        <td>{row.grammar_id}</td>
                        <td>{row.lexicon_id}</td>
                        <td>{row.entry}</td>
                        <td>{row.category}</td>
                        <td>{row.match_count}</td>
                      </tr>
                    ))}
                    {dictionaryUsage.usage_lexicon_items.length === 0 && (
                      <tr>
                        <td colSpan={5}>一致する語彙項目はありません。</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </section>
      )}

      {activeTopTab === "importexport" && (
        <section className="lexicon-pane" data-testid="lexicon-importexport-tab">
          <h3>CSV/YAML管理</h3>
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
          <pre className="mono" data-testid="lexicon-importexport-output">
            {importExportText}
          </pre>
          <label>
            YAML入力
            <textarea
              aria-label="lexicon-yaml-input"
              rows={8}
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
          <pre className="mono" data-testid="lexicon-csv-preview-output">
            {csvPreview}
          </pre>
        </section>
      )}
    </div>
  );
}
