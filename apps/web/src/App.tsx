import { useEffect, useMemo, useRef, useState } from "react";
import { apiGet, apiPost, parseManualTokens } from "./api";
import type {
  DerivationState,
  FeatureDocEntry,
  GeneratedNumeration,
  GrammarRuleSourceEntry,
  GrammarRuleSourceResponse,
  GrammarOption,
  HtmlDocResponse,
  LexiconCommitResponse,
  LexiconExportResponse,
  LexiconImportResponse,
  LexiconValidateResponse,
  LfResponse,
  NumerationFileEntry,
  ObservationTreeResponse,
  RuleCandidate,
  RuleDocEntry,
  SrResponse
} from "./types";

type SnapshotSlot = "T0" | "T1" | "T2";
type BranchSlot = "A" | "B";
type TreeMode = "tree" | "tree_cat";
type UiMode = "legacy" | "renewed";
type TokenInputMode = "manual" | "auto";
type Step1HelpKey = "generate_num" | "init_from_sentence" | "init_from_num";
type RenewMenu = "hypothesis" | "reference" | "lexicon";
type RenewPanel =
  | "sentence"
  | "numeration"
  | "target"
  | "observation"
  | "resume"
  | "reference"
  | "lexicon";

type TokenSlotEdit = {
  slot: number;
  token: string;
  selectedLexiconId: number;
  candidateLexiconIds: number[];
  plusValue: string;
  idxValue: string;
};

type ArrangeRow = {
  slot: number;
  lexiconId: string;
  plusValue: string;
  idxValue: string;
};

type RenderNode = {
  id: string;
  x: number;
  y: number;
  labelLines: string[];
};

type RenderEdge = {
  from: string;
  to: string;
  color: string;
};

type TreeRenderModel = {
  nodes: RenderNode[];
  edges: RenderEdge[];
  width: number;
  height: number;
};

const DEFAULT_GRAMMARS: GrammarOption[] = [
  { grammar_id: "imi01", folder: "imi01", uses_lexicon_all: true, display_name: "imi01" },
  { grammar_id: "imi02", folder: "imi02", uses_lexicon_all: true, display_name: "imi02" },
  { grammar_id: "imi03", folder: "imi03", uses_lexicon_all: true, display_name: "imi03" },
  {
    grammar_id: "japanese2",
    folder: "japanese2",
    uses_lexicon_all: false,
    display_name: "japanese2"
  }
];

const RENEW_MENUS: Array<{
  key: RenewMenu;
  label: string;
  steps: Array<{ key: RenewPanel; label: string }>;
}> = [
  {
    key: "hypothesis",
    label: "仮説検証ステップ",
    steps: [
      { key: "sentence", label: "Step 1 入力" },
      { key: "numeration", label: "Step 2 Numeration" },
      { key: "target", label: "Step 3 Target/Rule" },
      { key: "observation", label: "Step 4 観察" },
      { key: "resume", label: "Step 5 保存/再開" }
    ]
  },
  {
    key: "reference",
    label: "素性とルールの確認",
    steps: [{ key: "reference", label: "Feature/Rule 参照" }]
  },
  {
    key: "lexicon",
    label: "語彙の編集",
    steps: [{ key: "lexicon", label: "Lexicon" }]
  }
];

function cloneState(state: DerivationState | null): DerivationState | null {
  if (!state) {
    return null;
  }
  return JSON.parse(JSON.stringify(state)) as DerivationState;
}

function parseNumerationText(text: string): {
  memo: string;
  lexicon: string[];
  plus: string[];
  idx: string[];
} {
  const lines = text.split(/\r?\n/);
  const row1 = (lines[0] || "").split("\t");
  const row2 = (lines[1] || "").split("\t");
  const row3 = (lines[2] || "").split("\t");

  const lexicon = Array.from({ length: 30 }, (_, i) => row1[i + 1] || "");
  const plus = Array.from({ length: 30 }, (_, i) => row2[i + 1] || "");
  const idx = Array.from({ length: 30 }, (_, i) => row3[i + 1] || "");

  return {
    memo: row1[0] || "",
    lexicon,
    plus,
    idx
  };
}

function buildNumerationText(memo: string, lexicon: string[], plus: string[], idx: string[]): string {
  const line1 = [memo, ...lexicon.slice(0, 30)];
  const line2 = [" ", ...plus.slice(0, 30)];
  const line3 = [" ", ...idx.slice(0, 30)];
  return `${line1.join("\t")}\n${line2.join("\t")}\n${line3.join("\t")}`;
}

function deriveStatus(state: DerivationState | null): "grammatical" | "ungrammatical" | "-" {
  if (!state) {
    return "-";
  }
  const body = JSON.stringify(state.base);
  return /,[0-9]/.test(body) ? "ungrammatical" : "grammatical";
}

function formatGrammarOption(option: GrammarOption): string {
  const display = option.display_name.trim();
  if (display === "" || display === option.grammar_id) {
    return option.grammar_id;
  }
  return `${display} (${option.grammar_id})`;
}

const TOKEN_CHIP_COLORS = [
  "#ffe1e6",
  "#ffe9d2",
  "#fff2ba",
  "#dff6e3",
  "#dcf2ff",
  "#e7e6ff",
  "#f6ddff"
];

const STEP1_HELP_CONTENT: Record<Step1HelpKey, string> = {
  generate_num:
    "観察文を分割して語彙候補を解決し、.num テキストだけを更新します。T0 はまだ作りません。",
  init_from_sentence:
    "観察文から .num を生成した直後に、その .num を使って T0（規則適用前の初期状態）を作ります。最初の派生観察を始める標準操作です。",
  init_from_num:
    "すでに用意済みの .num テキストを使って T0（規則適用前の初期状態）を作ります。語彙選択や .num 編集の再利用時に使います。"
};

const T0_BRIEF_DESCRIPTION =
  "T0 は規則適用前の最初の派生状態です。Step3 の候補探索や規則実行は、この T0 を起点に進みます。";

const LEGACY_PERL_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL?.trim() || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

function toDisplayLines(value: unknown): string[] {
  const raw = String(value)
    .replace(/&lt;br&gt;/g, "\n")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&");
  return raw.split("\n");
}

function buildTreeRenderModel(csvText: string): { model: TreeRenderModel; dotText: string } {
  const nodeLabels = new Map<string, string>();
  const nodeFlags = new Map<string, string>();
  const children = new Map<string, string[]>();
  const parents = new Map<string, string>();

  const lines = csvText
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0);

  for (const line of lines) {
    const cols = line.split(",", 4);
    if (cols.length !== 4) {
      continue;
    }
    const [node, edgeRaw, flag, label] = cols;
    nodeLabels.set(node, label);
    nodeFlags.set(node, flag);

    const edgeList = edgeRaw
      .split(" ")
      .map((item) => item.trim())
      .filter((item) => item.length > 0);
    children.set(node, edgeList);
    for (const child of edgeList) {
      parents.set(child, node);
    }
  }

  const roots = Array.from(nodeLabels.keys()).filter((node) => !parents.has(node));
  const orderedRoots = roots.length > 0 ? roots : Array.from(nodeLabels.keys());

  const depthByNode = new Map<string, number>();
  const queue: string[] = [...orderedRoots];
  for (const root of orderedRoots) {
    depthByNode.set(root, 0);
  }
  while (queue.length > 0) {
    const current = queue.shift() as string;
    const currentDepth = depthByNode.get(current) || 0;
    for (const child of children.get(current) || []) {
      if (!depthByNode.has(child)) {
        depthByNode.set(child, currentDepth + 1);
        queue.push(child);
      }
    }
  }

  const nodesByDepth = new Map<number, string[]>();
  for (const node of nodeLabels.keys()) {
    const depth = depthByNode.get(node) || 0;
    const arr = nodesByDepth.get(depth) || [];
    arr.push(node);
    nodesByDepth.set(depth, arr);
  }

  const sortedDepths = Array.from(nodesByDepth.keys()).sort((a, b) => a - b);
  for (const depth of sortedDepths) {
    nodesByDepth.get(depth)?.sort((a, b) => Number(a) - Number(b));
  }

  const xSpacing = 180;
  const ySpacing = 120;
  const nodeWidth = 140;
  const maxPerDepth = Math.max(...Array.from(nodesByDepth.values()).map((rows) => rows.length), 1);
  const width = Math.max(420, maxPerDepth * xSpacing + 80);
  const height = Math.max(240, sortedDepths.length * ySpacing + 80);

  const renderNodes: RenderNode[] = [];
  const position = new Map<string, { x: number; y: number }>();

  for (const depth of sortedDepths) {
    const rows = nodesByDepth.get(depth) || [];
    rows.forEach((nodeId, index) => {
      const x = 40 + index * xSpacing;
      const y = 40 + depth * ySpacing;
      position.set(nodeId, { x, y });
      renderNodes.push({
        id: nodeId,
        x,
        y,
        labelLines: toDisplayLines(nodeLabels.get(nodeId) || "")
      });
    });
  }

  const renderEdges: RenderEdge[] = [];
  for (const [from, edgeList] of children.entries()) {
    for (const to of edgeList) {
      const color = nodeFlags.get(to) === "1" ? "#cc0000" : "#222";
      renderEdges.push({ from, to, color });
    }
  }

  let dot = "graph {";
  for (const [node, label] of nodeLabels.entries()) {
    const escaped = label.replace(/"/g, '\\"');
    dot += `${node} [label="${escaped}"];`;
  }
  for (const edge of renderEdges) {
    dot += `${edge.from}--${edge.to}`;
    if (edge.color === "#cc0000") {
      dot += " [color=red]";
    }
    dot += ";";
  }
  dot += "}";

  return {
    model: {
      nodes: renderNodes,
      edges: renderEdges,
      width: width + nodeWidth,
      height
    },
    dotText: dot.replace(/;/g, ";\n")
  };
}

function renderBaseItem(item: unknown, depth = 0): JSX.Element {
  if (!Array.isArray(item)) {
    return <div className="mono">{String(item)}</div>;
  }

  const lexicalId = String(item[0] ?? "");
  const category = String(item[1] ?? "");
  const predicates = Array.isArray(item[2]) ? (item[2] as unknown[]) : [];
  const syntax = Array.isArray(item[3]) ? (item[3] as unknown[]) : [];
  const idslot = String(item[4] ?? "");
  const semantics = Array.isArray(item[5]) ? (item[5] as unknown[]) : [];
  const phono = String(item[6] ?? "");
  const daughters = Array.isArray(item[7]) ? (item[7] as unknown[]) : [];
  const note = String(item[8] ?? "");

  return (
    <div style={{ marginLeft: depth * 14 }}>
      <div className="mono">
        [{lexicalId}] ca={category} ph={phono} sl={idslot}
      </div>
      {syntax.length > 0 && <div className="mono">sy: {syntax.map((v) => String(v)).join(" | ")}</div>}
      {semantics.length > 0 && (
        <div className="mono">se: {semantics.map((v) => String(v)).join(" | ")}</div>
      )}
      {predicates.length > 0 && (
        <div className="mono">pr: {predicates.map((v) => JSON.stringify(v)).join(" | ")}</div>
      )}
      {note !== "" && <div className="mono">nb: {note}</div>}
      {daughters.length > 0 && (
        <div>
          {daughters.map((daughter, index) => (
            <div key={`${lexicalId}-${depth}-${index}`}>
              {daughter === "zero" ? (
                <div className="mono" style={{ marginLeft: (depth + 1) * 14 }}>
                  trace: zero
                </div>
              ) : (
                renderBaseItem(daughter, depth + 1)
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [uiMode, setUiMode] = useState<UiMode>("renewed");
  const [legacyFrameReloadTick, setLegacyFrameReloadTick] = useState(0);
  const [renewMenu, setRenewMenu] = useState<RenewMenu>("hypothesis");
  const [renewPanel, setRenewPanel] = useState<RenewPanel>("sentence");

  const [grammarOptions, setGrammarOptions] = useState<GrammarOption[]>(DEFAULT_GRAMMARS);
  const [grammarId, setGrammarId] = useState("imi03");
  const [sentence, setSentence] = useState("ジョンが本を読んだ");
  const [tokenInputMode, setTokenInputMode] = useState<TokenInputMode>("manual");
  const [manualTokensInput, setManualTokensInput] = useState("ジョン が 本 を 読んだ");
  const [splitMode, setSplitMode] = useState("C");
  const [autoPreviewTokens, setAutoPreviewTokens] = useState<string[]>([]);
  const [autoPreviewLoading, setAutoPreviewLoading] = useState(false);
  const [openStep1Help, setOpenStep1Help] = useState<Step1HelpKey | null>(null);

  const [uploadNumerationText, setUploadNumerationText] = useState("");
  const [numerationText, setNumerationText] = useState("");
  const [setNumerationFiles, setSetNumerationFiles] = useState<NumerationFileEntry[]>([]);
  const [savedNumerationFiles, setSavedNumerationFiles] = useState<NumerationFileEntry[]>([]);
  const [selectedSetPath, setSelectedSetPath] = useState("");
  const [selectedSavedPath, setSelectedSavedPath] = useState("");

  const [arrangeRows, setArrangeRows] = useState<ArrangeRow[]>([]);
  const [tokenSlotEdits, setTokenSlotEdits] = useState<TokenSlotEdit[]>([]);

  const [generated, setGenerated] = useState<GeneratedNumeration | null>(null);
  const [state, setState] = useState<DerivationState | null>(null);
  const [candidates, setCandidates] = useState<RuleCandidate[]>([]);
  const [left, setLeft] = useState("1");
  const [right, setRight] = useState("2");
  const [selectedLeft, setSelectedLeft] = useState<number | null>(null);
  const [selectedRight, setSelectedRight] = useState<number | null>(null);

  const [treeCsv, setTreeCsv] = useState("");
  const [treeCatCsv, setTreeCatCsv] = useState("");
  const [activeTreeMode, setActiveTreeMode] = useState<TreeMode>("tree");
  const [treeSourceCsv, setTreeSourceCsv] = useState("");
  const [treeDot, setTreeDot] = useState("");
  const [treeGraph, setTreeGraph] = useState<TreeRenderModel | null>(null);

  const [lfRows, setLfRows] = useState<LfResponse["list_representation"]>([]);
  const [srRows, setSrRows] = useState<SrResponse["truth_conditional_meaning"]>([]);

  const [featureDocs, setFeatureDocs] = useState<FeatureDocEntry[]>([]);
  const [selectedFeatureDoc, setSelectedFeatureDoc] = useState("");
  const [featureDocHtml, setFeatureDocHtml] = useState("");
  const [ruleDocs, setRuleDocs] = useState<RuleDocEntry[]>([]);
  const [selectedRuleDoc, setSelectedRuleDoc] = useState("");
  const [ruleDocHtml, setRuleDocHtml] = useState("");
  const [referenceDocsLoadedGrammarId, setReferenceDocsLoadedGrammarId] = useState("");
  const [grammarRuleSources, setGrammarRuleSources] = useState<GrammarRuleSourceEntry[]>([]);
  const [selectedGrammarRuleNumber, setSelectedGrammarRuleNumber] = useState<number | null>(null);
  const [grammarRuleSourceText, setGrammarRuleSourceText] = useState("");
  const [grammarRuleSourceFileName, setGrammarRuleSourceFileName] = useState("");
  const [grammarRuleSourceMessage, setGrammarRuleSourceMessage] = useState("");

  const [resumeText, setResumeText] = useState("");
  const [lexiconFormat, setLexiconFormat] = useState<"yaml" | "csv">("yaml");
  const [lexiconPath, setLexiconPath] = useState("");
  const [lexiconEntryCount, setLexiconEntryCount] = useState<number>(0);
  const [lexiconText, setLexiconText] = useState("");
  const [lexiconYamlInput, setLexiconYamlInput] = useState("");
  const [lexiconValidateErrors, setLexiconValidateErrors] = useState<string[]>([]);
  const [lexiconCsvPreview, setLexiconCsvPreview] = useState("");
  const [runLexiconCompatibilityTests, setRunLexiconCompatibilityTests] = useState(true);
  const [lexiconCommitMessage, setLexiconCommitMessage] = useState("");
  const [lexiconCommitStdout, setLexiconCommitStdout] = useState("");
  const [lexiconCommitStderr, setLexiconCommitStderr] = useState("");

  const [snapshots, setSnapshots] = useState<Record<SnapshotSlot, DerivationState | null>>({
    T0: null,
    T1: null,
    T2: null
  });
  const [branches, setBranches] = useState<Record<BranchSlot, DerivationState | null>>({
    A: null,
    B: null
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const referenceSectionRef = useRef<HTMLElement | null>(null);
  const step1ActionRowRef = useRef<HTMLDivElement | null>(null);
  const autoPreviewRequestSeqRef = useRef(0);

  const manualTokens = useMemo(() => parseManualTokens(manualTokensInput), [manualTokensInput]);
  const grammarStatus = useMemo(() => deriveStatus(state), [state]);
  const activeGrammarOption = useMemo(
    () => grammarOptions.find((option) => option.grammar_id === grammarId),
    [grammarOptions, grammarId]
  );
  const displayedTokens = useMemo(() => {
    if (tokenInputMode === "auto") {
      return autoPreviewTokens;
    }
    return manualTokens ?? [];
  }, [autoPreviewTokens, manualTokens, tokenInputMode]);
  const selectedGrammarRule = useMemo(
    () =>
      grammarRuleSources.find((row) => row.rule_number === selectedGrammarRuleNumber) || null,
    [grammarRuleSources, selectedGrammarRuleNumber]
  );

  async function withLoading(task: () => Promise<void>) {
    setLoading(true);
    setError(null);
    try {
      await task();
    } catch (taskError) {
      setError(taskError instanceof Error ? taskError.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function refreshAutoTokenPreview() {
    if (tokenInputMode !== "auto" || sentence.trim() === "") {
      setAutoPreviewTokens([]);
      setAutoPreviewLoading(false);
      return;
    }
    const seq = autoPreviewRequestSeqRef.current + 1;
    autoPreviewRequestSeqRef.current = seq;
    setAutoPreviewLoading(true);
    try {
      const response = await apiPost<{ tokens: string[] }>("/v1/derivation/numeration/tokenize", {
        grammar_id: grammarId,
        sentence,
        split_mode: splitMode
      });
      if (autoPreviewRequestSeqRef.current !== seq) {
        return;
      }
      setAutoPreviewTokens(response.tokens);
    } catch {
      if (autoPreviewRequestSeqRef.current !== seq) {
        return;
      }
      setAutoPreviewTokens([]);
      // 自動プレビュー失敗は観察用の補助機能なので、全体エラー表示には出さない。
      setError(null);
    } finally {
      if (autoPreviewRequestSeqRef.current === seq) {
        setAutoPreviewLoading(false);
      }
    }
  }

  function syncTokenEdits(response: GeneratedNumeration) {
    const edits: TokenSlotEdit[] = response.token_resolutions.map((row, index) => ({
      slot: index + 1,
      token: row.token,
      selectedLexiconId: row.lexicon_id,
      candidateLexiconIds: row.candidate_lexicon_ids,
      plusValue: "",
      idxValue: String(index + 1)
    }));
    setTokenSlotEdits(edits);
  }

  function applyTreeConversion(source: string) {
    const { model, dotText } = buildTreeRenderModel(source);
    setTreeGraph(model);
    setTreeDot(dotText);
  }

  async function handleLoadAllGrammars() {
    await withLoading(async () => {
      const rows = await apiGet<GrammarOption[]>("/v1/derivation/grammars");
      if (rows.length > 0) {
        setGrammarOptions(rows);
      }
    });
  }

  async function handleGenerate() {
    const tokensForRequest = tokenInputMode === "manual" ? manualTokens : undefined;
    await withLoading(async () => {
      const response = await apiPost<GeneratedNumeration>("/v1/derivation/numeration/generate", {
        grammar_id: grammarId,
        sentence,
        tokens: tokensForRequest,
        split_mode: splitMode
      });
      setGenerated(response);
      setNumerationText(response.numeration_text);
      syncTokenEdits(response);
      setArrangeRows([]);
    });
  }

  async function handleInitFromSentence() {
    const tokensForRequest = tokenInputMode === "manual" ? manualTokens : undefined;
    await withLoading(async () => {
      const response = await apiPost<{ numeration: GeneratedNumeration; state: DerivationState }>(
        "/v1/derivation/init/from-sentence",
        {
          grammar_id: grammarId,
          sentence,
          tokens: tokensForRequest,
          split_mode: splitMode
        }
      );
      setGenerated(response.numeration);
      setNumerationText(response.numeration.numeration_text);
      syncTokenEdits(response.numeration);
      setState(response.state);
      setSnapshots({ T0: cloneState(response.state), T1: null, T2: null });
      setCandidates([]);
      setTreeCsv("");
      setTreeCatCsv("");
      setTreeSourceCsv("");
      setTreeDot("");
      setTreeGraph(null);
      setLfRows([]);
      setSrRows([]);
      setArrangeRows([]);
      setSelectedLeft(null);
      setSelectedRight(null);
    });
  }

  async function handleInitFromNumerationText() {
    if (numerationText.trim() === "") {
      setError(".num テキストが空です。");
      return;
    }
    await withLoading(async () => {
      const response = await apiPost<DerivationState>("/v1/derivation/init", {
        grammar_id: grammarId,
        numeration_text: numerationText
      });
      setState(response);
      setSnapshots({ T0: cloneState(response), T1: null, T2: null });
      setCandidates([]);
      setTreeCsv("");
      setTreeCatCsv("");
      setTreeSourceCsv("");
      setTreeDot("");
      setTreeGraph(null);
      setLfRows([]);
      setSrRows([]);
      setSelectedLeft(null);
      setSelectedRight(null);
    });
  }

  async function handleLoadNumerationFiles(source: "set" | "saved") {
    await withLoading(async () => {
      const rows = await apiGet<NumerationFileEntry[]>(
        `/v1/derivation/numeration/files?grammar_id=${grammarId}&source=${source}`
      );
      if (source === "set") {
        setSetNumerationFiles(rows);
      } else {
        setSavedNumerationFiles(rows);
      }
    });
  }

  async function handleLoadNumerationPath(path: string) {
    if (path.trim() === "") {
      setError("読み込む .num ファイルを選択してください。");
      return;
    }
    await withLoading(async () => {
      const response = await apiPost<{ path: string; numeration_text: string; memo: string }>(
        "/v1/derivation/numeration/load",
        {
          grammar_id: grammarId,
          path
        }
      );
      setNumerationText(response.numeration_text);
      setSentence(response.memo || sentence);
      setArrangeRows([]);
    });
  }

  async function handleSaveNumeration() {
    if (numerationText.trim() === "") {
      setError("保存する .num テキストが空です。");
      return;
    }
    await withLoading(async () => {
      await apiPost<{ path: string }>("/v1/derivation/numeration/save", {
        grammar_id: grammarId,
        numeration_text: numerationText
      });
      await handleLoadNumerationFiles("saved");
    });
  }

  function handleApplyUploadNumeration() {
    if (uploadNumerationText.trim() === "") {
      setError("upload テキストが空です。");
      return;
    }
    setNumerationText(uploadNumerationText);
    setArrangeRows([]);
  }

  function handleArrangeFromCurrentNumeration() {
    const parsed = parseNumerationText(numerationText);
    const rows: ArrangeRow[] = [];
    for (let i = 0; i < 30; i += 1) {
      if (parsed.lexicon[i] === "") {
        continue;
      }
      rows.push({
        slot: i + 1,
        lexiconId: parsed.lexicon[i],
        plusValue: parsed.plus[i],
        idxValue: parsed.idx[i] || String(i + 1)
      });
    }
    setArrangeRows(rows);
  }

  function handleApplyArrangeToNumeration() {
    if (arrangeRows.length === 0) {
      setError("arrange 対象がありません。");
      return;
    }
    const parsed = parseNumerationText(numerationText);
    for (const row of arrangeRows) {
      const idx = row.slot - 1;
      parsed.lexicon[idx] = row.lexiconId;
      parsed.plus[idx] = row.plusValue;
      parsed.idx[idx] = row.idxValue;
    }
    setNumerationText(buildNumerationText(parsed.memo, parsed.lexicon, parsed.plus, parsed.idx));
  }

  async function handleComposeNumerationFromTokenSelection() {
    if (tokenSlotEdits.length === 0) {
      setError("候補再選択の対象がありません。先に Generate .num または Init T0 を実行してください。");
      return;
    }
    await withLoading(async () => {
      const response = await apiPost<{ numeration_text: string }>("/v1/derivation/numeration/compose", {
        memo: sentence.trim() === "" ? "manual" : sentence.trim(),
        lexicon_ids: tokenSlotEdits.map((row) => row.selectedLexiconId),
        plus_values: tokenSlotEdits.map((row) => row.plusValue),
        idx_values: tokenSlotEdits.map((row) => row.idxValue)
      });
      setNumerationText(response.numeration_text);
      if (generated) {
        setGenerated({
          ...generated,
          memo: sentence.trim() === "" ? generated.memo : sentence.trim(),
          lexicon_ids: tokenSlotEdits.map((row) => row.selectedLexiconId),
          token_resolutions: generated.token_resolutions.map((row, i) => ({
            ...row,
            lexicon_id: tokenSlotEdits[i]?.selectedLexiconId ?? row.lexicon_id
          })),
          numeration_text: response.numeration_text
        });
      }
    });
  }

  function updateTokenSlotEdit(slot: number, patch: Partial<TokenSlotEdit>) {
    setTokenSlotEdits((prev) => prev.map((row) => (row.slot === slot ? { ...row, ...patch } : row)));
  }

  function updateArrangeRow(slot: number, patch: Partial<ArrangeRow>) {
    setArrangeRows((prev) => prev.map((row) => (row.slot === slot ? { ...row, ...patch } : row)));
  }

  async function handleCandidates() {
    if (!state) {
      setError("T0 以降の state がありません。先に 初期化 を実行してください。");
      return;
    }

    const leftValue = selectedLeft ?? Number(left);
    const rightValue = selectedRight ?? Number(right);
    if (!Number.isInteger(leftValue) || !Number.isInteger(rightValue)) {
      setError("left/right は整数で指定してください。");
      return;
    }

    await withLoading(async () => {
      const response = await apiPost<RuleCandidate[]>("/v1/derivation/candidates", {
        state,
        left: leftValue,
        right: rightValue
      });
      setCandidates(response);
      setLeft(String(leftValue));
      setRight(String(rightValue));
    });
  }

  async function handleExecuteCandidate(candidate: RuleCandidate) {
    if (!state) {
      return;
    }
    await withLoading(async () => {
      const payload: Record<string, unknown> = {
        state,
        rule_name: candidate.rule_name
      };
      if (candidate.rule_kind === "single") {
        payload.check = candidate.check;
      } else {
        payload.left = candidate.left;
        payload.right = candidate.right;
      }
      const nextState = await apiPost<DerivationState>("/v1/derivation/execute", payload);
      setState(nextState);
      setCandidates([]);
      setSnapshots((prev) => {
        if (!prev.T1) {
          return { ...prev, T1: cloneState(nextState) };
        }
        return { ...prev, T2: cloneState(nextState) };
      });
    });
  }

  async function handleTree(mode: TreeMode) {
    if (!state) {
      setError("観察対象の state がありません。");
      return;
    }
    await withLoading(async () => {
      const response = await apiPost<ObservationTreeResponse>("/v1/observation/tree", {
        state,
        mode
      });
      if (mode === "tree") {
        setTreeCsv(response.csv_text);
      } else {
        setTreeCatCsv(response.csv_text);
      }
      setActiveTreeMode(mode);
      setTreeSourceCsv(response.csv_text);
      applyTreeConversion(response.csv_text);
    });
  }

  function handleTreeConvert() {
    applyTreeConversion(treeSourceCsv);
  }

  async function handleSemantics(mode: "lf" | "sr") {
    if (!state) {
      setError("観察対象の state がありません。");
      return;
    }
    await withLoading(async () => {
      if (mode === "lf") {
        const response = await apiPost<LfResponse>("/v1/semantics/lf", { state });
        setLfRows(response.list_representation);
      } else {
        const response = await apiPost<SrResponse>("/v1/semantics/sr", { state });
        setSrRows(response.truth_conditional_meaning);
      }
    });
  }

  async function handleLoadReferenceDocs() {
    await withLoading(async () => {
      const [featureRows, ruleRows] = await Promise.all([
        apiGet<FeatureDocEntry[]>("/v1/reference/features"),
        apiGet<RuleDocEntry[]>(`/v1/reference/rules/${grammarId}`)
      ]);
      setFeatureDocs(featureRows);
      setRuleDocs(ruleRows);

      const nextFeatureDoc =
        featureRows.find((row) => row.file_name === selectedFeatureDoc)?.file_name ||
        featureRows[0]?.file_name ||
        "";
      const nextRuleDoc =
        ruleRows.find((row) => row.file_name === selectedRuleDoc)?.file_name ||
        ruleRows[0]?.file_name ||
        "";

      setSelectedFeatureDoc(nextFeatureDoc);
      setSelectedRuleDoc(nextRuleDoc);

      const [featureDoc, ruleDoc] = await Promise.all([
        nextFeatureDoc
          ? apiGet<HtmlDocResponse>(`/v1/reference/features/${nextFeatureDoc}`)
          : Promise.resolve(null),
        nextRuleDoc
          ? apiGet<HtmlDocResponse>(`/v1/reference/rules/doc/${nextRuleDoc}`)
          : Promise.resolve(null)
      ]);
      setFeatureDocHtml(featureDoc?.html_text || "");
      setRuleDocHtml(ruleDoc?.html_text || "");
      setReferenceDocsLoadedGrammarId(grammarId);
    });
  }

  async function handleLoadFeatureDocs() {
    await handleLoadReferenceDocs();
  }

  async function handleOpenFeatureDoc(fileName: string) {
    if (fileName.trim() === "") {
      return;
    }
    await withLoading(async () => {
      const doc = await apiGet<HtmlDocResponse>(`/v1/reference/features/${fileName}`);
      setFeatureDocHtml(doc.html_text);
    });
  }

  async function handleLoadRuleDocs() {
    await handleLoadReferenceDocs();
  }

  async function handleOpenRuleDoc(fileName: string) {
    if (fileName.trim() === "") {
      return;
    }
    await withLoading(async () => {
      const doc = await apiGet<HtmlDocResponse>(`/v1/reference/rules/doc/${fileName}`);
      setRuleDocHtml(doc.html_text);
    });
  }

  async function handleLoadGrammarRuleSources() {
    await withLoading(async () => {
      const rows = await apiGet<GrammarRuleSourceEntry[]>(
        `/v1/reference/grammars/${grammarId}/rule-sources`
      );
      setGrammarRuleSources(rows);
      setGrammarRuleSourceMessage(
        rows.length > 0
          ? `ルール一覧を読み込みました（${rows.length}件）`
          : "ルール一覧は空です。"
      );
      if (rows.length > 0) {
        const first = rows[0];
        setSelectedGrammarRuleNumber(first.rule_number);
        const response = await apiGet<GrammarRuleSourceResponse>(
          `/v1/reference/grammars/${grammarId}/rule-sources/${first.rule_number}`
        );
        setGrammarRuleSourceText(response.source_text);
        setGrammarRuleSourceFileName(response.file_name);
      } else {
        setSelectedGrammarRuleNumber(null);
        setGrammarRuleSourceText("");
        setGrammarRuleSourceFileName("");
      }
    });
  }

  async function handleOpenGrammarRuleSource(ruleNumber: number) {
    await withLoading(async () => {
      const response = await apiGet<GrammarRuleSourceResponse>(
        `/v1/reference/grammars/${grammarId}/rule-sources/${ruleNumber}`
      );
      setSelectedGrammarRuleNumber(ruleNumber);
      setGrammarRuleSourceText(response.source_text);
      setGrammarRuleSourceFileName(response.file_name);
      setGrammarRuleSourceMessage("");
    });
  }

  async function handleSaveGrammarRuleSource() {
    if (!selectedGrammarRuleNumber) {
      setError("保存対象のルールを選択してください。");
      return;
    }
    await withLoading(async () => {
      const response = await apiPost<GrammarRuleSourceResponse>(
        `/v1/reference/grammars/${grammarId}/rule-sources/${selectedGrammarRuleNumber}`,
        { source_text: grammarRuleSourceText }
      );
      setGrammarRuleSourceFileName(response.file_name);
      setGrammarRuleSourceText(response.source_text);
      setGrammarRuleSourceMessage(`保存しました: ${response.file_name}`);
    });
  }

  async function handleResumeExport() {
    if (!state) {
      setError("エクスポート対象の state がありません。");
      return;
    }
    await withLoading(async () => {
      const response = await apiPost<{ resume_text: string }>("/v1/derivation/resume/export", {
        state
      });
      setResumeText(response.resume_text);
    });
  }

  async function handleResumeImport() {
    await withLoading(async () => {
      const response = await apiPost<DerivationState>("/v1/derivation/resume/import", {
        resume_text: resumeText
      });
      setState(response);
    });
  }

  async function handleLoadLexicon() {
    await withLoading(async () => {
      const response = await apiGet<LexiconExportResponse>(
        `/v1/lexicon/${grammarId}?format=${lexiconFormat}`
      );
      setLexiconPath(response.lexicon_path);
      setLexiconEntryCount(response.entry_count);
      setLexiconText(response.content_text);
      if (response.format === "yaml") {
        setLexiconYamlInput(response.content_text);
      }
      setLexiconValidateErrors([]);
      setLexiconCsvPreview("");
      setLexiconCommitMessage("");
      setLexiconCommitStdout("");
      setLexiconCommitStderr("");
    });
  }

  async function handleValidateLexiconYaml() {
    await withLoading(async () => {
      const response = await apiPost<LexiconValidateResponse>(`/v1/lexicon/${grammarId}/validate`, {
        yaml_text: lexiconYamlInput
      });
      setLexiconEntryCount(response.entry_count);
      setLexiconValidateErrors(response.errors);
      if (response.valid) {
        setLexiconText(response.normalized_yaml_text);
        setLexiconCsvPreview(response.preview_csv_text);
      } else {
        setLexiconCsvPreview("");
      }
      setLexiconCommitMessage("");
      setLexiconCommitStdout("");
      setLexiconCommitStderr("");
    });
  }

  async function handleImportLexiconYaml() {
    await withLoading(async () => {
      const response = await apiPost<LexiconImportResponse>(`/v1/lexicon/${grammarId}/import`, {
        yaml_text: lexiconYamlInput
      });
      setLexiconEntryCount(response.entry_count);
      setLexiconText(response.normalized_yaml_text);
      setLexiconCsvPreview(response.csv_text);
      setLexiconValidateErrors([]);
      setLexiconCommitMessage("");
      setLexiconCommitStdout("");
      setLexiconCommitStderr("");
    });
  }

  async function handleCommitLexiconYaml() {
    await withLoading(async () => {
      const response = await apiPost<LexiconCommitResponse>(`/v1/lexicon/${grammarId}/commit`, {
        yaml_text: lexiconYamlInput,
        run_compatibility_tests: runLexiconCompatibilityTests
      });
      setLexiconEntryCount(response.entry_count);
      setLexiconText(response.normalized_yaml_text);
      setLexiconCsvPreview(response.committed_csv_text);
      setLexiconValidateErrors(response.errors);
      setLexiconPath(response.lexicon_path || lexiconPath);
      setLexiconCommitMessage(response.message);
      setLexiconCommitStdout(response.stdout);
      setLexiconCommitStderr(response.stderr);
    });
  }

  function saveSnapshot(slot: SnapshotSlot) {
    setSnapshots((prev) => ({ ...prev, [slot]: cloneState(state) }));
  }

  function restoreSnapshot(slot: SnapshotSlot) {
    const restored = snapshots[slot];
    if (!restored) {
      setError(`${slot} は未保存です。`);
      return;
    }
    setState(cloneState(restored));
  }

  function saveBranch(slot: BranchSlot) {
    setBranches((prev) => ({ ...prev, [slot]: cloneState(state) }));
  }

  function loadBranch(slot: BranchSlot) {
    const restored = branches[slot];
    if (!restored) {
      setError(`branch ${slot} は未保存です。`);
      return;
    }
    setState(cloneState(restored));
  }

  function handleSelectRenewMenu(menuKey: RenewMenu) {
    setRenewMenu(menuKey);
    const menu = RENEW_MENUS.find((entry) => entry.key === menuKey);
    if (menu && menu.steps.length > 0) {
      setRenewPanel(menu.steps[0].key);
    }
  }

  async function jumpToGrammarEditor() {
    setUiMode("renewed");
    setRenewMenu("reference");
    setRenewPanel("reference");
    await handleLoadReferenceDocs();
    await handleLoadGrammarRuleSources();
    window.requestAnimationFrame(() => {
      referenceSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  useEffect(() => {
    void handleLoadAllGrammars();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (renewPanel !== "reference") {
      return;
    }
    if (referenceDocsLoadedGrammarId === grammarId && featureDocs.length > 0 && ruleDocs.length > 0) {
      return;
    }
    void handleLoadReferenceDocs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [renewPanel, grammarId]);

  useEffect(() => {
    void refreshAutoTokenPreview();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tokenInputMode, splitMode, sentence, grammarId]);

  useEffect(() => {
    if (!openStep1Help) {
      return;
    }
    const onMouseDown = (event: MouseEvent) => {
      const host = step1ActionRowRef.current;
      if (!host) {
        return;
      }
      if (host.contains(event.target as Node)) {
        return;
      }
      setOpenStep1Help(null);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpenStep1Help(null);
      }
    };
    window.addEventListener("mousedown", onMouseDown);
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("mousedown", onMouseDown);
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [openStep1Help]);

  const activeRenewMenu =
    RENEW_MENUS.find((entry) => entry.key === renewMenu) || RENEW_MENUS[0];
  const legacyPerlIframeSrc = `${LEGACY_PERL_BASE_URL}/v1/legacy/perl/index-IMI.cgi?reload=${legacyFrameReloadTick}`;

  return (
    <div className={uiMode === "legacy" ? "page legacy-mode" : "page renewed-mode"}>
      <header className="hero">
        <p className="eyebrow">SYNCSEMPHONE NEXT</p>
        <h1>Hypothesis Loop Workbench</h1>
        <p>
          Perl版の仮説検証導線（numeration編集・target選択・rule適用・tree/tree_cat・LF/SR・resume）を
          Python版で再現します。
        </p>
        {uiMode === "legacy" && (
          <div className="legacy-titlebar">
            <div className="legacy-title-main">統語意味論デモプログラム</div>
            <div className="legacy-title-sub">
              {activeGrammarOption?.display_name || grammarId} ({grammarId})
            </div>
          </div>
        )}
        <div className="ui-mode-switch">
          <button
            type="button"
            className={uiMode === "legacy" ? "mode-btn active" : "mode-btn"}
            onClick={() => setUiMode("legacy")}
          >
            Legacy UI
          </button>
          <button
            type="button"
            className={uiMode === "renewed" ? "mode-btn active" : "mode-btn"}
            onClick={() => setUiMode("renewed")}
          >
            Renewed UI
          </button>
        </div>
      </header>

      {error && <p className="alert">Error: {error}</p>}

      {uiMode === "legacy" ? (
        <section className="legacy-embed-shell">
          <div className="legacy-embed-toolbar">
            <p className="mono">Perl原本HTMLをそのまま表示（LegacyはRenewed変更と分離）</p>
            <button type="button" onClick={() => setLegacyFrameReloadTick((prev) => prev + 1)}>
              Legacyを再読込
            </button>
          </div>
          <iframe
            title="legacy-perl-ui"
            className="legacy-embed-frame"
            src={legacyPerlIframeSrc}
          />
        </section>
      ) : (
        <div className="renew-shell">
          <aside className="renew-side">
            <h2>Menu</h2>
            {RENEW_MENUS.map((menu) => (
              <button
                key={`menu-${menu.key}`}
                type="button"
                className={renewMenu === menu.key ? "renew-menu-btn active" : "renew-menu-btn"}
                onClick={() => handleSelectRenewMenu(menu.key)}
              >
                {menu.label}
              </button>
            ))}
          </aside>

          <section className="renew-main">
            <div className="renew-topnav">
              {activeRenewMenu.steps.map((step) => (
                <button
                  key={`step-${step.key}`}
                  type="button"
                  className={renewPanel === step.key ? "renew-step-btn active" : "renew-step-btn"}
                  onClick={() => setRenewPanel(step.key)}
                >
                  {step.label}
                </button>
              ))}
            </div>

          <main
            className={uiMode === "renewed" ? "grid renewed-grid" : "grid legacy-grid"}
            data-active-panel={renewPanel}
          >
        <section className="card" data-panel="sentence">
          <h2>1. 入力と初期化</h2>
          <p className="hint step1-t0-note">{T0_BRIEF_DESCRIPTION}</p>
          <div className="step1-stack">
            <div className="grammar-field">
              <div className="grammar-label">文法</div>
              <div className="row grammar-controls">
                <select
                  aria-label="Grammar"
                  value={grammarId}
                  onChange={(event) => {
                    setGrammarId(event.target.value);
                    setReferenceDocsLoadedGrammarId("");
                    setAutoPreviewTokens([]);
                    setGrammarRuleSources([]);
                    setSelectedGrammarRuleNumber(null);
                    setGrammarRuleSourceText("");
                    setGrammarRuleSourceFileName("");
                    setGrammarRuleSourceMessage("");
                  }}
                >
                  {grammarOptions.map((option) => (
                    <option key={option.grammar_id} value={option.grammar_id}>
                      {formatGrammarOption(option)}
                    </option>
                  ))}
                </select>
                <button onClick={handleLoadAllGrammars} disabled={loading}>
                  文法一覧を更新
                </button>
                <button
                  onClick={() => {
                    void jumpToGrammarEditor();
                  }}
                  disabled={loading}
                >
                  文法定義を閲覧・編集
                </button>
              </div>
            </div>

            <label>
              観察文（原文）
              <textarea
                aria-label="Sentence"
                value={sentence}
                onChange={(event) => setSentence(event.target.value)}
                rows={3}
              />
            </label>

            <div className="split-result-panel">
              <div className="split-result-head">
                <div className="split-result-title">分割結果</div>
                <div className="split-result-actions">
                  <span className="split-mode-status" data-testid="token-input-mode">
                    {tokenInputMode === "manual" ? "手動" : "自動"}
                  </span>
                  <div className="token-mode-toggle" role="group" aria-label="分割方法">
                    <button
                      type="button"
                      className={tokenInputMode === "manual" ? "token-mode-btn active" : "token-mode-btn"}
                      onClick={() => setTokenInputMode("manual")}
                    >
                      手動
                    </button>
                    <button
                      type="button"
                      className={tokenInputMode === "auto" ? "token-mode-btn active" : "token-mode-btn"}
                      onClick={() => setTokenInputMode("auto")}
                    >
                      自動（Sudachi）
                    </button>
                  </div>
                </div>
              </div>

              {tokenInputMode === "manual" ? (
                <label>
                  手動入力（空白/カンマ区切り）
                  <input
                    aria-label="Manual Tokens"
                    value={manualTokensInput}
                    onChange={(event) => setManualTokensInput(event.target.value)}
                  />
                </label>
              ) : (
                <label>
                  Sudachi 分割モード
                  <select
                    aria-label="Sudachi Split Mode"
                    value={splitMode}
                    onChange={(event) => setSplitMode(event.target.value)}
                  >
                    <option value="A">A</option>
                    <option value="B">B</option>
                    <option value="C">C</option>
                  </select>
                </label>
              )}
              {tokenInputMode === "auto" && (
                <p className="hint">
                  分割モードを切り替えると結果がその場で更新されます。
                  {autoPreviewLoading ? "（更新中）" : ""}
                </p>
              )}

              <div className="token-chip-row" data-testid="token-chip-row">
                {displayedTokens.length === 0 && (
                  <span className="token-chip-empty">（まだ分割結果がありません）</span>
                )}
                {displayedTokens.map((token, index) => (
                  <span
                    key={`${token}-${index}`}
                    className="token-chip"
                    style={{ backgroundColor: TOKEN_CHIP_COLORS[index % TOKEN_CHIP_COLORS.length] }}
                  >
                    {token}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="row step1-actions" ref={step1ActionRowRef}>
            <div className="step1-action-item">
              <button onClick={handleGenerate} disabled={loading}>
                .num を生成（T0は作らない）
              </button>
              <button
                type="button"
                className="help-tip"
                aria-label=".num を生成の説明"
                aria-expanded={openStep1Help === "generate_num"}
                onClick={() =>
                  setOpenStep1Help((prev) => (prev === "generate_num" ? null : "generate_num"))
                }
              >
                ?
              </button>
              {openStep1Help === "generate_num" && (
                <div className="help-popover">{STEP1_HELP_CONTENT.generate_num}</div>
              )}
            </div>
            <div className="step1-action-item">
              <button onClick={handleInitFromSentence} disabled={loading}>
                文から T0 を初期化（.num 生成あり）
              </button>
              <button
                type="button"
                className="help-tip"
                aria-label="文から T0 を初期化の説明"
                aria-expanded={openStep1Help === "init_from_sentence"}
                onClick={() =>
                  setOpenStep1Help((prev) =>
                    prev === "init_from_sentence" ? null : "init_from_sentence"
                  )
                }
              >
                ?
              </button>
              {openStep1Help === "init_from_sentence" && (
                <div className="help-popover">{STEP1_HELP_CONTENT.init_from_sentence}</div>
              )}
            </div>
            <div className="step1-action-item">
              <button onClick={handleInitFromNumerationText} disabled={loading || numerationText.trim() === ""}>
                .num から T0 を初期化
              </button>
              <button
                type="button"
                className="help-tip"
                aria-label=".num から T0 を初期化の説明"
                aria-expanded={openStep1Help === "init_from_num"}
                onClick={() =>
                  setOpenStep1Help((prev) => (prev === "init_from_num" ? null : "init_from_num"))
                }
              >
                ?
              </button>
              {openStep1Help === "init_from_num" && (
                <div className="help-popover">{STEP1_HELP_CONTENT.init_from_num}</div>
              )}
            </div>
          </div>
          <p className="hint step1-action-summary">
            まず「文から T0 を初期化（.num 生成あり）」を使い、.num 調整だけ行いたい時に「.num を生成（T0は作らない）」、
            既存 .num の再利用時に「.num から T0 を初期化」を使います。
          </p>
        </section>

        <section className="card" data-panel="numeration">
          <h2>2. Numeration 作成・編集</h2>
          <pre data-testid="numeration-text">{numerationText || "(未生成)"}</pre>
          <label>
            .num エディタ
            <textarea
              aria-label="numeration-editor"
              rows={8}
              value={numerationText}
              onChange={(event) => setNumerationText(event.target.value)}
            />
          </label>
          <p>lexicon_ids: {generated?.lexicon_ids.join(", ") || "-"}</p>

          <h3>Perl互換 .num ソース</h3>
          <div className="row">
            <button onClick={() => handleLoadNumerationFiles("set")} disabled={loading}>
              set-numeration を読み込む
            </button>
            <select
              aria-label="set-numeration-select"
              value={selectedSetPath}
              onChange={(event) => setSelectedSetPath(event.target.value)}
            >
              <option value="">（set-numeration を選択）</option>
              {setNumerationFiles.map((row) => (
                <option key={row.path} value={row.path}>
                  [{row.memo}] {row.file_name}
                </option>
              ))}
            </select>
            <button
              onClick={() => handleLoadNumerationPath(selectedSetPath)}
              disabled={loading || selectedSetPath === ""}
            >
              選択した set を反映
            </button>
          </div>

          <div className="row">
            <button onClick={() => handleLoadNumerationFiles("saved")} disabled={loading}>
              numeration を読み込む
            </button>
            <select
              aria-label="saved-numeration-select"
              value={selectedSavedPath}
              onChange={(event) => setSelectedSavedPath(event.target.value)}
            >
              <option value="">（numeration を選択）</option>
              {savedNumerationFiles.map((row) => (
                <option key={row.path} value={row.path}>
                  [{row.memo}] {row.file_name}
                </option>
              ))}
            </select>
            <button
              onClick={() => handleLoadNumerationPath(selectedSavedPath)}
              disabled={loading || selectedSavedPath === ""}
            >
              選択した numeration を反映
            </button>
            <button onClick={handleSaveNumeration} disabled={loading || numerationText.trim() === ""}>
              .num を保存
            </button>
          </div>

          <label>
            .num テキスト入力（Perl upload 相当）
            <textarea
              aria-label="upload-numeration"
              rows={4}
              value={uploadNumerationText}
              onChange={(event) => setUploadNumerationText(event.target.value)}
            />
          </label>
          <div className="row">
            <button onClick={handleApplyUploadNumeration} disabled={loading || uploadNumerationText.trim() === ""}>
              入力テキストを反映
            </button>
            <button onClick={handleArrangeFromCurrentNumeration} disabled={loading || numerationText.trim() === ""}>
              現在の .num から Arrange を作成
            </button>
            <button onClick={handleApplyArrangeToNumeration} disabled={loading || arrangeRows.length === 0}>
              Arrange を反映
            </button>
          </div>

          {arrangeRows.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>slot</th>
                  <th>lexicon</th>
                  <th>plus</th>
                  <th>idx</th>
                </tr>
              </thead>
              <tbody>
                {arrangeRows.map((row) => (
                  <tr key={`arrange-${row.slot}`}>
                    <td>{row.slot}</td>
                    <td>
                      <input
                        value={row.lexiconId}
                        onChange={(event) =>
                          updateArrangeRow(row.slot, { lexiconId: event.target.value })
                        }
                      />
                    </td>
                    <td>
                      <input
                        value={row.plusValue}
                        onChange={(event) =>
                          updateArrangeRow(row.slot, { plusValue: event.target.value })
                        }
                      />
                    </td>
                    <td>
                      <input
                        value={row.idxValue}
                        onChange={(event) =>
                          updateArrangeRow(row.slot, { idxValue: event.target.value })
                        }
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {tokenSlotEdits.length > 0 && (
            <>
              <h3>Lexical candidate re-selection (Perl lexicon_select 相当)</h3>
              <table>
                <thead>
                  <tr>
                    <th>slot</th>
                    <th>token</th>
                    <th>selected lexicon</th>
                    <th>idx</th>
                    <th>plus</th>
                  </tr>
                </thead>
                <tbody>
                  {tokenSlotEdits.map((row) => (
                    <tr key={`slot-edit-${row.slot}`}>
                      <td>{row.slot}</td>
                      <td>{row.token}</td>
                      <td>
                        <select
                          value={row.selectedLexiconId}
                          onChange={(event) =>
                            updateTokenSlotEdit(row.slot, {
                              selectedLexiconId: Number(event.target.value)
                            })
                          }
                        >
                          {row.candidateLexiconIds.map((candidateId) => (
                            <option key={`${row.slot}-${candidateId}`} value={candidateId}>
                              {candidateId}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <input
                          value={row.idxValue}
                          onChange={(event) =>
                            updateTokenSlotEdit(row.slot, { idxValue: event.target.value })
                          }
                        />
                      </td>
                      <td>
                        <input
                          value={row.plusValue}
                          onChange={(event) =>
                            updateTokenSlotEdit(row.slot, { plusValue: event.target.value })
                          }
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <button onClick={handleComposeNumerationFromTokenSelection} disabled={loading}>
                Compose .num from token selection
              </button>
            </>
          )}
        </section>

        <section className="card" data-panel="target">
          <h2>3. Target / Derivation</h2>
          <p>status: {grammarStatus}</p>
          <p>
            basenum/newnum: {state ? `${state.basenum}/${state.newnum}` : "-"}
          </p>
          <p className="mono" data-testid="current-history">
            history: {state?.history || "(empty)"}
          </p>

          {state && (
            <table>
              <thead>
                <tr>
                  <th>left</th>
                  <th>right</th>
                  <th>base item</th>
                </tr>
              </thead>
              <tbody>
                {Array.from({ length: state.basenum }, (_, i) => i + 1).map((index) => (
                  <tr key={`base-row-${index}`}>
                    <td>
                      <input
                        type="radio"
                        name="left-target"
                        checked={selectedLeft === index}
                        onChange={() => {
                          setSelectedLeft(index);
                          setLeft(String(index));
                        }}
                      />
                    </td>
                    <td>
                      <input
                        type="radio"
                        name="right-target"
                        checked={selectedRight === index}
                        onChange={() => {
                          setSelectedRight(index);
                          setRight(String(index));
                        }}
                      />
                    </td>
                    <td>{renderBaseItem((state.base as unknown[])[index])}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <div className="row">
            <label>
              left
              <input
                aria-label="left"
                value={left}
                onChange={(event) => {
                  setLeft(event.target.value);
                  setSelectedLeft(null);
                }}
              />
            </label>
            <label>
              right
              <input
                aria-label="right"
                value={right}
                onChange={(event) => {
                  setRight(event.target.value);
                  setSelectedRight(null);
                }}
              />
            </label>
            <button onClick={handleCandidates} disabled={loading || !state}>
              Load Candidates
            </button>
          </div>

          <table data-testid="candidate-table">
            <thead>
              <tr>
                <th>rule</th>
                <th>kind</th>
                <th>args</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {candidates.map((candidate) => (
                <tr key={`${candidate.rule_number}-${candidate.left}-${candidate.right}-${candidate.check}`}>
                  <td>
                    {candidate.rule_number}:{candidate.rule_name}
                  </td>
                  <td>{candidate.rule_kind}</td>
                  <td>
                    {candidate.rule_kind === "single"
                      ? `check=${candidate.check}`
                      : `L=${candidate.left}, R=${candidate.right}`}
                  </td>
                  <td>
                    <button onClick={() => handleExecuteCandidate(candidate)} disabled={loading}>
                      Execute
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="card" data-panel="observation">
          <h2>4. Observation</h2>
          <div className="row">
            <button onClick={() => handleTree("tree")} disabled={loading || !state}>
              tree
            </button>
            <button onClick={() => handleTree("tree_cat")} disabled={loading || !state}>
              tree_cat
            </button>
            <button onClick={() => handleSemantics("lf")} disabled={loading || !state}>
              lf
            </button>
            <button onClick={() => handleSemantics("sr")} disabled={loading || !state}>
              sr
            </button>
          </div>

          <h3>tree</h3>
          <pre data-testid="tree-output">{treeCsv}</pre>
          <h3>tree_cat</h3>
          <pre data-testid="tree-cat-output">{treeCatCsv}</pre>
          <h3>LF list representation</h3>
          <pre data-testid="lf-output">
            {lfRows.map((row) => `${row.lexical_id} | ${row.semantics.join("; ")}`).join("\n")}
          </pre>
          <h3>SR truth conditional meaning</h3>
          <pre data-testid="sr-output">
            {srRows
              .map((row) => `${row.object_id}-${row.layer}-${row.kind} | ${row.properties.join("; ")}`)
              .join("\n")}
          </pre>

          <h3>Tree graphical viewer ({activeTreeMode})</h3>
          <label>
            source_csv
            <textarea
              aria-label="tree-source-csv"
              rows={8}
              value={treeSourceCsv}
              onChange={(event) => setTreeSourceCsv(event.target.value)}
            />
          </label>
          <button onClick={handleTreeConvert} disabled={loading || treeSourceCsv.trim() === ""}>
            変換
          </button>
          <label>
            converted_dot
            <textarea aria-label="tree-dot" rows={8} value={treeDot} readOnly />
          </label>
          {treeGraph && (
            <div style={{ overflow: "auto" }}>
              <svg width={treeGraph.width} height={treeGraph.height} data-testid="tree-graph">
                {treeGraph.edges.map((edge) => {
                  const from = treeGraph.nodes.find((node) => node.id === edge.from);
                  const to = treeGraph.nodes.find((node) => node.id === edge.to);
                  if (!from || !to) {
                    return null;
                  }
                  return (
                    <line
                      key={`${edge.from}-${edge.to}`}
                      x1={from.x + 70}
                      y1={from.y + 50}
                      x2={to.x + 70}
                      y2={to.y}
                      stroke={edge.color}
                      strokeWidth={2}
                    />
                  );
                })}
                {treeGraph.nodes.map((node) => (
                  <g key={`node-${node.id}`}>
                    <rect x={node.x} y={node.y} width={140} height={56} fill="#fff" stroke="#444" />
                    {node.labelLines.map((line, index) => (
                      <text
                        key={`label-${node.id}-${index}`}
                        x={node.x + 8}
                        y={node.y + 18 + index * 14}
                        fontSize={12}
                        fontFamily="monospace"
                      >
                        {line}
                      </text>
                    ))}
                  </g>
                ))}
              </svg>
            </div>
          )}
        </section>

        <section className="card" data-panel="resume">
          <h2>5. Save/Resume + A/B</h2>
          <div className="row">
            <button onClick={handleResumeExport} disabled={loading || !state}>
              Export resume
            </button>
            <button onClick={handleResumeImport} disabled={loading || resumeText.length === 0}>
              Import resume
            </button>
          </div>
          <textarea
            aria-label="resume-text"
            rows={5}
            value={resumeText}
            onChange={(event) => setResumeText(event.target.value)}
          />

          <div className="stack">
            <h3>T0/T1/T2 snapshots</h3>
            <div className="row">
              <button onClick={() => saveSnapshot("T0")}>Save T0</button>
              <button onClick={() => saveSnapshot("T1")}>Save T1</button>
              <button onClick={() => saveSnapshot("T2")}>Save T2</button>
            </div>
            <div className="row">
              <button onClick={() => restoreSnapshot("T0")}>Load T0</button>
              <button onClick={() => restoreSnapshot("T1")}>Load T1</button>
              <button onClick={() => restoreSnapshot("T2")}>Load T2</button>
            </div>
          </div>

          <div className="stack">
            <h3>A/B branch compare</h3>
            <div className="row">
              <button onClick={() => saveBranch("A")}>Save A</button>
              <button onClick={() => saveBranch("B")}>Save B</button>
              <button onClick={() => loadBranch("A")}>Load A</button>
              <button onClick={() => loadBranch("B")}>Load B</button>
            </div>
            <p className="mono">
              A history: {branches.A?.history || "-"}
              {"\n"}
              B history: {branches.B?.history || "-"}
            </p>
          </div>
        </section>

        <section className="card" data-panel="reference" ref={referenceSectionRef}>
          <h2>6. Rule/Feature Reference (iframe)</h2>
          <div className="row">
            <button onClick={handleLoadFeatureDocs} disabled={loading}>
              機能ドキュメントを再読み込み
            </button>
            <select
              aria-label="feature-doc-select"
              value={selectedFeatureDoc}
              onChange={(event) => setSelectedFeatureDoc(event.target.value)}
            >
              <option value="">(select feature doc)</option>
              {featureDocs.map((doc) => (
                <option key={doc.file_name} value={doc.file_name}>
                  {doc.file_name}
                </option>
              ))}
            </select>
            <button
              onClick={() => handleOpenFeatureDoc(selectedFeatureDoc)}
              disabled={loading || selectedFeatureDoc === ""}
            >
              機能ドキュメントを表示
            </button>
          </div>

          <iframe title="feature-doc" srcDoc={featureDocHtml} style={{ width: "100%", height: 220 }} />

          <div className="row">
            <button onClick={handleLoadRuleDocs} disabled={loading}>
              規則ドキュメントを再読み込み
            </button>
            <select
              aria-label="rule-doc-select"
              value={selectedRuleDoc}
              onChange={(event) => setSelectedRuleDoc(event.target.value)}
            >
              <option value="">(select rule doc)</option>
              {ruleDocs.map((doc) => (
                <option key={`${doc.rule_number}-${doc.file_name}`} value={doc.file_name}>
                  {doc.rule_number}:{doc.rule_name}
                </option>
              ))}
            </select>
            <button
              onClick={() => handleOpenRuleDoc(selectedRuleDoc)}
              disabled={loading || selectedRuleDoc === ""}
            >
              規則ドキュメントを表示
            </button>
          </div>

          <iframe title="rule-doc" srcDoc={ruleDocHtml} style={{ width: "100%", height: 220 }} />

          <h3>文法ルール原本の閲覧・編集</h3>
          <div className="row">
            <button onClick={handleLoadGrammarRuleSources} disabled={loading}>
              ルール一覧を読み込む
            </button>
            <select
              aria-label="grammar-rule-source-select"
              value={selectedGrammarRuleNumber?.toString() || ""}
              onChange={(event) => {
                const value = Number(event.target.value);
                if (Number.isInteger(value) && value > 0) {
                  setSelectedGrammarRuleNumber(value);
                } else {
                  setSelectedGrammarRuleNumber(null);
                }
              }}
            >
              <option value="">（ルールを選択）</option>
              {grammarRuleSources.map((row) => (
                <option key={`rule-source-${row.rule_number}`} value={row.rule_number}>
                  {row.rule_number}: {row.rule_name} [{row.file_name}]
                  {row.exists ? "" : " (missing)"}
                </option>
              ))}
            </select>
            <button
              onClick={() => {
                if (selectedGrammarRuleNumber) {
                  void handleOpenGrammarRuleSource(selectedGrammarRuleNumber);
                }
              }}
              disabled={loading || !selectedGrammarRuleNumber}
            >
              読み込む
            </button>
            <button onClick={handleSaveGrammarRuleSource} disabled={loading || !selectedGrammarRuleNumber}>
              保存
            </button>
          </div>
          <p className="mono" data-testid="grammar-rule-source-meta">
            file: {grammarRuleSourceFileName || "-"}
            {"\n"}
            selected:{" "}
            {selectedGrammarRule
              ? `${selectedGrammarRule.rule_number}:${selectedGrammarRule.rule_name}`
              : "-"}
          </p>
          <p data-testid="grammar-rule-source-message">{grammarRuleSourceMessage}</p>
          <label>
            ルール原本（.pl）
            <textarea
              aria-label="grammar-rule-source-editor"
              rows={10}
              value={grammarRuleSourceText}
              onChange={(event) => setGrammarRuleSourceText(event.target.value)}
            />
          </label>
        </section>

        <section className="card" data-panel="lexicon">
          <h2>7. Lexicon Viewer (Phase A-C)</h2>
          <div className="row">
            <label>
              Lexicon Format
              <select
                aria-label="Lexicon Format"
                value={lexiconFormat}
                onChange={(event) => setLexiconFormat(event.target.value as "yaml" | "csv")}
              >
                <option value="yaml">yaml</option>
                <option value="csv">csv</option>
              </select>
            </label>
            <button onClick={handleLoadLexicon} disabled={loading}>
              Load Lexicon
            </button>
            <button onClick={handleValidateLexiconYaml} disabled={loading || lexiconYamlInput.length === 0}>
              Validate YAML
            </button>
            <button onClick={handleImportLexiconYaml} disabled={loading || lexiconYamlInput.length === 0}>
              Import YAML
            </button>
            <button onClick={handleCommitLexiconYaml} disabled={loading || lexiconYamlInput.length === 0}>
              Commit YAML
            </button>
          </div>
          <label>
            <input
              type="checkbox"
              checked={runLexiconCompatibilityTests}
              onChange={(event) => setRunLexiconCompatibilityTests(event.target.checked)}
            />
            Run compatibility tests on commit
          </label>
          <p>path: {lexiconPath || "-"}</p>
          <p>entries: {lexiconEntryCount || 0}</p>
          <p data-testid="lexicon-commit-message">{lexiconCommitMessage}</p>
          <pre data-testid="lexicon-output">{lexiconText}</pre>
          <label>
            YAML Input
            <textarea
              aria-label="Lexicon YAML Input"
              rows={8}
              value={lexiconYamlInput}
              onChange={(event) => setLexiconYamlInput(event.target.value)}
            />
          </label>
          {lexiconValidateErrors.length > 0 && (
            <pre data-testid="lexicon-errors">{lexiconValidateErrors.join("\n")}</pre>
          )}
          <h3>CSV Preview</h3>
          <pre data-testid="lexicon-csv-preview">{lexiconCsvPreview}</pre>
          <h3>Commit stdout</h3>
          <pre data-testid="lexicon-commit-stdout">{lexiconCommitStdout}</pre>
          <h3>Commit stderr</h3>
          <pre data-testid="lexicon-commit-stderr">{lexiconCommitStderr}</pre>
        </section>
          </main>
        </section>
      </div>
      )}
    </div>
  );
}
