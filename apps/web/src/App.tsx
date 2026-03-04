import { useEffect, useMemo, useRef, useState } from "react";
import { apiGet, apiPost, parseManualTokens } from "./api";
import LexiconWorkbench from "./LexiconWorkbench";
import type {
  DerivationState,
  FeatureDocEntry,
  GeneratedNumeration,
  GrammarOption,
  HtmlDocResponse,
  LexiconItemLookupItem,
  LexiconItemsPageResponse,
  LexiconCommitResponse,
  LexiconItemsLookupResponse,
  LexiconExportResponse,
  LexiconSummaryResponse,
  LexiconImportResponse,
  LexiconValidateResponse,
  LfResponse,
  MergeRuleEntry,
  NumerationFileEntry,
  ObservationTreeResponse,
  ProcessExportResponse,
  ReachabilityEvidence,
  ReachabilityEvidencePageResponse,
  ReachabilityJobStartResponse,
  ReachabilityJobStatusResponse,
  ReachabilityResponse,
  RuleCompareResponse,
  RuleCandidate,
  RuleDocEntry,
  SrResponse
} from "./types";

type SnapshotSlot = "T0" | "T1" | "T2";
type BranchSlot = "A" | "B";
type TreeMode = "tree" | "tree_cat";
type UiMode = "legacy" | "renewed";
type TokenInputMode = "manual" | "auto";
type Step1EntryMode = "example_sentence" | "upload_num" | "build_lexicon";
type ReferenceDocTab = "feature" | "rule";
type RenewMenu = "hypothesis" | "reference" | "lexicon";
type RenewPanel =
  | "setup"
  | "sentence"
  | "numeration"
  | "target"
  | "observation"
  | "resume"
  | "grammarInspect"
  | "lexiconInspect"
  | "ruleCompare"
  | "referenceDocs"
  | "lexicon";

type PersistedUiState = {
  uiMode: UiMode;
  renewPanel: RenewPanel;
  workflowStarted: boolean;
  grammarId: string;
  setupGrammarId: string;
  step1EntryMode: Step1EntryMode;
};

type TokenCandidateCompatibility = {
  lexiconId: number;
  compatible: boolean;
  reasonCodes: string[];
  missingRuleNames: string[];
  referencedRuleNames: string[];
};

type TokenSlotEdit = {
  slot: number;
  token: string;
  selectedLexiconId: number;
  candidateLexiconIds: number[];
  candidateCompatibilityById: Record<number, TokenCandidateCompatibility>;
  plusValue: string;
  idxValue: string;
};

type NumerationTokenResolution = {
  slot: number;
  token: string;
  lexicon_id: number;
  candidate_lexicon_ids: number[];
  candidate_compatibility?: Array<{
    lexicon_id: number;
    compatible: boolean;
    reason_codes: string[];
    missing_rule_names: string[];
    referenced_rule_names: string[];
  }>;
};

type ReachabilityDisplayGroup = {
  firstStepKey: string;
  representative: ReachabilityEvidence;
  options: ReachabilityEvidence[];
};

type AutoSupplementNote = NonNullable<GeneratedNumeration["auto_supplements"]>[number];

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

const UI_PERSISTENCE_KEY = "syncsemphone-next:ui-state:v1";
const ENABLE_UI_PERSISTENCE = import.meta.env.MODE !== "test";

const RENEW_MENUS: Array<{
  key: RenewMenu;
  label: string;
  steps: Array<{ key: RenewPanel; label: string }>;
}> = [
  {
    key: "hypothesis",
    label: "仮説検証ステップ",
    steps: [
      { key: "setup", label: "【Step.0】LexiconとGrammarの選択" },
      { key: "sentence", label: "【Step.1】Numerationの形成" },
      { key: "target", label: "【Step.2】Grammarの適用" },
      { key: "observation", label: "【Step.3】観察" },
      { key: "resume", label: "【Step.4】保存/再開" },
      { key: "numeration", label: "補助：Numeration編集" }
    ]
  },
  {
    key: "reference",
    label: "素性とルールの確認",
    steps: [
      { key: "grammarInspect", label: "文法規則の内容確認" },
      { key: "lexiconInspect", label: "語彙の内容確認" },
      { key: "referenceDocs", label: "資料参照" }
    ]
  },
  {
    key: "lexicon",
    label: "語彙の編集",
    steps: [{ key: "lexicon", label: "語彙の編集" }]
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
  const normalized = text.replace(/\\t/g, "\t");
  const lines = normalized.split(/\r?\n/);
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

function normalizeNumerationTextForParse(text: string): string {
  return text.replace(/\\t/g, "\t");
}

function encodeNumerationTextLikePerl(text: string): string {
  return text.replace(/\t/g, "\\t");
}

function buildReachabilityFirstStepKey(row: ReachabilityEvidence): string {
  const first = row.rule_sequence[0];
  if (!first) {
    return `no-step:${row.rank}`;
  }
  return [
    first.rule_number,
    first.rule_name,
    first.rule_kind,
    first.left ?? "",
    first.right ?? "",
    first.check ?? ""
  ].join(":");
}

type NumerationLexiconRow = {
  slot: number;
  rawLexiconId: string;
  lexiconId: number | null;
  plus: string;
  idx: string;
  found: boolean | null;
  entry: string;
  phono: string;
  category: string;
  syncFeatures: string[];
  idslot: string;
  semantics: string[];
  note: string;
};

type PartnerRequirement = {
  featureCode: "25" | "33";
  label: string;
};

type Step1PartnerWarning = {
  level: "impossible" | "possible";
  slot: number;
  selectedLexiconId: number;
  selectedEntry: string;
  requirement: PartnerRequirement;
  providerSlots: number[];
};

type Step2DisplayNode = {
  xLabel: string;
  category: string;
  syncFeatures: string[];
  idslot: string;
  semantics: string[];
  phono: string;
  unresolvedMessage: string | null;
  children: Step2DisplayNode[];
};

type Step2DisplayRow = {
  slot: number;
  node: Step2DisplayNode;
};

function parseNumerationLexiconRows(text: string): Pick<NumerationLexiconRow, "slot" | "rawLexiconId" | "lexiconId" | "plus" | "idx">[] {
  const lines = normalizeNumerationTextForParse(text).replace(/\r\n/g, "\n").split("\n");
  const row1 = (lines[0] || "").split("\t");
  const row2 = (lines[1] || "").split("\t");
  const row3 = (lines[2] || "").split("\t");
  const parsedRows = [];
  for (let i = 0; i < 30; i += 1) {
    const raw = (row1[i + 1] ?? "").trim();
    if (raw === "") {
      continue;
    }
    const parsedId = Number(raw);
    parsedRows.push({
      slot: i + 1,
      rawLexiconId: raw,
      lexiconId: Number.isInteger(parsedId) && parsedId > 0 ? parsedId : null,
      plus: (row2[i + 1] ?? "").trim(),
      idx: (row3[i + 1] ?? "").trim()
    });
  }
  return parsedRows;
}

function buildStep2DisplayNode(item: unknown, fallbackLabel: string): Step2DisplayNode {
  if (!Array.isArray(item)) {
    return {
      xLabel: fallbackLabel,
      category: "-",
      syncFeatures: [],
      idslot: "",
      semantics: [],
      phono: "",
      unresolvedMessage: "この行の語彙情報を表示できません。",
      children: []
    };
  }

  const xLabelRaw = String(item[0] ?? "").trim();
  const xLabel = xLabelRaw === "" ? fallbackLabel : xLabelRaw;
  const children: Step2DisplayNode[] = [];
  const rawChildren = item[7];
  if (Array.isArray(rawChildren)) {
    for (let idx = 0; idx < rawChildren.length; idx += 1) {
      const child = rawChildren[idx];
      if (child === "zero") {
        continue;
      }
      children.push(buildStep2DisplayNode(child, `${xLabel}-d${idx + 1}`));
    }
  }

  return {
    xLabel,
    category: String(item[1] ?? "").trim(),
    syncFeatures: Array.isArray(item[3])
      ? item[3].map((value) => (value == null ? "" : String(value)))
      : [],
    idslot: String(item[4] ?? ""),
    semantics: Array.isArray(item[5])
      ? item[5].map((value) => (value == null ? "" : String(value)))
      : [],
    phono: String(item[6] ?? ""),
    unresolvedMessage: null,
    children
  };
}

function buildStep2DisplayRows(state: DerivationState | null): Step2DisplayRow[] {
  if (!state || !Array.isArray(state.base)) {
    return [];
  }
  const rows: Step2DisplayRow[] = [];
  for (let slot = 1; slot <= state.basenum; slot += 1) {
    const item = (state.base as unknown[])[slot];
    rows.push({
      slot,
      node: buildStep2DisplayNode(item, `x${slot}-1`)
    });
  }
  return rows;
}

type EncodedFeatureSegment = {
  text: string;
  tone: "base" | "annotation" | "plain";
  subscript?: boolean;
};

type EncodedFeatureRender = {
  isFeature: boolean;
  segments: EncodedFeatureSegment[];
};

function parseEncodedFeatureLikePerl(value: string): EncodedFeatureRender {
  if (value === "0=R=0") {
    return { isFeature: true, segments: [{ text: "+R", tone: "base" }] };
  }
  if (value === "0=da=0") {
    return { isFeature: true, segments: [{ text: "da", tone: "base" }] };
  }
  if (!/,[0-9]/.test(value)) {
    return { isFeature: false, segments: [{ text: value, tone: "plain" }] };
  }
  const parts = value.split(",");
  const code = parts[1] ?? "";
  const p2 = parts[2] ?? "";
  const p3 = parts[3] ?? "";
  const p4 = parts[4] ?? "";
  const p5 = parts[5] ?? "";
  const p6 = parts[6] ?? "";

  if (code === "17") {
    const segments: EncodedFeatureSegment[] = [{ text: `+${p2}${p3}`, tone: "base" }];
    if (p4 !== "") {
      segments.push({ text: `[${p4}]`, tone: "annotation" });
    }
    if (p5 !== "") {
      segments.push({ text: `(${p5})`, tone: "annotation" });
    }
    if (p6 !== "") {
      segments.push({ text: `(${p6})`, tone: "annotation" });
    }
    return { isFeature: true, segments };
  }
  if (code === "34") {
    const segments: EncodedFeatureSegment[] = [
      { text: "★", tone: "base" },
      { text: `${p2}${p3}`, tone: "annotation", subscript: true }
    ];
    if (p4 !== "") {
      segments.push({ text: `[${p4}]`, tone: "annotation" });
    }
    if (p5 !== "") {
      segments.push({ text: `(${p5})`, tone: "annotation" });
    }
    return { isFeature: true, segments };
  }
  if (code === "25" || code === "33") {
    return {
      isFeature: true,
      segments: [
        { text: "★", tone: "base" },
        { text: p2, tone: "base", subscript: true }
      ]
    };
  }
  if (code === "26" || code === "27") {
    const suffix = code === "26" ? `[${p2}]` : `<${p2}>`;
    return {
      isFeature: true,
      segments: [
        { text: "★", tone: "base" },
        { text: suffix, tone: "base", subscript: true }
      ]
    };
  }
  if (code === "70" || code === "71") {
    const suffix = code === "70" ? p2 : `<${p2}>`;
    return {
      isFeature: true,
      segments: [
        { text: "●", tone: "base" },
        { text: suffix, tone: "base", subscript: true }
      ]
    };
  }
  return {
    isFeature: true,
    segments: [{ text: formatEncodedFeatureLikePerl(value), tone: "base" }]
  };
}

function renderEncodedFeatureLikePerl(value: string, keyPrefix: string): JSX.Element {
  const parsed = parseEncodedFeatureLikePerl(value);
  if (!parsed.isFeature) {
    return <>{parsed.segments[0]?.text || value}</>;
  }
  return (
    <span className="numeration-feature">
      {parsed.segments.map((segment, idx) => {
        const className =
          segment.tone === "annotation"
            ? "numeration-feature-orange"
            : "numeration-feature-red";
        if (segment.subscript) {
          return (
            <sub className={className} key={`${keyPrefix}-${idx}`}>
              {segment.text}
            </sub>
          );
        }
        return (
          <span className={className} key={`${keyPrefix}-${idx}`}>
            {segment.text}
          </span>
        );
      })}
    </span>
  );
}

function isEncodedFeature(value: string): boolean {
  return /,[0-9]/.test(value) || value === "0=R=0" || value === "0=da=0";
}

function parsePartnerRequirementsFromSemantics(semantics: string[]): PartnerRequirement[] {
  const requirements: PartnerRequirement[] = [];
  for (const semantic of semantics) {
    const pos = semantic.indexOf(":");
    if (pos < 0) {
      continue;
    }
    const value = semantic.slice(pos + 1).trim();
    if (!isEncodedFeature(value)) {
      continue;
    }
    const parts = value.split(",");
    const featureCode = (parts[1] ?? "").trim();
    const label = (parts[2] ?? "").trim();
    if ((featureCode === "25" || featureCode === "33") && label !== "") {
      requirements.push({ featureCode, label });
    }
  }
  return requirements;
}

function parsePartnerCapabilitiesFromSyncFeatures(syncFeatures: string[]): {
  plain: Set<string>;
  labeled: Set<string>;
} {
  const plain = new Set<string>();
  const labeled = new Set<string>();
  for (const rawFeature of syncFeatures) {
    const feature = rawFeature.trim();
    if (feature === "") {
      continue;
    }
    if (!isEncodedFeature(feature)) {
      plain.add(feature);
      continue;
    }
    const parts = feature.split(",");
    const code = (parts[1] ?? "").trim();
    const label = (parts[2] ?? "").trim();
    if ((code === "11" || code === "12") && label !== "") {
      labeled.add(label);
    }
  }
  return { plain, labeled };
}

function normalizeTokenCandidateCompatibility(
  row: GeneratedNumeration["token_resolutions"][number]
): Record<number, TokenCandidateCompatibility> {
  const out: Record<number, TokenCandidateCompatibility> = {};
  const byPayload = row.candidate_compatibility || [];
  for (const item of byPayload) {
    out[item.lexicon_id] = {
      lexiconId: item.lexicon_id,
      compatible: item.compatible,
      reasonCodes: item.reason_codes || [],
      missingRuleNames: item.missing_rule_names || [],
      referencedRuleNames: item.referenced_rule_names || []
    };
  }
  for (const candidateId of row.candidate_lexicon_ids || []) {
    if (!out[candidateId]) {
      out[candidateId] = {
        lexiconId: candidateId,
        compatible: true,
        reasonCodes: [],
        missingRuleNames: [],
        referencedRuleNames: []
      };
    }
  }
  return out;
}

function formatCompatibilityReasonsForDisplay(
  compatibility: TokenCandidateCompatibility
): string[] {
  const reasons: string[] = [];
  if (compatibility.reasonCodes.includes("requires_japanese2_l_feature")) {
    reasons.push("1L/2L/3L 素性は japanese2 文法専用です。");
  }
  if (
    compatibility.reasonCodes.includes("missing_required_rule") &&
    compatibility.missingRuleNames.length > 0
  ) {
    reasons.push(
      `必要ルールが Step0 の文法にありません（${compatibility.missingRuleNames.join(", ")}）。`
    );
  }
  if (reasons.length === 0) {
    reasons.push("選択中の Step0 文法でこの語彙項目を使う条件を満たしません。");
  }
  return reasons;
}

function formatEncodedFeatureLikePerl(value: string): string {
  if (value === "0=R=0") {
    return "+R";
  }
  if (value === "0=da=0") {
    return "da";
  }
  if (!/,[0-9]/.test(value)) {
    return value;
  }
  const parts = value.split(",");
  const bucket = parts[0] ?? "";
  const code = parts[1] ?? "";
  const p2 = parts[2] ?? "";
  const p3 = parts[3] ?? "";
  const p4 = parts[4] ?? "";
  const p5 = parts[5] ?? "";
  const p6 = parts[6] ?? "";

  switch (code) {
    case "1":
      return `+${p2}`;
    case "2":
      return p2;
    case "3":
      return `++${p2}`;
    case "5":
      return `+${p2}`;
    case "6":
      return `+${p2}/${p3}`;
    case "7":
      return `-${p2}(${p3})`;
    case "8":
      return `+${p2}[${p3}]`;
    case "9":
      return `+${p2}[${p3}]${p4 ? `_${p4}` : ""}`;
    case "10":
      return `+${p2}${p3 ? `_${p3}` : ""}`;
    case "11":
      return `${p2}(★)`;
    case "12":
      return `${p2}(+${p3})`;
    case "13":
      return "suffix";
    case "14":
      return "SUFFIX";
    case "15":
      return "prefix";
    case "16":
      return "PREFIX";
    case "17": {
      let text = `+${p2}${p3}`;
      if (p4 !== "") {
        text += `[${p4}]`;
      }
      if (p5 !== "") {
        text += `(${p5})`;
      }
      if (p6 !== "") {
        text += `(${p6})`;
      }
      return text;
    }
    case "21":
      return "○";
    case "22":
      return "●";
    case "23":
      return "☆";
    case "24":
      return "★";
    case "25":
      return `★${p2}`;
    case "26":
      return `★[${p2}]`;
    case "27":
      return `★<${p2}>`;
    case "28":
      return `●<<${p2}>>`;
    case "29":
      return `★${p2},[${p3}]`;
    case "30":
      return `α(★<${p2}>);`;
    case "31":
      return `★<${p2}>,[${p3}]`;
    case "32":
      return "▲";
    case "33":
      return `★${p2}`;
    case "34": {
      let text = `★${p2}${p3}`;
      if (p4 !== "") {
        text += `[${p4}]`;
      }
      if (p5 !== "") {
        text += `(${p5})`;
      }
      return text;
    }
    case "51":
      return `<${p2}, ☆>`;
    case "52":
      return `<${p2}, ★>`;
    case "53":
      return `<${p2}, ${p3}>`;
    case "54":
      return bucket === "3"
        ? "<★[Predication], partitioning>"
        : bucket === "2"
          ? "<★[Rel], partitioning>"
          : "<★, partitioning>";
    case "56":
      return `<${p2}, partitioning>`;
    case "58":
      return `<${p2}, ●>`;
    case "59":
      return `<${p2},<${p3},{<${p4}, __>}>>`;
    case "60":
      return `<${p2},<○,{<${p4}, __>}>>`;
    case "61":
      return `<${p2},<●,{<${p4}, __>}>>`;
    case "62":
      return `<${p2},<☆,{<${p4}, __>}>>`;
    case "63":
      return `<${p2},<★,{<${p4}, __>}>>`;
    case "64":
      return `<${p2},<★${p5},{<${p4}, __>}>>`;
    case "70":
      return `●${p2}`;
    case "71":
      return `●<${p2}>`;
    case "101":
      return "Kind";
    case "102":
      return "Bind";
    case "103":
      return p3 === "" ? `β${p2}＝■` : `β${p2}＝${p3}(${p4})`;
    case "106":
      return "pickup";
    case "107":
      return "move";
    default:
      return value;
  }
}

function formatSemanticLikePerl(value: string): string {
  const pos = value.indexOf(":");
  if (pos < 0) {
    return isEncodedFeature(value) ? formatEncodedFeatureLikePerl(value) : value;
  }
  const attribute = value.slice(0, pos).trim();
  const semanticValue = value.slice(pos + 1).trim();
  const formatted = isEncodedFeature(semanticValue)
    ? formatEncodedFeatureLikePerl(semanticValue)
    : semanticValue;
  return `${attribute}: ${formatted}`;
}

function resolveIdSlotLikePerl(idslot: string, xLabel: string): string {
  if (idslot === "id") {
    return xLabel;
  }
  if (idslot === "zero" || idslot === "rel") {
    return "";
  }
  const trimmed = idslot.trim();
  if (trimmed === "") {
    return "";
  }
  if (isEncodedFeature(trimmed)) {
    return formatEncodedFeatureLikePerl(trimmed);
  }
  return trimmed;
}

function buildNumerationText(memo: string, lexicon: string[], plus: string[], idx: string[]): string {
  const line1 = [memo, ...lexicon.slice(0, 30)];
  const line2 = [" ", ...plus.slice(0, 30)];
  const line3 = [" ", ...idx.slice(0, 30)];
  return `${line1.join("\t")}\n${line2.join("\t")}\n${line3.join("\t")}`;
}

function parseTabSeparatedGrid(text: string): string[][] {
  const normalized = text.replace(/\r\n/g, "\n");
  if (normalized === "") {
    return [[""]];
  }
  return normalized.split("\n").map((line) => line.split("\t"));
}

function buildTabSeparatedGrid(rows: string[][]): string {
  return rows.map((row) => row.join("\t")).join("\n");
}

function validateNumerationTabFormat(text: string): string | null {
  const normalized = normalizeNumerationTextForParse(text);
  if (normalized.trim() === "") {
    return "numテキストが空です。";
  }
  const lines = normalized.replace(/\r\n/g, "\n").split("\n");
  if (lines.length < 3) {
    return "numは3行（memo/plus/idx）必要です。";
  }
  const firstThree = lines.slice(0, 3);
  const columnCounts = firstThree.map((line) => line.split("\t").length);
  if (columnCounts.some((count) => count < 2)) {
    return "各行はタブ区切りで2列以上必要です。";
  }
  if (!(columnCounts[0] === columnCounts[1] && columnCounts[1] === columnCounts[2])) {
    return "3行の列数（タブ区切り）が一致していません。";
  }
  return null;
}

function deriveStatus(state: DerivationState | null): "grammatical" | "ungrammatical" | "-" {
  if (!state) {
    return "-";
  }
  const body = JSON.stringify(state.base);
  return /,[0-9]/.test(body) ? "ungrammatical" : "grammatical";
}

function buildFallbackProcessText(state: DerivationState): string {
  const base = Array.from({ length: state.basenum + 1 }, (_, index) => {
    if (index === 0) {
      return null;
    }
    return (state.base as unknown[])[index] ?? null;
  });
  return [
    state.grammar_id,
    state.memo,
    String(state.newnum),
    String(state.basenum),
    state.history,
    JSON.stringify(base),
  ].join("\n");
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

const LEXICON_INSPECT_PAGE_SIZE = 20;
const STEP0_START_DESCRIPTION =
  "Step0では、観察に使う語彙と規則セットを選びます。確認ボタンで中身を見てから開始できます。";

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

function renderTreeGraphSvg(model: TreeRenderModel, testId: string): JSX.Element {
  const nodeById = new Map(model.nodes.map((node) => [node.id, node]));
  return (
    <svg width={model.width} height={model.height} data-testid={testId}>
      {model.edges.map((edge) => {
        const from = nodeById.get(edge.from);
        const to = nodeById.get(edge.to);
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
      {model.nodes.map((node) => (
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
  );
}

export default function App() {
  const [uiMode, setUiMode] = useState<UiMode>("renewed");
  const [legacyFrameReloadTick, setLegacyFrameReloadTick] = useState(0);
  const [renewMenu, setRenewMenu] = useState<RenewMenu>("hypothesis");
  const [renewPanel, setRenewPanel] = useState<RenewPanel>("setup");

  const [grammarOptions, setGrammarOptions] = useState<GrammarOption[]>(DEFAULT_GRAMMARS);
  const [grammarId, setGrammarId] = useState("imi01");
  const [setupGrammarId, setSetupGrammarId] = useState("imi01");
  const [showMoreGrammarOptions, setShowMoreGrammarOptions] = useState(false);
  const [workflowStarted, setWorkflowStarted] = useState(false);
  const [sentence, setSentence] = useState("ジョンが本を読んだ");
  const [step1EntryMode, setStep1EntryMode] = useState<Step1EntryMode>("example_sentence");
  const [step1ExampleNumerationPath, setStep1ExampleNumerationPath] = useState("");
  const [step1ExampleNumerationMemo, setStep1ExampleNumerationMemo] = useState("");
  const [tokenInputMode, setTokenInputMode] = useState<TokenInputMode>("auto");
  const [splitMode, setSplitMode] = useState("C");
  const [autoPreviewTokens, setAutoPreviewTokens] = useState<string[]>([]);
  const [autoPreviewLoading, setAutoPreviewLoading] = useState(false);
  const [manualTokenInput, setManualTokenInput] = useState("ジョンが本を読んだ");
  const [manualTokens, setManualTokens] = useState<string[]>(["ジョンが本を読んだ"]);
  const [isEditingManualTokens, setIsEditingManualTokens] = useState(false);

  const [uploadNumerationText, setUploadNumerationText] = useState("");
  const [step1ExampleNumerationText, setStep1ExampleNumerationText] = useState("");
  const [step1BuildPreviewNumerationText, setStep1BuildPreviewNumerationText] = useState("");
  const [step1BuildPreviewError, setStep1BuildPreviewError] = useState("");
  const [isStep1BuildPreviewLoading, setIsStep1BuildPreviewLoading] = useState(false);
  const [step1UploadFileName, setStep1UploadFileName] = useState("");
  const [step1AutoSupplementNotes, setStep1AutoSupplementNotes] = useState<AutoSupplementNote[]>([]);
  const [numerationText, setNumerationText] = useState("");
  const [numerationEditorPath, setNumerationEditorPath] = useState("");
  const [numerationLexiconRows, setNumerationLexiconRows] = useState<NumerationLexiconRow[]>([]);
  const [isNumerationLexiconLoading, setIsNumerationLexiconLoading] = useState(false);
  const [numerationLexiconError, setNumerationLexiconError] = useState("");
  const [numerationLookupItems, setNumerationLookupItems] = useState<LexiconItemLookupItem[]>([]);
  const [openStep1CandidateSlot, setOpenStep1CandidateSlot] = useState<number | null>(null);
  const [openStep2CandidateSlot, setOpenStep2CandidateSlot] = useState<number | null>(null);
  const [setNumerationFiles, setSetNumerationFiles] = useState<NumerationFileEntry[]>([]);
  const [savedNumerationFiles, setSavedNumerationFiles] = useState<NumerationFileEntry[]>([]);
  const [selectedSetPath, setSelectedSetPath] = useState("");
  const [selectedSavedPath, setSelectedSavedPath] = useState("");

  const [arrangeRows, setArrangeRows] = useState<ArrangeRow[]>([]);
  const [tokenSlotEdits, setTokenSlotEdits] = useState<TokenSlotEdit[]>([]);

  const [generated, setGenerated] = useState<GeneratedNumeration | null>(null);
  const [state, setState] = useState<DerivationState | null>(null);
  const [candidates, setCandidates] = useState<RuleCandidate[]>([]);
  const [step2AllRules, setStep2AllRules] = useState<RuleCandidate[]>([]);
  const [step2RulesLoadedGrammarId, setStep2RulesLoadedGrammarId] = useState("");
  const [isStep2RulesLoading, setIsStep2RulesLoading] = useState(false);
  const [step2RulesError, setStep2RulesError] = useState("");
  const [reachabilityResult, setReachabilityResult] = useState<ReachabilityResponse | null>(null);
  const [reachabilityRows, setReachabilityRows] = useState<ReachabilityEvidence[]>([]);
  const [reachabilityJobId, setReachabilityJobId] = useState("");
  const [reachabilityMessage, setReachabilityMessage] = useState("");
  const [reachabilityProgress, setReachabilityProgress] = useState<{ percent: number; phase: string; message: string } | null>(null);
  const [reachabilityOffset, setReachabilityOffset] = useState(0);
  const [reachabilityLimit, setReachabilityLimit] = useState(10);
  const [openReachabilityFirstStepKey, setOpenReachabilityFirstStepKey] = useState<string | null>(null);
  const [step2ProcessText, setStep2ProcessText] = useState("");
  const [step2UndoStack, setStep2UndoStack] = useState<DerivationState[]>([]);
  const [selectedLeft, setSelectedLeft] = useState<number | null>(null);
  const [selectedRight, setSelectedRight] = useState<number | null>(null);
  const [isStep2CandidatesLoading, setIsStep2CandidatesLoading] = useState(false);
  const [lexiconFocusLexiconId, setLexiconFocusLexiconId] = useState<number | null>(null);
  const [lexiconFocusRequestSeq, setLexiconFocusRequestSeq] = useState(0);

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
  const [referenceDocTab, setReferenceDocTab] = useState<ReferenceDocTab>("feature");
  const [referenceDocsLoadedGrammarId, setReferenceDocsLoadedGrammarId] = useState("");
  const [inspectLexiconSummary, setInspectLexiconSummary] = useState<LexiconSummaryResponse | null>(null);
  const [inspectLexiconItems, setInspectLexiconItems] = useState<LexiconItemsPageResponse | null>(null);
  const [inspectLexiconPage, setInspectLexiconPage] = useState(1);
  const [inspectLexiconCategoryFilter, setInspectLexiconCategoryFilter] = useState<string | null>(null);
  const [inspectMergeRules, setInspectMergeRules] = useState<MergeRuleEntry[]>([]);
  const [inspectRuleCompare, setInspectRuleCompare] = useState<RuleCompareResponse | null>(null);
  const [inspectCompareRuleNumber, setInspectCompareRuleNumber] = useState<number | null>(null);
  const [inspectMergeRulesLoadedGrammarId, setInspectMergeRulesLoadedGrammarId] = useState("");

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
  const [uiPersistenceReady, setUiPersistenceReady] = useState(!ENABLE_UI_PERSISTENCE);
  const referenceSectionRef = useRef<HTMLElement | null>(null);
  const step1UploadFileInputRef = useRef<HTMLInputElement | null>(null);
  const numerationEditorFileInputRef = useRef<HTMLInputElement | null>(null);
  const autoPreviewRequestSeqRef = useRef(0);
  const numLookupRequestSeqRef = useRef(0);
  const step1BuildPreviewRequestSeqRef = useRef(0);
  const step2AutoCandidatesRequestSeqRef = useRef(0);
  const step2AutoCandidatesRequestKeyRef = useRef("");
  const step2ProcessRequestSeqRef = useRef(0);
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
  const primaryGrammarOptions = useMemo(() => {
    const preferredOrder = ["imi01", "imi02", "imi03"];
    const byId = new Map(grammarOptions.map((option) => [option.grammar_id, option]));
    const preferred = preferredOrder
      .map((grammarKey) => byId.get(grammarKey))
      .filter((option): option is GrammarOption => Boolean(option));
    if (preferred.length === 3) {
      return preferred;
    }
    return grammarOptions.slice(0, 3);
  }, [grammarOptions]);
  const shownStep0GrammarOptions = useMemo(() => {
    if (showMoreGrammarOptions) {
      return grammarOptions;
    }
    return primaryGrammarOptions;
  }, [grammarOptions, primaryGrammarOptions, showMoreGrammarOptions]);
  const activeSetupGrammarOption = useMemo(
    () => grammarOptions.find((option) => option.grammar_id === setupGrammarId) || null,
    [grammarOptions, setupGrammarId]
  );
  const step1UploadFormatError = useMemo(
    () => validateNumerationTabFormat(uploadNumerationText),
    [uploadNumerationText]
  );
  const step1NumerationLexiconSourceText = useMemo(() => {
    if (renewPanel === "numeration") {
      return numerationText;
    }
    if (step1EntryMode === "upload_num") {
      return uploadNumerationText;
    }
    if (step1EntryMode === "example_sentence") {
      return step1ExampleNumerationText;
    }
    if (step1EntryMode === "build_lexicon") {
      return step1BuildPreviewNumerationText;
    }
    return "";
  }, [
    numerationText,
    renewPanel,
    step1BuildPreviewNumerationText,
    step1EntryMode,
    step1ExampleNumerationText,
    uploadNumerationText
  ]);
  const step1NumerationRows = useMemo(
    () => parseNumerationLexiconRows(normalizeNumerationTextForParse(step1NumerationLexiconSourceText)),
    [step1NumerationLexiconSourceText]
  );
  const step1NumerationLexiconSourceTextForDisplay = useMemo(
    () => encodeNumerationTextLikePerl(step1NumerationLexiconSourceText),
    [step1NumerationLexiconSourceText]
  );
  const numerationEditorGrid = useMemo(() => parseTabSeparatedGrid(numerationText), [numerationText]);
  const numerationEditorGridColumnCount = useMemo(
    () => Math.max(8, ...numerationEditorGrid.map((row) => Math.max(1, row.length))),
    [numerationEditorGrid]
  );
  const tokenSlotEditBySlot = useMemo(() => {
    const bySlot = new Map<number, TokenSlotEdit>();
    for (const row of tokenSlotEdits) {
      bySlot.set(row.slot, row);
    }
    return bySlot;
  }, [tokenSlotEdits]);
  const reachabilityDisplayGroups = useMemo<ReachabilityDisplayGroup[]>(() => {
    const grouped = new Map<string, ReachabilityEvidence[]>();
    for (const row of reachabilityRows) {
      const key = buildReachabilityFirstStepKey(row);
      const existing = grouped.get(key);
      if (existing) {
        existing.push(row);
      } else {
        grouped.set(key, [row]);
      }
    }
    const groups: ReachabilityDisplayGroup[] = [];
    for (const [firstStepKey, rows] of grouped.entries()) {
      const sorted = [...rows].sort((a, b) => {
        if (a.steps_to_goal !== b.steps_to_goal) {
          return a.steps_to_goal - b.steps_to_goal;
        }
        return a.rank - b.rank;
      });
      groups.push({
        firstStepKey,
        representative: sorted[0],
        options: sorted
      });
    }
    groups.sort((a, b) => a.representative.rank - b.representative.rank);
    return groups;
  }, [reachabilityRows]);
  const numerationLookupMap = useMemo(() => {
    const byId = new Map<number, LexiconItemLookupItem>();
    for (const item of numerationLookupItems) {
      byId.set(item.lexicon_id, item);
    }
    return byId;
  }, [numerationLookupItems]);

  useEffect(() => {
    if (openReachabilityFirstStepKey === null) {
      return;
    }
    const exists = reachabilityDisplayGroups.some((group) => group.firstStepKey === openReachabilityFirstStepKey);
    if (!exists) {
      setOpenReachabilityFirstStepKey(null);
    }
  }, [openReachabilityFirstStepKey, reachabilityDisplayGroups]);
  const step1PartnerWarnings = useMemo(() => {
    const slotCandidates = numerationLexiconRows.map((row) => {
      const slotEdit = tokenSlotEditBySlot.get(row.slot);
      const includeSlotCandidates =
        step1EntryMode === "build_lexicon" || step1EntryMode === "example_sentence";
      const candidateIds = Array.from(
        new Set(
          [
            ...(row.lexiconId && row.lexiconId > 0 ? [row.lexiconId] : []),
            ...(
              includeSlotCandidates
                ? (slotEdit?.candidateLexiconIds || []).filter(
                  (candidateId) => Number.isInteger(candidateId) && candidateId > 0
                )
                : []
            ),
          ].filter((candidateId): candidateId is number => Number.isInteger(candidateId) && candidateId > 0)
        )
      );
      const selectedLexiconId = includeSlotCandidates
        ? slotEdit?.selectedLexiconId ?? row.lexiconId ?? null
        : row.lexiconId ?? null;
      return {
        slot: row.slot,
        selectedLexiconId,
        candidateIds,
      };
    });

    const capabilityByLexiconId = new Map<number, { plain: Set<string>; labeled: Set<string> }>();
    const requirementsByLexiconId = new Map<number, PartnerRequirement[]>();

    function getCapability(lexiconId: number): { plain: Set<string>; labeled: Set<string> } {
      if (capabilityByLexiconId.has(lexiconId)) {
        return capabilityByLexiconId.get(lexiconId)!;
      }
      const lookup = numerationLookupMap.get(lexiconId);
      const capability = parsePartnerCapabilitiesFromSyncFeatures(lookup?.sync_features || []);
      capabilityByLexiconId.set(lexiconId, capability);
      return capability;
    }

    function getRequirements(lexiconId: number): PartnerRequirement[] {
      if (requirementsByLexiconId.has(lexiconId)) {
        return requirementsByLexiconId.get(lexiconId)!;
      }
      const lookup = numerationLookupMap.get(lexiconId);
      const requirements = parsePartnerRequirementsFromSemantics(lookup?.semantics || []);
      requirementsByLexiconId.set(lexiconId, requirements);
      return requirements;
    }

    function requirementSatisfied(
      requirement: PartnerRequirement,
      capability: { plain: Set<string>; labeled: Set<string> }
    ): boolean {
      if (requirement.featureCode === "25") {
        return capability.plain.has(requirement.label);
      }
      return capability.labeled.has(requirement.label);
    }

    const warnings: Step1PartnerWarning[] = [];
    for (const source of slotCandidates) {
      if (!source.selectedLexiconId || source.selectedLexiconId <= 0) {
        continue;
      }
      const sourceLookup = numerationLookupMap.get(source.selectedLexiconId);
      if (!sourceLookup) {
        continue;
      }
      const requirements = getRequirements(source.selectedLexiconId);
      if (requirements.length === 0) {
        continue;
      }

      for (const requirement of requirements) {
        const selectedProviderSlots = slotCandidates
          .filter((candidate) => candidate.slot !== source.slot && candidate.selectedLexiconId !== null)
          .filter((candidate) =>
            requirementSatisfied(requirement, getCapability(candidate.selectedLexiconId!))
          )
          .map((candidate) => candidate.slot);
        if (selectedProviderSlots.length > 0) {
          continue;
        }

        const possibleProviderSlots = slotCandidates
          .filter((candidate) => candidate.slot !== source.slot)
          .filter((candidate) =>
            candidate.candidateIds.some((candidateId) =>
              requirementSatisfied(requirement, getCapability(candidateId))
            )
          )
          .map((candidate) => candidate.slot);

        warnings.push({
          level: possibleProviderSlots.length > 0 ? "possible" : "impossible",
          slot: source.slot,
          selectedLexiconId: source.selectedLexiconId,
          selectedEntry: sourceLookup.entry,
          requirement,
          providerSlots: Array.from(new Set(possibleProviderSlots)),
        });
      }
    }

    return warnings;
  }, [numerationLexiconRows, numerationLookupMap, step1EntryMode, tokenSlotEditBySlot]);
  useEffect(() => {
    if (!ENABLE_UI_PERSISTENCE) {
      return;
    }
    try {
      const raw = window.localStorage.getItem(UI_PERSISTENCE_KEY);
      if (!raw) {
        return;
      }
      const parsed = JSON.parse(raw) as Partial<PersistedUiState>;
      if (parsed.uiMode === "legacy" || parsed.uiMode === "renewed") {
        setUiMode(parsed.uiMode);
      }
      if (typeof parsed.workflowStarted === "boolean") {
        setWorkflowStarted(parsed.workflowStarted);
      }
      if (typeof parsed.grammarId === "string" && parsed.grammarId.trim() !== "") {
        setGrammarId(parsed.grammarId);
      }
      if (typeof parsed.setupGrammarId === "string" && parsed.setupGrammarId.trim() !== "") {
        setSetupGrammarId(parsed.setupGrammarId);
      }
      if (
        parsed.step1EntryMode === "example_sentence" ||
        parsed.step1EntryMode === "upload_num" ||
        parsed.step1EntryMode === "build_lexicon"
      ) {
        setStep1EntryMode(parsed.step1EntryMode);
      }
      if (
        parsed.renewPanel &&
        RENEW_MENUS.some((menu) => menu.steps.some((step) => step.key === parsed.renewPanel))
      ) {
        setRenewPanel(parsed.renewPanel);
      }
    } catch {
      // localStorageが壊れている場合は既定値で続行する。
    } finally {
      setUiPersistenceReady(true);
    }
  }, []);

  useEffect(() => {
    const owner = RENEW_MENUS.find((menu) => menu.steps.some((step) => step.key === renewPanel));
    if (owner && owner.key !== renewMenu) {
      setRenewMenu(owner.key);
    }
  }, [renewMenu, renewPanel]);

  useEffect(() => {
    if (!ENABLE_UI_PERSISTENCE || !uiPersistenceReady) {
      return;
    }
    const payload: PersistedUiState = {
      uiMode,
      renewPanel,
      workflowStarted,
      grammarId,
      setupGrammarId,
      step1EntryMode
    };
    try {
      window.localStorage.setItem(UI_PERSISTENCE_KEY, JSON.stringify(payload));
    } catch {
      // 保存できない環境では無視する。
    }
  }, [grammarId, renewPanel, setupGrammarId, step1EntryMode, uiMode, uiPersistenceReady, workflowStarted]);

  useEffect(() => {
    const targetGrammarId = state?.grammar_id || grammarId;
    if (!targetGrammarId) {
      return;
    }
    if (step2RulesLoadedGrammarId === targetGrammarId) {
      return;
    }

    let cancelled = false;
    setIsStep2RulesLoading(true);
    setStep2RulesError("");
    void (async () => {
      try {
        const rows = await apiGet<RuleCandidate[]>(`/v1/derivation/rules/${targetGrammarId}`);
        if (cancelled) {
          return;
        }
        setStep2AllRules(rows);
        setStep2RulesLoadedGrammarId(targetGrammarId);
        setStep2RulesError("");
      } catch (ruleError) {
        if (cancelled) {
          return;
        }
        setStep2AllRules([]);
        setStep2RulesLoadedGrammarId(targetGrammarId);
        setStep2RulesError(
          ruleError instanceof Error ? ruleError.message : "ルール一覧の取得に失敗しました。"
        );
      } finally {
        if (!cancelled) {
          setIsStep2RulesLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [grammarId, state?.grammar_id, step2RulesLoadedGrammarId]);

  const step2DisplayRows = useMemo(() => buildStep2DisplayRows(state), [state]);
  const step2RuleRows = useMemo(() => {
    const fallbackRules = Array.from(
      new Map(
        candidates.map((candidate) => [
          candidate.rule_number,
          {
            rule_number: candidate.rule_number,
            rule_name: candidate.rule_name,
            rule_kind: candidate.rule_kind
          } as RuleCandidate
        ])
      ).values()
    );
    const allRules = step2AllRules.length > 0 ? step2AllRules : fallbackRules;
    const candidatesByRule = new Map<number, RuleCandidate[]>();
    for (const candidate of candidates) {
      const rows = candidatesByRule.get(candidate.rule_number) || [];
      rows.push(candidate);
      candidatesByRule.set(candidate.rule_number, rows);
    }

    return allRules
      .map((rule) => {
        const applicableRows = candidatesByRule.get(rule.rule_number) || [];
        const executableCandidate = applicableRows[0] || null;
        const executable = executableCandidate !== null;
        let reason = "";
        if (!state) {
          reason = "state を初期化してください。";
        } else if (selectedLeft === null || selectedRight === null) {
          reason = "left / right を選択してください。";
        } else if (selectedLeft === selectedRight) {
          reason = "left と right は別の行を選択してください。";
        } else if (
          selectedLeft < 1 ||
          selectedRight < 1 ||
          selectedLeft > state.basenum ||
          selectedRight > state.basenum
        ) {
          reason = "left / right の選択が範囲外です。";
        } else if (isStep2CandidatesLoading) {
          reason = "left / right に対する適用可否を判定中です。";
        } else if (!executable) {
          reason = `選択中の left / right では ${rule.rule_name} を適用できません。`;
        }

        let argsLabel = "";
        if (executableCandidate) {
          if (executableCandidate.rule_kind === "single") {
            argsLabel = `check=${executableCandidate.check ?? "-"}`;
          } else {
            argsLabel = `L=${executableCandidate.left ?? selectedLeft ?? "-"}, R=${executableCandidate.right ?? selectedRight ?? "-"}`;
          }
        } else if (rule.rule_kind === "single") {
          argsLabel = "check=-";
        } else {
          argsLabel = `L=${selectedLeft ?? "-"}, R=${selectedRight ?? "-"}`;
        }

        return {
          rule,
          executable,
          executableCandidate,
          reason,
          argsLabel
        };
      })
      .sort((a, b) => {
        if (a.executable !== b.executable) {
          return a.executable ? -1 : 1;
        }
        return a.rule.rule_number - b.rule.rule_number;
      });
  }, [candidates, isStep2CandidatesLoading, selectedLeft, selectedRight, state, step2AllRules]);

  function renderStep2DisplayNode(
    node: Step2DisplayNode,
    rowSlot: number,
    keyPath: string,
    depth: number
  ): JSX.Element {
    const syValues = node.syncFeatures.filter((feature) => feature.trim() !== "");
    const semanticValues = node.semantics.filter((semantic) => semantic.trim() !== "");
    const idslotRaw = node.idslot.trim();

    return (
      <>
        {node.unresolvedMessage ? (
          <div
            className={depth === 0
              ? "numeration-legacy-topline step2-parent-topline"
              : "numeration-legacy-topline step2-child-topline"}
            style={depth > 0 ? { paddingLeft: `${depth * 20}px` } : undefined}
          >
            <span className="perl-f0">{node.xLabel}</span>
            <span className="perl-f1">-</span>
            <span className="numeration-legacy-unresolved">{node.unresolvedMessage}</span>
          </div>
        ) : (
          <div
            className={depth === 0
              ? "numeration-legacy-topline step2-parent-topline"
              : "numeration-legacy-topline step2-child-topline"}
            style={depth > 0 ? { paddingLeft: `${depth * 20}px` } : undefined}
          >
            <span className="perl-f0">{node.xLabel}</span>
            <span className="perl-f1">{node.category || "-"}</span>
            {syValues.map((feature, featureIdx) => (
              <span className="perl-f3" key={`${keyPath}-sy-${featureIdx}`}>
                {renderEncodedFeatureLikePerl(feature, `${rowSlot}-step2-${keyPath}-sy-${featureIdx}`)}
              </span>
            ))}
            {idslotRaw === "id" && <span className="perl-f4">{node.xLabel}</span>}
            {idslotRaw !== "" && idslotRaw !== "id" && idslotRaw !== "zero" && idslotRaw !== "rel" && (
              <span className="perl-f4">
                {isEncodedFeature(idslotRaw)
                  ? renderEncodedFeatureLikePerl(idslotRaw, `${rowSlot}-step2-${keyPath}-sl`)
                  : idslotRaw}
              </span>
            )}
            {semanticValues.map((semantic, semIdx) => {
              const pos = semantic.indexOf(":");
              const attribute = pos >= 0 ? semantic.slice(0, pos).trim() : "";
              const rawValue = pos >= 0 ? semantic.slice(pos + 1).trim() : semantic.trim();
              return (
                <span className="perl-f5" key={`${keyPath}-se-${semIdx}`}>
                  {attribute !== "" ? `${attribute}: ` : ""}
                  {isEncodedFeature(rawValue)
                    ? renderEncodedFeatureLikePerl(rawValue, `${rowSlot}-step2-${keyPath}-se-${semIdx}`)
                    : rawValue}
                </span>
              );
            })}
            {node.phono !== "" && <span className="perl-f6">{node.phono}</span>}
          </div>
        )}
        {node.children.map((child, childIndex) => (
          <div className="step2-child-block" key={`${keyPath}-child-${childIndex}`}>
            {renderStep2DisplayNode(child, rowSlot, `${keyPath}-${childIndex}`, depth + 1)}
          </div>
        ))}
      </>
    );
  }

  function buildNumerationLexiconRows(
    parsedRows: Pick<
      NumerationLexiconRow,
      "slot" | "rawLexiconId" | "lexiconId" | "plus" | "idx"
    >[],
    lookupMap: Map<number, LexiconItemLookupItem>
  ): NumerationLexiconRow[] {
    return parsedRows.map((row) => {
      if (row.lexiconId === null) {
        return {
          ...row,
          found: null,
          entry: "",
          phono: "",
          category: "",
          syncFeatures: [],
          idslot: "",
          semantics: [],
          note: ""
        };
      }
      const lookup = lookupMap.get(row.lexiconId);
      if (!lookup) {
        return {
          ...row,
          found: null,
          entry: "",
          phono: "",
          category: "",
          syncFeatures: [],
          idslot: "",
          semantics: [],
          note: ""
        };
      }
      return {
        ...row,
        found: lookup.found,
        entry: lookup.entry,
        phono: lookup.phono,
        category: lookup.category,
        syncFeatures: lookup.sync_features,
        idslot: lookup.idslot,
        semantics: lookup.semantics,
        note: lookup.note
      };
    });
  }

  const loadLookupRowsForNumerationText = async (sourceText: string) => {
    const parsedRows = parseNumerationLexiconRows(normalizeNumerationTextForParse(sourceText));
    const rowIds = parsedRows
      .map((row) => row.lexiconId)
      .filter((value): value is number => value !== null);
    const includeTokenCandidates =
      step1EntryMode === "build_lexicon" || step1EntryMode === "example_sentence";
    const candidateIds = includeTokenCandidates
      ? parsedRows.flatMap((row) => tokenSlotEditBySlot.get(row.slot)?.candidateLexiconIds || [])
      : [];
    const uniqueIds = Array.from(
      new Set(
        [...rowIds, ...candidateIds].filter(
          (value): value is number => Number.isInteger(value) && Number(value) > 0
        )
      )
    );
    if (uniqueIds.length === 0) {
      setNumerationLookupItems([]);
      setNumerationLexiconRows(buildNumerationLexiconRows(parsedRows, new Map()));
      const hasInvalidIds = parsedRows.some((row) => row.lexiconId === null);
      setNumerationLexiconError(
        hasInvalidIds ? "語彙IDが数値ではありません（対象行は補足表示）。" : ""
      );
      return;
    }

    const requestId = numLookupRequestSeqRef.current + 1;
    numLookupRequestSeqRef.current = requestId;
    setIsNumerationLexiconLoading(true);
    setNumerationLexiconError("");
    try {
      const response = await apiPost<LexiconItemsLookupResponse>(
        `/v1/reference/grammars/${grammarId}/lexicon-items/by-ids`,
        { ids: uniqueIds }
      );
      if (numLookupRequestSeqRef.current !== requestId) {
        return;
      }
      const lookupMap = new Map<number, LexiconItemLookupItem>();
      for (const item of response.items) {
        lookupMap.set(item.lexicon_id, item);
      }
      setNumerationLookupItems(response.items);
      setNumerationLexiconRows(buildNumerationLexiconRows(parsedRows, lookupMap));
      if (response.missing_ids.length > 0 && response.found_count < response.requested_count) {
        setNumerationLexiconError(
          `語彙ID が見つかりませんでした: ${response.missing_ids.join(", ")}`
        );
      } else {
        setNumerationLexiconError("");
      }
    } catch (lookupError) {
      setNumerationLookupItems([]);
      setNumerationLexiconRows(buildNumerationLexiconRows(parsedRows, new Map()));
      setNumerationLexiconError(
        lookupError instanceof Error ? lookupError.message : "語彙IDの参照に失敗しました。"
      );
    } finally {
      if (numLookupRequestSeqRef.current === requestId) {
        setIsNumerationLexiconLoading(false);
      }
    }
  };

  useEffect(() => {
    if (step1NumerationLexiconSourceText.trim() === "") {
      setNumerationLexiconRows([]);
      setNumerationLookupItems([]);
      setNumerationLexiconError("");
      setIsNumerationLexiconLoading(false);
      return;
    }
    const timer = setTimeout(() => {
      void loadLookupRowsForNumerationText(step1NumerationLexiconSourceText);
    }, 250);
    return () => {
      clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [grammarId, step1EntryMode, step1NumerationRows, step1NumerationLexiconSourceText, tokenSlotEdits]);

  useEffect(() => {
    if (openStep1CandidateSlot === null) {
      return;
    }
    if (!numerationLexiconRows.some((row) => row.slot === openStep1CandidateSlot)) {
      setOpenStep1CandidateSlot(null);
    }
  }, [numerationLexiconRows, openStep1CandidateSlot]);

  useEffect(() => {
    if (openStep2CandidateSlot === null) {
      return;
    }
    if (!step2DisplayRows.some((row) => row.slot === openStep2CandidateSlot)) {
      setOpenStep2CandidateSlot(null);
    }
  }, [openStep2CandidateSlot, step2DisplayRows]);

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

  useEffect(() => {
    if (step1EntryMode !== "build_lexicon") {
      setStep1BuildPreviewNumerationText("");
      setStep1BuildPreviewError("");
      setIsStep1BuildPreviewLoading(false);
      return;
    }
    if (sentence.trim() === "") {
      setStep1BuildPreviewNumerationText("");
      setStep1BuildPreviewError("");
      setIsStep1BuildPreviewLoading(false);
      return;
    }

    const requestId = step1BuildPreviewRequestSeqRef.current + 1;
    step1BuildPreviewRequestSeqRef.current = requestId;
    setIsStep1BuildPreviewLoading(true);

    const tokensForRequest = tokenInputMode === "manual" ? resolveManualTokensForSubmit() : undefined;
    void (async () => {
      try {
        const response = await apiPost<GeneratedNumeration>("/v1/derivation/numeration/generate", {
          grammar_id: grammarId,
          sentence,
          tokens: tokensForRequest,
          split_mode: splitMode
        });
        if (step1BuildPreviewRequestSeqRef.current !== requestId) {
          return;
        }
        setStep1BuildPreviewNumerationText(response.numeration_text);
        syncTokenEdits(response);
        setStep1AutoSupplementNotes(response.auto_supplements || []);
        setStep1BuildPreviewError("");
      } catch (previewError) {
        if (step1BuildPreviewRequestSeqRef.current !== requestId) {
          return;
        }
        setStep1BuildPreviewNumerationText("");
        setStep1AutoSupplementNotes([]);
        setStep1BuildPreviewError(
          previewError instanceof Error ? previewError.message : "語彙候補の計算に失敗しました。"
        );
      } finally {
        if (step1BuildPreviewRequestSeqRef.current === requestId) {
          setIsStep1BuildPreviewLoading(false);
        }
      }
    })();
  }, [grammarId, manualTokenInput, manualTokens, sentence, splitMode, step1EntryMode, tokenInputMode]);

  function parseManualTokenInput(input: string): string[] {
    const trimmed = input.trim();
    if (trimmed === "") {
      return [];
    }
    return parseManualTokens(trimmed) || [];
  }

  function resolveManualTokensForSubmit(): string[] | undefined {
    if (tokenInputMode !== "manual") {
      return undefined;
    }
    const parsed = parseManualTokenInput(manualTokenInput);
    if (parsed.length > 0) {
      return parsed;
    }
    const rawSentence = sentence.trim();
    return rawSentence === "" ? undefined : [rawSentence];
  }

  function startManualTokenEdit() {
    if (tokenInputMode !== "manual") {
      return;
    }
    setIsEditingManualTokens(true);
    setManualTokenInput(manualTokens.join(", "));
  }

  function commitManualTokenEdit() {
    const candidate = parseManualTokenInput(manualTokenInput);
    if (candidate.length > 0) {
      setManualTokens(candidate);
      setManualTokenInput(candidate.join(", "));
    } else {
      const rawSentence = sentence.trim();
      setManualTokens(rawSentence === "" ? [] : [rawSentence]);
      setManualTokenInput(rawSentence);
    }
    setIsEditingManualTokens(false);
  }

  function syncTokenEdits(response: GeneratedNumeration) {
    const edits: TokenSlotEdit[] = response.token_resolutions.map((row, index) => ({
      slot: index + 1,
      token: row.token,
      selectedLexiconId: row.lexicon_id,
      candidateLexiconIds: row.candidate_lexicon_ids,
      candidateCompatibilityById: normalizeTokenCandidateCompatibility(row),
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

  async function handleOpenLexiconInspect(
    grammarKey: string,
    page = 1,
    categoryFilter: string | null = inspectLexiconCategoryFilter
  ) {
    const targetPage = Math.max(1, page);
    await withLoading(async () => {
      const categoryQuery =
        categoryFilter && categoryFilter.trim() !== ""
          ? `&category=${encodeURIComponent(categoryFilter)}`
          : "";
      const [summary, pageResponse] = await Promise.all([
        apiGet<LexiconSummaryResponse>(`/v1/reference/grammars/${grammarKey}/lexicon-summary`),
        apiGet<LexiconItemsPageResponse>(
          `/v1/reference/grammars/${grammarKey}/lexicon-items?page=${targetPage}&page_size=${LEXICON_INSPECT_PAGE_SIZE}${categoryQuery}`
        )
      ]);
      setInspectLexiconSummary(summary);
      setInspectLexiconItems(pageResponse);
      setInspectLexiconPage(pageResponse.page);
      setInspectLexiconCategoryFilter(pageResponse.category_filter || null);
      setRenewMenu("reference");
      setRenewPanel("lexiconInspect");
      setUiMode("renewed");
    });
  }

  async function handleOpenGrammarInspect(grammarKey: string) {
    await withLoading(async () => {
      const rows = await apiGet<MergeRuleEntry[]>(`/v1/reference/grammars/${grammarKey}/merge-rules`);
      setInspectMergeRules(rows);
      setInspectMergeRulesLoadedGrammarId(grammarKey);
      setInspectRuleCompare(null);
      const firstRule = rows[0];
      if (firstRule) {
        setInspectCompareRuleNumber(firstRule.rule_number);
      }
      setRenewMenu("reference");
      setRenewPanel("grammarInspect");
      setUiMode("renewed");
    });
  }

  async function handleOpenRuleCompare(grammarKey: string, ruleNumber: number) {
    await withLoading(async () => {
      const compare = await apiGet<RuleCompareResponse>(
        `/v1/reference/grammars/${grammarKey}/rule-compare/${ruleNumber}`
      );
      setInspectRuleCompare(compare);
      setInspectCompareRuleNumber(ruleNumber);
      setRenewMenu("reference");
      setRenewPanel("ruleCompare");
      setUiMode("renewed");
    });
  }

  function handleStartHypothesisLoop() {
    setGrammarId(setupGrammarId);
    setReferenceDocsLoadedGrammarId("");
    setInspectMergeRulesLoadedGrammarId("");
    setWorkflowStarted(true);
    setRenewMenu("hypothesis");
    setRenewPanel("sentence");
    void handleLoadNumerationFiles("set", setupGrammarId);
    void handleLoadNumerationFiles("saved", setupGrammarId);
  }

  function handleSelectStep1EntryMode(mode: Step1EntryMode) {
    if (mode === "build_lexicon" && step1EntryMode === "example_sentence") {
      if (step1ExampleNumerationMemo.trim() !== "") {
        setSentence(step1ExampleNumerationMemo);
      }
    }
    setStep1EntryMode(mode);
    if (mode === "example_sentence") {
      setStep1ExampleNumerationText("");
      setNumerationLexiconRows([]);
      setNumerationLexiconError("");
      setTokenSlotEdits([]);
      setGenerated(null);
      setStep1AutoSupplementNotes([]);
      setOpenStep1CandidateSlot(null);
      if (setNumerationFiles.length === 0) {
        setStep1ExampleNumerationPath("");
      } else if (
        step1ExampleNumerationPath === "" ||
        setNumerationFiles.findIndex((row) => row.path === step1ExampleNumerationPath) < 0
      ) {
        setStep1ExampleNumerationPath(setNumerationFiles[0].path);
      }
    }
    if (mode === "upload_num") {
      setNumerationLexiconRows([]);
      setNumerationLexiconError("");
      setTokenSlotEdits([]);
      setGenerated(null);
      setStep1AutoSupplementNotes([]);
      setOpenStep1CandidateSlot(null);
    }
    if (mode === "build_lexicon") {
      setTokenInputMode("auto");
      const rawSentence = sentence.trim();
      setManualTokens(rawSentence === "" ? [] : [rawSentence]);
      setManualTokenInput(rawSentence);
      setIsEditingManualTokens(false);
    }
  }

  function handleChangeStep1ExampleNumerationPath(value: string) {
    setStep1ExampleNumerationPath(value);
    setStep1ExampleNumerationText("");
    setTokenSlotEdits([]);
    setNumerationLexiconRows([]);
    setNumerationLexiconError("");
  }

  async function syncTokenEditsFromNumerationSourceText(sourceText: string) {
    const normalized = normalizeNumerationTextForParse(sourceText);
    const parsedRows = parseNumerationLexiconRows(normalized);
    const parsedBySlot = new Map(parsedRows.map((row) => [row.slot, row]));
    if (parsedRows.length === 0) {
      setTokenSlotEdits([]);
      return;
    }
    const response = await apiPost<{ token_resolutions: NumerationTokenResolution[] }>(
      "/v1/derivation/numeration/candidates-from-num",
      {
        grammar_id: grammarId,
        numeration_text: normalized
      }
    );
    const edits: TokenSlotEdit[] = response.token_resolutions.map((row) => {
      const parsed = parsedBySlot.get(row.slot);
      return {
        slot: row.slot,
        token: row.token,
        selectedLexiconId: row.lexicon_id,
        candidateLexiconIds: row.candidate_lexicon_ids,
        candidateCompatibilityById: normalizeTokenCandidateCompatibility({
          token: row.token,
          lexicon_id: row.lexicon_id,
          candidate_lexicon_ids: row.candidate_lexicon_ids,
          candidate_compatibility: row.candidate_compatibility || []
        }),
        plusValue: parsed?.plus ?? "",
        idxValue: parsed?.idx || String(row.slot)
      };
    });
    setTokenSlotEdits(edits);
  }

  async function handleLoadStep1ExampleNumerationByPath(path: string) {
    if (path.trim() === "") {
      setStep1ExampleNumerationText("");
      return;
    }
    try {
      const response = await apiPost<{ path: string; numeration_text: string; memo: string }>(
        "/v1/derivation/numeration/load",
        {
          grammar_id: grammarId,
          path
        }
      );
      setStep1ExampleNumerationText(response.numeration_text);
      setSentence(response.memo || sentence);
      setStep1ExampleNumerationMemo(response.memo || response.numeration_text?.split("\t")?.[0] || "");
      setStep1AutoSupplementNotes([]);
      setNumerationLexiconError("");
      await syncTokenEditsFromNumerationSourceText(response.numeration_text);
    } catch {
      setStep1ExampleNumerationText("");
      setStep1ExampleNumerationMemo("");
      setTokenSlotEdits([]);
      setNumerationLexiconError("選択した .num を読み込めませんでした。");
    }
  }

  async function handleStep1UploadFile(file: File | null) {
    if (!file) {
      return;
    }
    try {
      const text = await file.text();
      setUploadNumerationText(text);
      setStep1UploadFileName(file.name);
    } catch {
      setError("numファイルの読み込みに失敗しました。");
    }
  }

  useEffect(() => {
    const rawSentence = sentence.trim();
    setManualTokens(rawSentence === "" ? [] : [rawSentence]);
    setManualTokenInput(rawSentence);
    setIsEditingManualTokens(false);
  }, [sentence]);

  useEffect(() => {
    setReachabilityResult(null);
    setReachabilityRows([]);
    setReachabilityJobId("");
    setReachabilityProgress(null);
    setReachabilityMessage("");
    setReachabilityOffset(0);
  }, [state]);

  useEffect(() => {
    if (!state) {
      setStep2ProcessText("");
      return;
    }
    const requestSeq = step2ProcessRequestSeqRef.current + 1;
    step2ProcessRequestSeqRef.current = requestSeq;

    void (async () => {
      try {
        const response = await apiPost<ProcessExportResponse>("/v1/derivation/process/export", {
          state
        });
        if (requestSeq !== step2ProcessRequestSeqRef.current) {
          return;
        }
        setStep2ProcessText(response.process_text);
      } catch {
        if (requestSeq !== step2ProcessRequestSeqRef.current) {
          return;
        }
        setStep2ProcessText(buildFallbackProcessText(state));
      }
    })();
  }, [state]);

  function handleOpenStep1UploadPicker() {
    if (!step1UploadFileInputRef.current) {
      return;
    }
    step1UploadFileInputRef.current.value = "";
    step1UploadFileInputRef.current.click();
  }

  function handleOpenNumerationEditorPicker() {
    if (!numerationEditorFileInputRef.current) {
      return;
    }
    numerationEditorFileInputRef.current.value = "";
    numerationEditorFileInputRef.current.click();
  }

  async function handleNumerationEditorUploadFile(file: File | null) {
    if (!file) {
      return;
    }
    try {
      const text = await file.text();
      setNumerationText(text);
      setNumerationEditorPath(`(アップロード) ${file.name}`);
      setError(null);
    } catch {
      setError("numファイルの読み込みに失敗しました。");
    }
  }

  function handleUpdateNumerationGridCell(rowIndex: number, columnIndex: number, value: string) {
    setNumerationText((prev) => {
      const grid = parseTabSeparatedGrid(prev);
      while (grid.length <= rowIndex) {
        grid.push([""]);
      }
      while (grid[rowIndex].length <= columnIndex) {
        grid[rowIndex].push("");
      }
      grid[rowIndex][columnIndex] = value;
      return buildTabSeparatedGrid(grid);
    });
  }

  async function handleOpenAutoSupplementReference(path: string) {
    if (path.trim() === "") {
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
      setNumerationEditorPath(response.path);
      setRenewMenu("hypothesis");
      setRenewPanel("numeration");
    });
  }

  function applyInitializedState(nextState: DerivationState) {
    setState(nextState);
    setStep2UndoStack([]);
    setSnapshots({ T0: cloneState(nextState), T1: null, T2: null });
    setCandidates([]);
    setIsStep2CandidatesLoading(false);
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
  }

  async function requestGenerateNumeration(
    useManualTokens = tokenInputMode === "manual"
  ): Promise<GeneratedNumeration> {
    const tokensForRequest = useManualTokens ? resolveManualTokensForSubmit() : undefined;
    return apiPost<GeneratedNumeration>("/v1/derivation/numeration/generate", {
      grammar_id: grammarId,
      sentence,
      tokens: tokensForRequest,
      split_mode: splitMode
    });
  }

  async function handleGenerate(useManualTokens = tokenInputMode === "manual") {
    await withLoading(async () => {
      const response = await requestGenerateNumeration(useManualTokens);
      setGenerated(response);
      setNumerationText(response.numeration_text);
      setNumerationEditorPath("(未保存) Numeration自動生成");
      syncTokenEdits(response);
      setStep1AutoSupplementNotes(response.auto_supplements || []);
      setArrangeRows([]);
    });
  }

  async function handleCreateStep1Numeration() {
    if (step1EntryMode === "upload_num") {
      if (step1UploadFormatError) {
        setError(`num形式エラー: ${step1UploadFormatError}`);
        return;
      }
    }
    await withLoading(async () => {
      let formedNumerationText = "";
      if (step1EntryMode === "upload_num") {
        if (uploadNumerationText.trim() === "") {
          throw new Error("numファイルを読み込んでください。");
        }
        formedNumerationText = uploadNumerationText;
        setGenerated(null);
        setTokenSlotEdits([]);
        setStep1AutoSupplementNotes([]);
        setOpenStep1CandidateSlot(null);
      } else if (step1EntryMode === "example_sentence") {
        if (step1ExampleNumerationText.trim() === "") {
          throw new Error("例文から .num を選択してください。");
        }
        if (tokenSlotEdits.length > 0) {
          formedNumerationText = await composeNumerationFromTokenEdits(tokenSlotEdits);
        } else {
          formedNumerationText = step1ExampleNumerationText;
        }
        setGenerated(null);
        setStep1AutoSupplementNotes([]);
        setOpenStep1CandidateSlot(null);
      } else {
        if (tokenSlotEdits.length > 0) {
          // Step1で差し替えた候補を保持したまま Numeration を形成する。
          formedNumerationText = await composeNumerationFromTokenEdits(tokenSlotEdits);
        } else {
          const generatedNumeration = await requestGenerateNumeration(tokenInputMode === "manual");
          setGenerated(generatedNumeration);
          syncTokenEdits(generatedNumeration);
          setStep1AutoSupplementNotes(generatedNumeration.auto_supplements || []);
          formedNumerationText = generatedNumeration.numeration_text;
        }
      }

      setNumerationText(formedNumerationText);
      setNumerationEditorPath("(未保存) Step1 Numeration形成");
      setArrangeRows([]);

      const initialized = await apiPost<DerivationState>("/v1/derivation/init", {
        grammar_id: grammarId,
        numeration_text: formedNumerationText
      });
      applyInitializedState(initialized);
      setRenewMenu("hypothesis");
      setRenewPanel("target");
    });
  }

  async function handleInitFromSentence() {
    const tokensForRequest = tokenInputMode === "manual" ? resolveManualTokensForSubmit() : undefined;
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
      setNumerationEditorPath("(未保存) 文から初期化");
      syncTokenEdits(response.numeration);
      setStep1AutoSupplementNotes(response.numeration.auto_supplements || []);
      applyInitializedState(response.state);
      setRenewMenu("hypothesis");
      setRenewPanel("target");
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
      applyInitializedState(response);
      setRenewMenu("hypothesis");
      setRenewPanel("target");
    });
  }

  async function handleLoadNumerationFiles(source: "set" | "saved", targetGrammarId = grammarId) {
    await withLoading(async () => {
      const rows = await apiGet<NumerationFileEntry[]>(
        `/v1/derivation/numeration/files?grammar_id=${targetGrammarId}&source=${source}`
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
      setNumerationEditorPath(response.path);
      setArrangeRows([]);
    });
  }

  async function handleSaveNumeration() {
    if (numerationText.trim() === "") {
      setError("保存する .num テキストが空です。");
      return;
    }
    await withLoading(async () => {
      const response = await apiPost<{ path: string }>("/v1/derivation/numeration/save", {
        grammar_id: grammarId,
        numeration_text: numerationText
      });
      setNumerationEditorPath(response.path);
      await handleLoadNumerationFiles("saved");
    });
  }

  function handleApplyUploadNumeration() {
    if (uploadNumerationText.trim() === "") {
      setError("upload テキストが空です。");
      return;
    }
    setNumerationText(uploadNumerationText);
    setNumerationEditorPath("(未保存) upload テキスト");
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

  async function composeNumerationFromTokenEdits(
    nextTokenSlotEdits: TokenSlotEdit[],
    options?: { reinitializeState?: boolean }
  ): Promise<string> {
    const memoText = sentence.trim() === "" ? "manual" : sentence.trim();
    const response = await apiPost<{ numeration_text: string }>("/v1/derivation/numeration/compose", {
      memo: memoText,
      lexicon_ids: nextTokenSlotEdits.map((row) => row.selectedLexiconId),
      plus_values: nextTokenSlotEdits.map((row) => row.plusValue),
      idx_values: nextTokenSlotEdits.map((row) => row.idxValue)
    });
    setTokenSlotEdits(nextTokenSlotEdits);
    setNumerationText(response.numeration_text);
    setNumerationEditorPath("(未保存) 候補差し替え");
    if (step1EntryMode === "example_sentence") {
      setStep1ExampleNumerationText(response.numeration_text);
    }
    if (step1EntryMode === "build_lexicon") {
      setStep1BuildPreviewNumerationText(response.numeration_text);
    }
    if (generated) {
      setGenerated({
        ...generated,
        memo: sentence.trim() === "" ? generated.memo : sentence.trim(),
        lexicon_ids: nextTokenSlotEdits.map((row) => row.selectedLexiconId),
        token_resolutions: generated.token_resolutions.map((row, i) => ({
          ...row,
          lexicon_id: nextTokenSlotEdits[i]?.selectedLexiconId ?? row.lexicon_id
        })),
        numeration_text: response.numeration_text
      });
    }
    if (options?.reinitializeState) {
      const initialized = await apiPost<DerivationState>("/v1/derivation/init", {
        grammar_id: grammarId,
        numeration_text: response.numeration_text
      });
      applyInitializedState(initialized);
    }
    return response.numeration_text;
  }

  async function handleComposeNumerationFromTokenSelection() {
    if (tokenSlotEdits.length === 0) {
      setError("候補再選択の対象がありません。先に Generate .num または Init T0 を実行してください。");
      return;
    }
    await withLoading(async () => {
      await composeNumerationFromTokenEdits(tokenSlotEdits);
    });
  }

  async function handleApplyStep1Candidate(slot: number, candidateId: number) {
    const row = tokenSlotEditBySlot.get(slot);
    if (!row || row.selectedLexiconId === candidateId) {
      return;
    }
    const nextTokenSlotEdits = tokenSlotEdits.map((item) =>
      item.slot === slot ? { ...item, selectedLexiconId: candidateId } : item
    );
    await withLoading(async () => {
      await composeNumerationFromTokenEdits(nextTokenSlotEdits);
    });
  }

  async function handleApplyStep2Candidate(slot: number, candidateId: number) {
    const row = tokenSlotEditBySlot.get(slot);
    if (!row || row.selectedLexiconId === candidateId) {
      return;
    }
    const nextTokenSlotEdits = tokenSlotEdits.map((item) =>
      item.slot === slot ? { ...item, selectedLexiconId: candidateId } : item
    );
    await withLoading(async () => {
      await composeNumerationFromTokenEdits(nextTokenSlotEdits, { reinitializeState: true });
      setReachabilityMessage("語彙候補を差し替えて T0 を再初期化しました。");
      setRenewMenu("hypothesis");
      setRenewPanel("target");
    });
  }

  function handleOpenLexiconFromCandidate(lexiconId: number) {
    if (!Number.isInteger(lexiconId) || lexiconId <= 0) {
      return;
    }
    setLexiconFocusLexiconId(lexiconId);
    setLexiconFocusRequestSeq((prev) => prev + 1);
    setUiMode("renewed");
    setRenewMenu("lexicon");
    setRenewPanel("lexicon");
  }

  function updateTokenSlotEdit(slot: number, patch: Partial<TokenSlotEdit>) {
    setTokenSlotEdits((prev) => prev.map((row) => (row.slot === slot ? { ...row, ...patch } : row)));
  }

  function updateArrangeRow(slot: number, patch: Partial<ArrangeRow>) {
    setArrangeRows((prev) => prev.map((row) => (row.slot === slot ? { ...row, ...patch } : row)));
  }

  async function pollReachabilityJob(jobId: string): Promise<ReachabilityJobStatusResponse> {
    for (;;) {
      const status = await apiGet<ReachabilityJobStatusResponse>(`/v1/derivation/reachability/jobs/${jobId}`);
      setReachabilityProgress({
        percent: status.progress.percent,
        phase: status.progress.phase,
        message: status.progress.message
      });
      if (["reachable", "unreachable", "unknown", "failed"].includes(status.status)) {
        return status;
      }
      await new Promise((resolve) => setTimeout(resolve, 800));
    }
  }

  async function loadReachabilityEvidencePage(jobId: string, offset: number, limit: number) {
    const page = await apiGet<ReachabilityEvidencePageResponse>(
      `/v1/derivation/reachability/jobs/${jobId}/evidences?offset=${Math.max(0, offset)}&limit=${Math.max(1, limit)}`
    );
    setReachabilityRows(page.evidences);
    setOpenReachabilityFirstStepKey(null);
    setReachabilityOffset(page.counts.offset);
    setReachabilityLimit(page.counts.limit);
    setReachabilityResult((prev) => {
      if (!prev) {
        return null;
      }
      return {
        ...prev,
        counts: page.counts,
        evidences: page.evidences
      };
    });
  }

  function applyReachabilityTerminalStatus(terminal: ReachabilityJobStatusResponse) {
    const terminalStatus: ReachabilityResponse["status"] =
      terminal.status === "reachable" || terminal.status === "unreachable" || terminal.status === "unknown"
        ? terminal.status
        : "unknown";

    setReachabilityResult({
      status: terminalStatus,
      completed: Boolean(terminal.completed),
      reason: terminal.reason ?? terminalStatus,
      metrics: terminal.metrics ?? {
        expanded_nodes: 0,
        generated_nodes: 0,
        packed_nodes: 0,
        max_frontier: 0,
        elapsed_ms: 0,
        max_depth_reached: 0,
        actions_attempted: 0
      },
      counts: terminal.counts ?? {
        count_unit: "derivation_tree",
        count_basis: "structural_signature_v1",
        tree_signature_basis: "canonical_tree_v1",
        count_status: "unknown",
        goal_count_exact: null,
        total_exact: null,
        total_upper_bound_a_pair_only: "1",
        total_upper_bound_b_pair_rulemax: "1",
        rule_max_per_pair_bound: 1,
        rule_max_per_pair_observed: 1,
        shown_count: 0,
        offset: 0,
        limit: reachabilityLimit,
        shown_ratio_exact_percent: null,
        coverage_upper_bound_a_percent: 0,
        coverage_upper_bound_b_percent: 0,
        has_next: false
      },
      evidences: []
    });
    return terminalStatus;
  }

  async function handleHeadAssist() {
    if (!state) {
      setError("T0 以降の state がありません。先に 初期化 を実行してください。");
      return;
    }
    await withLoading(async () => {
      setReachabilityResult(null);
      setReachabilityRows([]);
      setReachabilityProgress({ percent: 0, phase: "queued", message: "ジョブ開始待ち" });
      const start = await apiPost<ReachabilityJobStartResponse>("/v1/derivation/reachability/jobs", {
        state,
        max_evidences: 50,
        offset: 0,
        limit: reachabilityLimit,
        budget_seconds: 30.0,
        max_nodes: 2_000_000,
        max_depth: 28,
        return_process_text: true
      });
      setReachabilityJobId(start.job_id);
      setReachabilityMessage("到達判定ジョブを開始しました。");

      const terminal = await pollReachabilityJob(start.job_id);
      if (terminal.status === "failed") {
        setReachabilityMessage(`到達判定に失敗しました: ${terminal.error ?? "unknown error"}`);
        return;
      }
      const terminalStatus = applyReachabilityTerminalStatus(terminal);
      await loadReachabilityEvidencePage(start.job_id, 0, reachabilityLimit);
      setReachabilityMessage(`到達判定: ${terminalStatus}`);
    });
  }

  async function handleContinueReachability() {
    if (!reachabilityJobId) {
      setError("続行対象の reachability job がありません。先に候補を提案してください。");
      return;
    }
    if (!reachabilityResult || reachabilityResult.completed) {
      setError("現在の判定結果は続行対象ではありません。");
      return;
    }

    await withLoading(async () => {
      setReachabilityProgress({ percent: 0, phase: "queued", message: "追加探索ジョブ開始待ち" });
      const restarted = await apiPost<ReachabilityJobStartResponse>(
        `/v1/derivation/reachability/jobs/${reachabilityJobId}/continue`,
        {
          additional_budget_seconds: 30.0,
          additional_max_nodes: 2_000_000,
          additional_max_depth: 8,
          additional_max_evidences: 10
        }
      );
      setReachabilityJobId(restarted.job_id);
      setReachabilityMessage("追加探索を開始しました。");
      const terminal = await pollReachabilityJob(restarted.job_id);
      if (terminal.status === "failed") {
        setReachabilityMessage(`追加探索に失敗しました: ${terminal.error ?? "unknown error"}`);
        return;
      }
      const terminalStatus = applyReachabilityTerminalStatus(terminal);
      await loadReachabilityEvidencePage(restarted.job_id, 0, reachabilityLimit);
      setReachabilityMessage(`到達判定: ${terminalStatus}`);
    });
  }

  async function executeStep2Rule(
    candidate: RuleCandidate,
    options?: { fromAssist?: boolean; rank?: number; left?: number; right?: number }
  ) {
    if (!state) {
      return;
    }
    const currentState = cloneState(state);
    await withLoading(async () => {
      const payload: Record<string, unknown> = {
        state,
        rule_name: candidate.rule_name
      };
      if (candidate.rule_kind === "single") {
        payload.check = candidate.check;
      } else {
        payload.left = options?.left ?? candidate.left;
        payload.right = options?.right ?? candidate.right;
      }
      const nextState = await apiPost<DerivationState>("/v1/derivation/execute", payload);
      if (currentState) {
        setStep2UndoStack((prev) => [...prev, currentState]);
      }
      setState(nextState);
      setCandidates([]);
      if (options?.fromAssist) {
        setReachabilityMessage(`証拠 ${options.rank ?? "-"} の先頭手を実行しました。`);
      }
      setSnapshots((prev) => {
        if (!prev.T1) {
          return { ...prev, T1: cloneState(nextState) };
        }
        return { ...prev, T2: cloneState(nextState) };
      });
    });
  }

  async function handleExecuteCandidate(candidate: RuleCandidate) {
    await executeStep2Rule(candidate);
  }

  function buildRuleCandidateFromReachabilityStep(step: ReachabilityEvidence["rule_sequence"][number]): RuleCandidate {
    return {
      rule_number: step.rule_number,
      rule_name: step.rule_name,
      rule_kind: step.rule_kind,
      left: step.left ?? undefined,
      right: step.right ?? undefined,
      check: step.check ?? undefined,
    };
  }

  async function handleExecuteHeadAssist(row: ReachabilityEvidence) {
    const first = row.rule_sequence[0];
    if (!first) {
      setReachabilityMessage("この証拠には実行可能な規則列がありません。");
      return;
    }
    setSelectedLeft(first.left ?? null);
    setSelectedRight(first.right ?? null);
    await executeStep2Rule(
      buildRuleCandidateFromReachabilityStep(first),
      { fromAssist: true, rank: row.rank, left: first.left ?? undefined, right: first.right ?? undefined }
    );
  }

  async function handleExecuteHeadAssistAllSteps(
    row: ReachabilityEvidence,
    options?: { rankOverride?: number; stepsOverride?: ReachabilityEvidence["rule_sequence"] }
  ) {
    if (!state) {
      return;
    }
    const steps = options?.stepsOverride ?? row.rule_sequence;
    if (steps.length === 0) {
      setReachabilityMessage("この証拠には実行可能な規則列がありません。");
      return;
    }
    const initialState = cloneState(state);
    await withLoading(async () => {
      let workingState = cloneState(state);
      if (!workingState) {
        throw new Error("state が初期化されていません。");
      }
      for (const step of steps) {
        const candidate = buildRuleCandidateFromReachabilityStep(step);
        const payload: Record<string, unknown> = {
          state: workingState,
          rule_name: candidate.rule_name
        };
        if (candidate.rule_kind === "single") {
          payload.check = candidate.check;
        } else {
          payload.left = candidate.left;
          payload.right = candidate.right;
        }
        workingState = await apiPost<DerivationState>("/v1/derivation/execute", payload);
      }

      if (initialState) {
        setStep2UndoStack((prev) => [...prev, initialState]);
      }
      setState(workingState);
      setCandidates([]);
      const first = steps[0];
      setSelectedLeft(first.left ?? null);
      setSelectedRight(first.right ?? null);
      setReachabilityMessage(
        `証拠 ${options?.rankOverride ?? row.rank} の全手順（${steps.length}手）を実行しました。`
      );
      setSnapshots((prev) => {
        if (!prev.T1) {
          return { ...prev, T1: cloneState(workingState) };
        }
        return { ...prev, T2: cloneState(workingState) };
      });
      setOpenReachabilityFirstStepKey(null);
    });
  }

  function handleUndoStep2Execute() {
    if (step2UndoStack.length === 0) {
      setReachabilityMessage("取り消せる実行がありません。");
      return;
    }
    const previous = step2UndoStack[step2UndoStack.length - 1];
    setStep2UndoStack((prev) => prev.slice(0, -1));
    setState(cloneState(previous));
    setCandidates([]);
    setIsStep2CandidatesLoading(false);
    setReachabilityMessage("直前の実行を取り消しました。");
  }

  async function handleReachabilityLoadMore() {
    if (!reachabilityJobId || !reachabilityResult) {
      return;
    }
    const nextOffset = reachabilityOffset + reachabilityLimit;
    if (!reachabilityResult.counts.has_next) {
      return;
    }
    await withLoading(async () => {
      await loadReachabilityEvidencePage(reachabilityJobId, nextOffset, reachabilityLimit);
      setReachabilityMessage("次の証拠を読み込みました。");
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

  async function handleOpenFeatureDoc(fileName: string) {
    if (fileName.trim() === "") {
      return;
    }
    await withLoading(async () => {
      const doc = await apiGet<HtmlDocResponse>(`/v1/reference/features/${fileName}`);
      setFeatureDocHtml(doc.html_text);
    });
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

  async function jumpToReferenceDocs() {
    setUiMode("renewed");
    setRenewMenu("reference");
    setRenewPanel("referenceDocs");
    await handleLoadReferenceDocs();
    window.requestAnimationFrame(() => {
      referenceSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  useEffect(() => {
    void handleLoadAllGrammars();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (renewPanel !== "referenceDocs") {
      return;
    }
    if (referenceDocsLoadedGrammarId === grammarId && featureDocs.length > 0 && ruleDocs.length > 0) {
      return;
    }
    void handleLoadReferenceDocs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [renewPanel, grammarId]);

  useEffect(() => {
    if (renewPanel !== "grammarInspect" || uiMode !== "renewed") {
      return;
    }
    if (inspectMergeRulesLoadedGrammarId === setupGrammarId && inspectMergeRules.length > 0) {
      return;
    }
    void handleOpenGrammarInspect(setupGrammarId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [renewPanel, setupGrammarId, uiMode, inspectMergeRulesLoadedGrammarId, inspectMergeRules.length]);

  useEffect(() => {
    if (grammarOptions.length === 0) {
      return;
    }
    const optionIds = new Set(grammarOptions.map((option) => option.grammar_id));
    if (!optionIds.has(grammarId)) {
      setGrammarId(grammarOptions[0].grammar_id);
    }
    if (!optionIds.has(setupGrammarId)) {
      setSetupGrammarId(grammarOptions[0].grammar_id);
    }
  }, [grammarId, grammarOptions, setupGrammarId]);

  useEffect(() => {
    void refreshAutoTokenPreview();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [grammarId, sentence, splitMode, tokenInputMode, workflowStarted]);

  useEffect(() => {
    if (step1EntryMode !== "example_sentence") {
      return;
    }
    if (setNumerationFiles.length === 0) {
      void handleLoadNumerationFiles("set", grammarId);
      return;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step1EntryMode, grammarId, setNumerationFiles.length]);

  useEffect(() => {
    if (step1EntryMode !== "example_sentence") {
      return;
    }
    if (setNumerationFiles.length === 0) {
      setStep1ExampleNumerationPath("");
      setStep1ExampleNumerationText("");
      return;
    }
    if (!setNumerationFiles.some((entry) => entry.path === step1ExampleNumerationPath)) {
      setStep1ExampleNumerationPath(setNumerationFiles[0].path);
      return;
    }
    if (step1ExampleNumerationPath === "") {
      setStep1ExampleNumerationPath(setNumerationFiles[0].path);
      return;
    }
    void handleLoadStep1ExampleNumerationByPath(step1ExampleNumerationPath);
  }, [grammarId, setNumerationFiles, step1ExampleNumerationPath, step1EntryMode]);

  useEffect(() => {
    step2AutoCandidatesRequestKeyRef.current = "";
    setCandidates([]);
    setIsStep2CandidatesLoading(false);
  }, [state?.basenum, state?.history, state?.newnum]);

  useEffect(() => {
    if (!state) {
      if (selectedLeft !== null) {
        setSelectedLeft(null);
      }
      if (selectedRight !== null) {
        setSelectedRight(null);
      }
      return;
    }
    if (step2DisplayRows.length === 0) {
      if (selectedLeft !== null) {
        setSelectedLeft(null);
      }
      if (selectedRight !== null) {
        setSelectedRight(null);
      }
      return;
    }
    const availableSlots = step2DisplayRows.map((row) => row.slot);
    const availableSet = new Set(availableSlots);
    let nextLeft = selectedLeft;
    if (nextLeft === null || !availableSet.has(nextLeft)) {
      nextLeft = availableSlots[0] ?? null;
    }
    let nextRight = selectedRight;
    const rightInvalid =
      nextRight === null || !availableSet.has(nextRight) || (nextLeft !== null && nextRight === nextLeft);
    if (rightInvalid) {
      nextRight = availableSlots.find((slot) => slot !== nextLeft) ?? null;
    }
    if (nextLeft !== selectedLeft) {
      setSelectedLeft(nextLeft);
    }
    if (nextRight !== selectedRight) {
      setSelectedRight(nextRight);
    }
  }, [selectedLeft, selectedRight, state, step2DisplayRows]);

  useEffect(() => {
    if (!state || selectedLeft === null || selectedRight === null) {
      setIsStep2CandidatesLoading(false);
      setCandidates([]);
      return;
    }
    if (selectedLeft === selectedRight) {
      setCandidates([]);
      setIsStep2CandidatesLoading(false);
      setReachabilityMessage("left と right は別の行を選択してください。");
      return;
    }
    if (
      selectedLeft < 1 ||
      selectedRight < 1 ||
      selectedLeft > state.basenum ||
      selectedRight > state.basenum
    ) {
      setCandidates([]);
      setIsStep2CandidatesLoading(false);
      return;
    }

    const requestKey = [
      state.newnum,
      state.basenum,
      state.history,
      selectedLeft,
      selectedRight
    ].join("|");
    if (step2AutoCandidatesRequestKeyRef.current === requestKey) {
      return;
    }
    step2AutoCandidatesRequestKeyRef.current = requestKey;

    const requestSeq = step2AutoCandidatesRequestSeqRef.current + 1;
    step2AutoCandidatesRequestSeqRef.current = requestSeq;

    setIsStep2CandidatesLoading(true);
    void (async () => {
      try {
        const response = await apiPost<RuleCandidate[]>("/v1/derivation/candidates", {
          state,
          left: selectedLeft,
          right: selectedRight
        });
        if (requestSeq !== step2AutoCandidatesRequestSeqRef.current) {
          return;
        }
        setCandidates(response);
        if (response.length === 0) {
          setReachabilityMessage("この左右では適用可能な規則がありません。");
        } else {
          setReachabilityMessage("");
        }
      } catch {
        if (requestSeq !== step2AutoCandidatesRequestSeqRef.current) {
          return;
        }
        setCandidates([]);
        setReachabilityMessage("適用可能ルールの読込に失敗しました。");
      } finally {
        if (requestSeq === step2AutoCandidatesRequestSeqRef.current) {
          setIsStep2CandidatesLoading(false);
        }
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedLeft, selectedRight, state]);

  const activeRenewMenu =
    RENEW_MENUS.find((entry) => entry.key === renewMenu) || RENEW_MENUS[0];
  const legacyPerlIframeSrc = `${LEGACY_PERL_BASE_URL}/v1/legacy/perl/index-IMI.cgi?reload=${legacyFrameReloadTick}`;

  const numerationLexiconPanel = (
    <div className="numeration-lexicon-panel legacy-numeration-panel">
      <h3>numerationの語彙情報参照</h3>
      <p className="hint">
        Perl実行表示に合わせて、slot・統語素性・意味素性・音韻を確認できます。
      </p>
      {isNumerationLexiconLoading && <p className="hint">語彙情報を参照中…</p>}
      {numerationLexiconError && <p className="step1-upload-error">{numerationLexiconError}</p>}
      {numerationLexiconRows.length === 0 ? (
        <p className="hint">対象の語彙IDがありません。</p>
      ) : (
        <div className="numeration-legacy-list" data-testid="numeration-lexicon-table">
          {numerationLexiconRows.map((row) => {
            const xLabel = `x${row.slot}-1`;
            const syValues = row.syncFeatures.filter((feature) => feature.trim() !== "");
            const semanticValues = row.semantics.filter((semantic) => semantic.trim() !== "");
            const idslotRaw = row.idslot.trim();
            const slotEdit = tokenSlotEditBySlot.get(row.slot);
            const includeSlotCandidates =
              (step1EntryMode === "build_lexicon" || step1EntryMode === "example_sentence") &&
              renewPanel !== "numeration";
            const slotCandidateIds = Array.from(
              new Set(
                (includeSlotCandidates ? slotEdit?.candidateLexiconIds || [] : []).filter(
                  (candidateId) => Number.isInteger(candidateId) && candidateId > 0
                )
              )
            );
            const candidateIds = Array.from(
              new Set([...(row.lexiconId ? [row.lexiconId] : []), ...slotCandidateIds])
            );
            const showStep1CandidateControls =
              renewPanel !== "numeration" && candidateIds.length > 0;
            const canApplyStep1Candidates = includeSlotCandidates && Boolean(slotEdit);
            const selectedCandidateId = includeSlotCandidates
              ? slotEdit?.selectedLexiconId ?? row.lexiconId ?? null
              : row.lexiconId ?? null;
            const selectedCompatibility =
              includeSlotCandidates && selectedCandidateId
                ? slotEdit?.candidateCompatibilityById[selectedCandidateId]
                : undefined;
            const selectedCompatibilityReasons =
              selectedCompatibility && !selectedCompatibility.compatible
                ? formatCompatibilityReasonsForDisplay(selectedCompatibility)
                : [];
            const inlinePartnerWarnings =
              includeSlotCandidates && selectedCandidateId
                ? step1PartnerWarnings.filter(
                  (warning) =>
                    warning.slot === row.slot && warning.selectedLexiconId === selectedCandidateId
                )
                : [];
            const unresolvedMessage = row.lexiconId === null
              ? `語彙ID ${row.rawLexiconId} は数値ではありません`
              : `語彙ID ${row.rawLexiconId} は辞書にありません`;

            return (
              <div className="numeration-legacy-row" key={`${row.slot}-${row.rawLexiconId}`}>
                <div className="numeration-legacy-slot">{row.slot}</div>
                <div className="numeration-legacy-main">
                  {row.found === false || row.lexiconId === null ? (
                    <div className="numeration-legacy-topline">
                      <span className="perl-f0">{xLabel}</span>
                      <span className="perl-f1">-</span>
                      <span className="numeration-legacy-unresolved">{unresolvedMessage}</span>
                    </div>
                  ) : (
                    <div className="numeration-legacy-topline">
                      <span className="perl-f0">{xLabel}</span>
                      <span className="perl-f1">{row.category || "-"}</span>
                      {syValues.map((feature, featureIdx) => (
                        <span className="perl-f3" key={`${row.slot}-sy-${featureIdx}`}>
                          {renderEncodedFeatureLikePerl(feature, `${row.slot}-sy-${featureIdx}`)}
                        </span>
                      ))}
                      {idslotRaw === "id" && <span className="perl-f4">{xLabel}</span>}
                      {idslotRaw !== "" && idslotRaw !== "id" && idslotRaw !== "zero" && idslotRaw !== "rel" && (
                        <span className="perl-f4">
                          {isEncodedFeature(idslotRaw)
                            ? renderEncodedFeatureLikePerl(idslotRaw, `${row.slot}-sl`)
                            : idslotRaw}
                        </span>
                      )}
                      {semanticValues.map((semantic, semIdx) => {
                        const pos = semantic.indexOf(":");
                        const attribute = pos >= 0 ? semantic.slice(0, pos).trim() : "";
                        const rawValue = pos >= 0 ? semantic.slice(pos + 1).trim() : semantic.trim();
                        return (
                          <span className="perl-f5" key={`${row.slot}-se-${semIdx}`}>
                            {attribute !== "" ? `${attribute}: ` : ""}
                            {isEncodedFeature(rawValue)
                              ? renderEncodedFeatureLikePerl(rawValue, `${row.slot}-se-${semIdx}`)
                              : rawValue}
                          </span>
                        );
                      })}
                      {row.phono !== "" && <span className="perl-f6">{row.phono}</span>}
                    </div>
                  )}
                  {showStep1CandidateControls && (
                    <div className="numeration-candidate-controls">
                      <button
                        type="button"
                        className="numeration-candidate-toggle"
                        data-testid={`step1-candidate-toggle-${row.slot}`}
                        aria-expanded={openStep1CandidateSlot === row.slot}
                        onClick={() =>
                          setOpenStep1CandidateSlot((prev) => (prev === row.slot ? null : row.slot))
                        }
                      >
                        候補({candidateIds.length})
                      </button>
                      <span className="numeration-candidate-status">
                        選択中: {selectedCandidateId ?? "-"}
                      </span>
                    </div>
                  )}
                  {selectedCompatibilityReasons.length > 0 && (
                    <p
                      className="numeration-candidate-inline-warning"
                      data-testid={`step1-inline-compat-warning-${row.slot}`}
                    >
                      警告: {selectedCompatibilityReasons.join(" ")}
                    </p>
                  )}
                  {inlinePartnerWarnings.map((warning, index) => (
                    <p
                      className={
                        warning.level === "impossible"
                          ? "numeration-candidate-inline-warning"
                          : "numeration-candidate-inline-note"
                      }
                      data-testid={`step1-inline-partner-summary-${row.slot}-${index}`}
                      key={`step1-inline-partner-${row.slot}-${warning.requirement.featureCode}-${warning.requirement.label}-${index}`}
                    >
                      {warning.level === "impossible"
                        ? `警告: ${warning.requirement.featureCode}(${warning.requirement.label}) を満たす語が見つかりません。`
                        : `注意: 現在の選択では ${warning.requirement.featureCode}(${warning.requirement.label}) を満たす語がありません。`}
                    </p>
                  ))}
                  {showStep1CandidateControls && openStep1CandidateSlot === row.slot && (
                    <div className="numeration-candidate-list" data-testid={`step1-candidate-panel-${row.slot}`}>
                      {candidateIds.map((candidateId) => {
                        const candidateItem = numerationLookupMap.get(candidateId);
                        const candidateCompatibility =
                          slotEdit?.candidateCompatibilityById[candidateId];
                        const isCompatible = candidateCompatibility
                          ? candidateCompatibility.compatible
                          : true;
                        const incompatibilityReasons =
                          candidateCompatibility && !candidateCompatibility.compatible
                            ? formatCompatibilityReasonsForDisplay(candidateCompatibility)
                            : [];
                        const candidateSyncFeatures = candidateItem
                          ? candidateItem.sync_features.filter((feature) => feature.trim() !== "").slice(0, 3)
                          : [];
                        const candidateSemantics = candidateItem
                          ? candidateItem.semantics.filter((semantic) => semantic.trim() !== "").slice(0, 2)
                          : [];
                        const isSelected = selectedCandidateId === candidateId;
                        return (
                          <div
                            className={`numeration-candidate-item${isSelected ? " selected" : ""}`}
                            key={`${row.slot}-candidate-${candidateId}`}
                          >
                            <div className="numeration-candidate-summary">
                              <span className="numeration-candidate-id">ID {candidateId}</span>
                              {!isCompatible && (
                                <span className="numeration-candidate-incompatible">
                                  文法非互換
                                </span>
                              )}
                              {candidateItem && (
                                <>
                                  <span className="numeration-candidate-cat">{candidateItem.category || "-"}</span>
                                  <span className="numeration-candidate-entry">{candidateItem.entry}</span>
                                  {candidateItem.phono !== "" && (
                                    <span className="numeration-candidate-phono">{candidateItem.phono}</span>
                                  )}
                                  {candidateSyncFeatures.map((feature, featureIdx) => (
                                    <span
                                      className="numeration-candidate-sy"
                                      key={`${row.slot}-candidate-${candidateId}-sy-${featureIdx}`}
                                    >
                                      {isEncodedFeature(feature)
                                        ? renderEncodedFeatureLikePerl(
                                          feature,
                                          `${row.slot}-candidate-${candidateId}-sy-${featureIdx}`
                                        )
                                        : feature}
                                    </span>
                                  ))}
                                  {candidateSemantics.map((semantic, semIdx) => (
                                    <span
                                      className="numeration-candidate-sem"
                                      key={`${row.slot}-candidate-${candidateId}-sem-${semIdx}`}
                                    >
                                      {semantic}
                                    </span>
                                  ))}
                                </>
                              )}
                              {!candidateItem && (
                                <span className="numeration-legacy-unresolved">
                                  候補詳細を取得できませんでした。
                                </span>
                              )}
                            </div>
                            {!isCompatible && (
                              <p className="numeration-candidate-incompatible-reason">
                                {incompatibilityReasons.join(" ")}
                              </p>
                            )}
                            <div className="numeration-candidate-actions">
                              <button
                                type="button"
                                className="numeration-candidate-open-lexicon"
                                onClick={() => {
                                  handleOpenLexiconFromCandidate(candidateId);
                                }}
                              >
                                語彙項目を編集
                              </button>
                              <button
                                type="button"
                                className="numeration-candidate-apply"
                                disabled={loading || isSelected || !canApplyStep1Candidates}
                                onClick={() => {
                                  void handleApplyStep1Candidate(row.slot, candidateId);
                                }}
                              >
                                {isSelected ? "選択中" : canApplyStep1Candidates ? "この候補に差し替え" : "差し替え不可"}
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
      <label className="numeration-legacy-source-label">
        numeration (.num)
        <textarea
          aria-label="Numeration Lexicon Source"
          className="numeration-legacy-source"
          rows={3}
          value={step1NumerationLexiconSourceTextForDisplay}
          readOnly
        />
      </label>
    </div>
  );

  return (
    <div className={uiMode === "legacy" ? "page legacy-mode" : "page renewed-mode"}>
      <header className="hero">
        <h1>SYNCSEMPHONE NEXT</h1>
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
            {activeRenewMenu.key !== "lexicon" && (
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
            )}

          <main
            className={uiMode === "renewed" ? "grid renewed-grid" : "grid legacy-grid"}
            data-active-panel={renewPanel}
          >
        <section className="card" data-panel="setup">
          <h2>0. Lexicon / Grammar の選択</h2>
          <p className="hint step0-description">{STEP0_START_DESCRIPTION}</p>
          <div className="step0-field">
            <div className="grammar-label">Lexicon / Grammar（共通選択）</div>
            <div className="row grammar-controls step0-controls">
              <div className="step0-select-block">
                <div className="step0-select-row">
                  <select
                    aria-label="Step0 Grammar"
                    value={setupGrammarId}
                    onChange={(event) => setSetupGrammarId(event.target.value)}
                  >
                    {shownStep0GrammarOptions.map((option) => (
                      <option key={`step0-grammar-${option.grammar_id}`} value={option.grammar_id}>
                        {formatGrammarOption(option)}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="step0-more-row">
                <div className="step0-inspect-actions step0-inspect-actions-inline">
                  <button
                    type="button"
                    className="step0-inspect-action-btn"
                    onClick={() => {
                      void handleOpenLexiconInspect(setupGrammarId, 1, null);
                    }}
                    disabled={loading}
                  >
                    Lexicon内容確認
                  </button>
                  <button
                    type="button"
                    className="step0-inspect-action-btn"
                    onClick={() => {
                      void handleOpenGrammarInspect(setupGrammarId);
                    }}
                    disabled={loading}
                    >
                    Grammar内容確認
                  </button>
                </div>
                <span
                  className="step0-more-toggle"
                  role="button"
                  tabIndex={loading ? -1 : 0}
                  aria-label="More toggle"
                  aria-pressed={showMoreGrammarOptions}
                  aria-disabled={loading}
                  onClick={() => {
                    if (!loading) {
                      setShowMoreGrammarOptions((prev) => !prev);
                    }
                  }}
                  onKeyDown={(event) => {
                    if (loading) {
                      return;
                    }
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      setShowMoreGrammarOptions((prev) => !prev);
                    }
                  }}
                >
                  {showMoreGrammarOptions ? "✓ More" : "More"}
                </span>
              </div>
            </div>
          </div>

          <div className="row step0-start-row">
            <button
              type="button"
              className="step0-start-btn"
              onClick={handleStartHypothesisLoop}
              disabled={loading}
            >
              この設定で開始
            </button>
          </div>
        </section>

        <section className="card" data-panel="sentence">
          <h2>【Step.1】Numerationの形成</h2>
          {!workflowStarted && (
            <p className="hint">
              先に Step0 で設定を確定してください。未確定でも操作できますが、観察条件の固定には Step0 開始操作を推奨します。
            </p>
          )}
          <p className="hint">
            適用中のGrammar:
            {" "}
            {activeGrammarOption ? formatGrammarOption(activeGrammarOption) : grammarId}
          </p>
          <p className="hint">
            このステップのゴールは「観察に使う .num（Numeration）を1本確定すること」です。
          </p>
          <p className="hint">
            入口を分離しています。<strong>例文選択 / Lexiconから組み立てる</strong>は「Numerationを新規に形成」します。
            <strong>numファイルを選ぶ</strong>は「既存 .num を読み込み」です。
          </p>
          <div className="row step1-entry-modes" role="group" aria-label="Step1 Entry Mode">
            <button
              type="button"
              className={step1EntryMode === "example_sentence" ? "token-mode-btn active" : "token-mode-btn"}
              onClick={() => handleSelectStep1EntryMode("example_sentence")}
            >
              例文から選ぶ
            </button>
            <button
              type="button"
              className={step1EntryMode === "upload_num" ? "token-mode-btn active" : "token-mode-btn"}
              onClick={() => handleSelectStep1EntryMode("upload_num")}
            >
              numファイルを選ぶ
            </button>
            <button
              type="button"
              className={step1EntryMode === "build_lexicon" ? "token-mode-btn active" : "token-mode-btn"}
              onClick={() => handleSelectStep1EntryMode("build_lexicon")}
            >
              Lexiconから組み立てる
            </button>
          </div>

          {step1EntryMode === "example_sentence" && (
            <div className="step1-stack">
              <p className="hint">このモードは set-numeration から example .num を選びます。</p>
              <label>
                例文選択
                <select
                  aria-label="Step1 Example Sentence"
                  value={step1ExampleNumerationPath}
                  onChange={(event) => handleChangeStep1ExampleNumerationPath(event.target.value)}
                  disabled={setNumerationFiles.length === 0}
                >
                  {setNumerationFiles.length === 0 ? (
                    <option value="">
                      （候補を読み込み中）
                    </option>
                  ) : (
                    setNumerationFiles.map((entry) => (
                      <option key={entry.path} value={entry.path}>
                        [{entry.memo}]
                      </option>
                    ))
                  )}
                </select>
              </label>
              {setNumerationFiles.length === 0 && (
                <p className="hint">例文候補が空です。Step0で「この設定で開始」を押すか、API接続を確認してください。</p>
              )}
              {step1NumerationLexiconSourceText === "" ? (
                <p className="hint">例文対応 .num を読み込んで語彙情報を参照中…</p>
              ) : (
                numerationLexiconPanel
              )}
            </div>
          )}

          {step1EntryMode === "upload_num" && (
            <div className="step1-stack">
              <p className="hint">このモードは既存 .num の読込専用です。</p>
              <div className="row row-start">
                <input
                  data-testid="step1-upload-file-input"
                  aria-label="Step1 Upload File"
                  type="file"
                  accept=".num,.txt,text/plain"
                  className="hidden-upload-input"
                  ref={step1UploadFileInputRef}
                  id="step1-upload-file-input"
                  onChange={(event) => {
                    const file = event.target.files?.[0] ?? null;
                    void handleStep1UploadFile(file);
                  }}
                />
                <button
                  type="button"
                  className="token-mode-btn upload-file-trigger"
                  onClick={handleOpenStep1UploadPicker}
                >
                  numファイルをアップロード
                </button>
              </div>
              {step1UploadFileName && <p className="hint">読み込み中ファイル: {step1UploadFileName}</p>}
              <label>
                .num テキスト入力（アップロード）
                <textarea
                  aria-label="Step1 Upload Numeration"
                  rows={5}
                  value={uploadNumerationText}
                  onChange={(event) => setUploadNumerationText(event.target.value)}
                />
              </label>
              {step1UploadFormatError && (
                <p className="step1-upload-error" data-testid="step1-upload-error">
                  {step1UploadFormatError}
                </p>
              )}
              {numerationLexiconPanel}
              <p className="hint">`Numerationを形成` を押すと、入力した `.num` を作業中Numerationへ反映します。</p>
            </div>
          )}

          {step1EntryMode === "build_lexicon" && (
            <div className="step1-stack">
              <p className="hint">このモードは観察文から語彙候補を解決し、Numerationを形成します。</p>
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
                        onClick={() => {
                          setTokenInputMode("manual");
                          setIsEditingManualTokens(false);
                          const rawSentence = sentence.trim();
                          setManualTokens(rawSentence === "" ? [] : [rawSentence]);
                          setManualTokenInput(rawSentence);
                        }}
                      >
                        手動
                      </button>
                      <button
                        type="button"
                        className={tokenInputMode === "auto" ? "token-mode-btn active" : "token-mode-btn"}
                        onClick={() => {
                          setIsEditingManualTokens(false);
                          setTokenInputMode("auto");
                        }}
                      >
                        自動（Sudachi）
                      </button>
                    </div>
                  </div>
                </div>

                {tokenInputMode === "manual" ? (
                  <p className="hint">
                    手動では観察文（原文）を空白/カンマ区切りで分割して利用します。
                  </p>
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

                <div
                  className={`token-chip-row ${tokenInputMode === "manual" ? "manual-editable" : ""}`}
                  data-testid="token-chip-row"
                  onClick={(event) => {
                    if (isEditingManualTokens) {
                      event.stopPropagation();
                      return;
                    }
                    startManualTokenEdit();
                  }}
                  onKeyDown={(event) => {
                    if (isEditingManualTokens) {
                      event.stopPropagation();
                      return;
                    }
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      startManualTokenEdit();
                    }
                  }}
                  role={tokenInputMode === "manual" ? "button" : undefined}
                  tabIndex={tokenInputMode === "manual" ? 0 : -1}
                >
                  {tokenInputMode === "manual" && isEditingManualTokens ? (
                    <textarea
                      aria-label="Manual Token Editor"
                      className="token-chip-editor"
                      rows={2}
                      value={manualTokenInput}
                      onChange={(event) => setManualTokenInput(event.target.value)}
                      onMouseDown={(event) => event.stopPropagation()}
                      onClick={(event) => event.stopPropagation()}
                      onKeyDown={(event) => {
                        event.stopPropagation();
                        if (event.key === "Enter") {
                          event.preventDefault();
                          commitManualTokenEdit();
                        }
                      }}
                      onBlur={commitManualTokenEdit}
                      autoFocus
                    />
                  ) : (
                    <>
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
                    </>
                  )}
                </div>
              </div>

              <p className="hint">
                分割結果にもとづく語彙候補を参照します（Lexiconから組み立てるモード）。
              </p>
              {isStep1BuildPreviewLoading && <p className="hint">分割結果から語彙候補を計算中…</p>}
              {step1BuildPreviewError && <p className="step1-upload-error">{step1BuildPreviewError}</p>}
              {step1AutoSupplementNotes.length > 0 && (
                <div className="step1-auto-supplement-notes" data-testid="step1-auto-supplement-notes">
                  <h4>自動補完の注釈</h4>
                  {step1AutoSupplementNotes.map((note, index) => (
                    <div
                      className="step1-auto-supplement-note"
                      key={`step1-auto-supplement-${note.lexicon_id}-${index}`}
                    >
                      <p>
                        {`ID ${note.lexicon_id}（${note.entry}）を ${note.count}件 追加: `}
                        {`${note.feature_code}(${note.label}) の要求 ${note.demand_count}件 / 供給 ${note.provider_count}件`}
                      </p>
                      <p className="hint">{note.reason}</p>
                      <div className="row row-start">
                        <button
                          type="button"
                          className="step1-auto-supplement-link"
                          disabled={!note.reference_numeration_path}
                          onClick={() => {
                            if (note.reference_numeration_path) {
                              void handleOpenAutoSupplementReference(note.reference_numeration_path);
                            }
                          }}
                        >
                          根拠 .num を Numeration編集で表示
                        </button>
                        {note.reference_numeration_memo && (
                          <span className="hint">根拠: {note.reference_numeration_memo}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {numerationLexiconPanel}
            </div>
          )}

          <div className="row step1-actions">
            <button
              type="button"
              className="step0-start-btn"
              onClick={() => {
                void handleCreateStep1Numeration();
              }}
              disabled={
                loading ||
                (step1EntryMode === "upload_num" &&
                  (uploadNumerationText.trim() === "" || step1UploadFormatError !== null)) ||
                (step1EntryMode === "example_sentence" && step1ExampleNumerationText.trim() === "") ||
                (step1EntryMode === "build_lexicon" && sentence.trim() === "")
              }
            >
            Numerationを形成
            </button>
          </div>
          <p className="hint step1-action-summary">
            {step1EntryMode === "upload_num"
              ? "numファイルを選んだモードでは、既存の `.num` をそのまま作業中Numerationへ読み込みます。"
              : step1EntryMode === "example_sentence"
                ? "例文選択モードでは set-numeration を読み込んで .num を採用します。"
                : "Lexiconから組み立てるモードでは、語彙候補解決結果をもとにNumerationを形成します。"}
          </p>
        </section>

        <section className="card" data-panel="numeration">
          <h2>Numeration編集</h2>
          <p className="hint">タブ区切り `.num` を直接編集し、下部で語彙情報参照を確認できます。</p>

          <input
            aria-label="Numeration Editor Upload File"
            type="file"
            accept=".num,.txt,text/plain"
            className="hidden-upload-input"
            ref={numerationEditorFileInputRef}
            onChange={(event) => {
              const file = event.target.files?.[0] ?? null;
              void handleNumerationEditorUploadFile(file);
            }}
          />
          <div className="row row-start">
            <button type="button" className="token-mode-btn upload-file-trigger" onClick={handleOpenNumerationEditorPicker}>
              numファイルをアップロード（編集）
            </button>
            <button type="button" onClick={() => void handleLoadNumerationFiles("set")} disabled={loading}>
              set-numeration 一覧更新
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
              type="button"
              onClick={() => void handleLoadNumerationPath(selectedSetPath)}
              disabled={loading || selectedSetPath === ""}
            >
              選択ファイルを読込
            </button>
            <button type="button" onClick={handleSaveNumeration} disabled={loading || numerationText.trim() === ""}>
              .num を保存
            </button>
          </div>
          <p className="hint">ファイルパス: {numerationEditorPath || "(未指定 / 未保存)"}</p>

          <div className="numeration-grid-wrap">
            <table className="numeration-grid" aria-label="numeration-grid-editor">
              <thead>
                <tr>
                  <th>#</th>
                  {Array.from({ length: numerationEditorGridColumnCount }, (_, index) => (
                    <th key={`num-col-${index}`}>{index}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {numerationEditorGrid.map((row, rowIndex) => (
                  <tr key={`num-row-${rowIndex}`}>
                    <th>{rowIndex + 1}</th>
                    {Array.from({ length: numerationEditorGridColumnCount }, (_, colIndex) => (
                      <td key={`num-cell-${rowIndex}-${colIndex}`}>
                        <input
                          aria-label={`numeration-cell-${rowIndex + 1}-${colIndex}`}
                          value={row[colIndex] ?? ""}
                          onChange={(event) => {
                            handleUpdateNumerationGridCell(rowIndex, colIndex, event.target.value);
                          }}
                        />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {numerationLexiconPanel}
        </section>

        <section className="card" data-panel="target">
          <h2>【Step.2】Grammarの適用</h2>
          <p className="hint">
            このステップの目的は、具体的な Numeration から解釈不可能性を消していくことです。
            手動で left/right と rule を選んで適用します（手動モードを維持）。
          </p>
          <p>status: {grammarStatus}</p>
          <p>
            basenum/newnum: {state ? `${state.basenum}/${state.newnum}` : "-"}
          </p>
          <p className="mono" data-testid="current-history">
            history: {state?.history || "(empty)"}
          </p>

          {state ? (
            <div className="numeration-lexicon-panel legacy-numeration-panel step2-target-panel">
              <h3>適用対象（left / right の選択）</h3>
              <p className="hint">
                `numerationの語彙情報参照` と同じ表示で確認しながら、左列・右列を選択してください。
                初期表示では先頭2行を自動選択し、候補規則を表示します。
              </p>
              {step2DisplayRows.length === 0 ? (
                <p className="hint">適用対象の行がありません。</p>
              ) : (
                <div className="numeration-legacy-list step2-selection-list" data-testid="step2-selection-list">
                  {step2DisplayRows.map((row) => {
                    const slotEdit = tokenSlotEditBySlot.get(row.slot);
                    const slotCandidateIds = Array.from(
                      new Set(
                        (slotEdit?.candidateLexiconIds || []).filter(
                          (candidateId) => Number.isInteger(candidateId) && candidateId > 0
                        )
                      )
                    );
                    const selectedCandidateId = slotEdit?.selectedLexiconId ?? null;
                    const selectedCompatibility = selectedCandidateId
                      ? slotEdit?.candidateCompatibilityById[selectedCandidateId]
                      : undefined;
                    const selectedCompatibilityReasons =
                      selectedCompatibility && !selectedCompatibility.compatible
                        ? formatCompatibilityReasonsForDisplay(selectedCompatibility)
                        : [];
                    const inlinePartnerWarnings = selectedCandidateId
                      ? step1PartnerWarnings.filter(
                        (warning) =>
                          warning.slot === row.slot && warning.selectedLexiconId === selectedCandidateId
                      )
                      : [];
                    const candidateIds = Array.from(
                      new Set([...(selectedCandidateId ? [selectedCandidateId] : []), ...slotCandidateIds])
                    );
                    const showStep2CandidateControls = candidateIds.length > 0;
                    const canApplyStep2Candidates =
                      state.history.trim() === "" &&
                      row.node.children.length === 0 &&
                      Boolean(slotEdit);
                    return (
                      <div className="numeration-legacy-row step2-selection-row" key={`step2-row-${row.slot}`}>
                        <label className="step2-side-select" aria-label={`left-select-${row.slot}`}>
                          <input
                            type="radio"
                            name="left-target"
                            aria-label={`left-${row.slot}`}
                            data-testid={`step2-left-radio-${row.slot}`}
                            checked={selectedLeft === row.slot}
                            onChange={() => {
                              setSelectedLeft(row.slot);
                              if (selectedRight === row.slot) {
                                setSelectedRight(null);
                              }
                            }}
                          />
                        </label>
                        <label className="step2-side-select" aria-label={`right-select-${row.slot}`}>
                          <input
                            type="radio"
                            name="right-target"
                            aria-label={`right-${row.slot}`}
                            data-testid={`step2-right-radio-${row.slot}`}
                            checked={selectedRight === row.slot}
                            onChange={() => {
                              setSelectedRight(row.slot);
                              if (selectedLeft === row.slot) {
                                setSelectedLeft(null);
                              }
                            }}
                          />
                        </label>
                        <div className="numeration-legacy-slot">{row.slot}</div>
                        <div className="numeration-legacy-main">
                          {renderStep2DisplayNode(row.node, row.slot, `${row.slot}`, 0)}
                          {showStep2CandidateControls && (
                            <div className="numeration-candidate-controls">
                              <button
                                type="button"
                                className="numeration-candidate-toggle"
                                data-testid={`step2-candidate-toggle-${row.slot}`}
                                aria-expanded={openStep2CandidateSlot === row.slot}
                                onClick={() =>
                                  setOpenStep2CandidateSlot((prev) => (prev === row.slot ? null : row.slot))
                                }
                              >
                                候補({candidateIds.length})
                              </button>
                              <span className="numeration-candidate-status">
                                選択中: {selectedCandidateId ?? "-"}
                              </span>
                            </div>
                          )}
                          {selectedCompatibilityReasons.length > 0 && (
                            <p
                              className="numeration-candidate-inline-warning"
                              data-testid={`step2-inline-compat-warning-${row.slot}`}
                            >
                              警告: {selectedCompatibilityReasons.join(" ")}
                            </p>
                          )}
                          {inlinePartnerWarnings.map((warning, index) => (
                            <p
                              className={
                                warning.level === "impossible"
                                  ? "numeration-candidate-inline-warning"
                                  : "numeration-candidate-inline-note"
                              }
                              data-testid={`step2-inline-partner-summary-${row.slot}-${index}`}
                              key={`step2-inline-partner-${row.slot}-${warning.requirement.featureCode}-${warning.requirement.label}-${index}`}
                            >
                              {warning.level === "impossible"
                                ? `警告: ${warning.requirement.featureCode}(${warning.requirement.label}) を満たす語が見つかりません。`
                                : `注意: 現在の選択では ${warning.requirement.featureCode}(${warning.requirement.label}) を満たす語がありません。`}
                            </p>
                          ))}
                          {showStep2CandidateControls && openStep2CandidateSlot === row.slot && (
                            <div className="numeration-candidate-list" data-testid={`step2-candidate-panel-${row.slot}`}>
                              {candidateIds.map((candidateId) => {
                                const candidateItem = numerationLookupMap.get(candidateId);
                                const candidateSyncFeatures = candidateItem
                                  ? candidateItem.sync_features.filter((feature) => feature.trim() !== "").slice(0, 3)
                                  : [];
                                const candidateSemantics = candidateItem
                                  ? candidateItem.semantics.filter((semantic) => semantic.trim() !== "").slice(0, 2)
                                  : [];
                                const isSelected = selectedCandidateId === candidateId;
                                return (
                                  <div
                                    className={`numeration-candidate-item${isSelected ? " selected" : ""}`}
                                    key={`step2-${row.slot}-candidate-${candidateId}`}
                                  >
                                    <div className="numeration-candidate-summary">
                                      <span className="numeration-candidate-id">ID {candidateId}</span>
                                      {candidateItem && (
                                        <>
                                          <span className="numeration-candidate-cat">{candidateItem.category || "-"}</span>
                                          <span className="numeration-candidate-entry">{candidateItem.entry}</span>
                                          {candidateItem.phono !== "" && (
                                            <span className="numeration-candidate-phono">{candidateItem.phono}</span>
                                          )}
                                          {candidateSyncFeatures.map((feature, featureIdx) => (
                                            <span
                                              className="numeration-candidate-sy"
                                              key={`step2-${row.slot}-candidate-${candidateId}-sy-${featureIdx}`}
                                            >
                                              {isEncodedFeature(feature)
                                                ? renderEncodedFeatureLikePerl(
                                                  feature,
                                                  `step2-${row.slot}-candidate-${candidateId}-sy-${featureIdx}`
                                                )
                                                : feature}
                                            </span>
                                          ))}
                                          {candidateSemantics.map((semantic, semIdx) => (
                                            <span
                                              className="numeration-candidate-sem"
                                              key={`step2-${row.slot}-candidate-${candidateId}-sem-${semIdx}`}
                                            >
                                              {semantic}
                                            </span>
                                          ))}
                                        </>
                                      )}
                                      {!candidateItem && (
                                        <span className="numeration-legacy-unresolved">
                                          候補詳細を取得できませんでした。
                                        </span>
                                      )}
                                    </div>
                                    <div className="numeration-candidate-actions">
                                      <button
                                        type="button"
                                        className="numeration-candidate-open-lexicon"
                                        onClick={() => {
                                          handleOpenLexiconFromCandidate(candidateId);
                                        }}
                                      >
                                        語彙項目を編集
                                      </button>
                                      <button
                                        type="button"
                                        className="numeration-candidate-apply"
                                        disabled={loading || isSelected || !canApplyStep2Candidates}
                                        onClick={() => {
                                          void handleApplyStep2Candidate(row.slot, candidateId);
                                        }}
                                      >
                                        {isSelected ? "選択中" : canApplyStep2Candidates ? "この候補に差し替え" : "差し替え不可"}
                                      </button>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
              <p className="hint">
                選択中 left/right: {selectedLeft ?? "-"} / {selectedRight ?? "-"}
              </p>
              <div className="step2-tree-tools" data-testid="step2-tree-tools">
                <button
                  type="button"
                  className="step0-start-btn step2-tree-btn"
                  onClick={() => {
                    void handleTree("tree_cat");
                  }}
                  disabled={loading || !state}
                  data-testid="step2-tree-cat-btn"
                >
                  樹形図（範疇蘇生）
                </button>
                <button
                  type="button"
                  className="step0-start-btn step2-tree-btn"
                  onClick={() => {
                    void handleTree("tree");
                  }}
                  disabled={loading || !state}
                  data-testid="step2-tree-index-btn"
                >
                  樹形図（指標番号）
                </button>
              </div>
              {treeGraph && (
                <div className="step2-tree-graph-panel" data-testid="step2-tree-graph-panel">
                  <p className="step2-tree-graph-title">
                    表示中: {activeTreeMode === "tree_cat" ? "樹形図（範疇蘇生）" : "樹形図（指標番号）"}
                  </p>
                  <div className="step2-tree-graph-scroll">
                    {renderTreeGraphSvg(treeGraph, "step2-tree-graph")}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="hint">state が未初期化です。Step1で Numeration を形成してください。</p>
          )}

          {step2RulesError && <p className="hint">{step2RulesError}</p>}
          <div className="step2-rule-table-scroll">
            <table data-testid="candidate-table" className="step2-rule-table">
              <thead>
                <tr>
                  <th>rule</th>
                  <th>kind</th>
                  <th>args</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {step2RuleRows.map((row) => (
                  <tr
                    key={`step2-rule-${row.rule.rule_number}`}
                    className={row.executable ? "step2-rule-row-executable" : "step2-rule-row-disabled"}
                  >
                    <td>
                      {row.rule.rule_number}:{row.rule.rule_name}
                    </td>
                    <td>{row.rule.rule_kind}</td>
                    <td>
                      {row.argsLabel}
                      {!row.executable && row.reason !== "" && (
                        <div
                          className="step2-rule-disabled-reason"
                          data-testid={`step2-rule-reason-${row.rule.rule_number}`}
                        >
                          {row.reason}
                        </div>
                      )}
                    </td>
                    <td>
                      <div className="step2-candidate-actions">
                        <button
                          className={!row.executable ? "step2-rule-execute-disabled" : ""}
                          onClick={() => {
                            if (row.executableCandidate) {
                              void handleExecuteCandidate(row.executableCandidate);
                            }
                          }}
                          disabled={loading || !row.executable}
                        >
                          実行
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {step2RuleRows.length === 0 && (
                  <tr>
                    <td>-</td>
                    <td>-</td>
                    <td>
                      {isStep2RulesLoading
                        ? "ルール一覧を読込中です…"
                        : isStep2CandidatesLoading
                          ? "left/right に対する適用可否を判定中です…"
                          : "ルールがありません。"}
                    </td>
                    <td>
                      <div className="step2-candidate-actions">
                        <button disabled>実行</button>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="row">
            <button onClick={handleUndoStep2Execute} disabled={loading || step2UndoStack.length === 0}>
              やり直し
            </button>
            <button onClick={handleHeadAssist} disabled={!state}>
              候補を提案
            </button>
            <button
              onClick={handleContinueReachability}
              disabled={!reachabilityJobId || !reachabilityResult || reachabilityResult.completed || loading}
            >
              探索を続ける
            </button>
          </div>
          {reachabilityProgress && (
            <p className="hint">
              進捗 {reachabilityProgress.percent.toFixed(1)}% / {reachabilityProgress.phase} / {reachabilityProgress.message}
            </p>
          )}
          {reachabilityMessage && <p className="hint">{reachabilityMessage}</p>}

          {reachabilityResult && (
            <div className="hint">
              判定: {reachabilityResult.status} / completed: {String(reachabilityResult.completed)} / reason: {reachabilityResult.reason}
              <br />
              count_status: {reachabilityResult.counts.count_status} / count_unit: {reachabilityResult.counts.count_unit}
              <br />
              上界A: {reachabilityResult.counts.total_upper_bound_a_pair_only}（{reachabilityResult.counts.coverage_upper_bound_a_percent.toFixed(3)}%）
              <br />
              上界B: {reachabilityResult.counts.total_upper_bound_b_pair_rulemax}（{reachabilityResult.counts.coverage_upper_bound_b_percent.toFixed(3)}%）
              {reachabilityResult.counts.shown_ratio_exact_percent !== null &&
                reachabilityResult.counts.shown_ratio_exact_percent !== undefined && (
                  <>
                    <br />
                    exact比率: {reachabilityResult.counts.shown_ratio_exact_percent.toFixed(3)}%
                  </>
                )}
            </div>
          )}

          {reachabilityDisplayGroups.length > 0 && (
            <table data-testid="reachability-table">
              <thead>
                <tr>
                  <th>rank</th>
                  <th>手数</th>
                  <th>先頭規則</th>
                  <th>証拠概要</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {reachabilityDisplayGroups.map((group) => {
                  const row = group.representative;
                  const first = row.rule_sequence[0];
                  return (
                  <tr key={`assist-${row.rank}`}>
                    <td>{row.rank}</td>
                    <td>{row.steps_to_goal}手</td>
                    <td>
                      {first
                        ? `${first.rule_number}:${first.rule_name}${first.rule_kind === "single" && first.check !== null && first.check !== undefined ? ` (check=${first.check})` : ""}`
                        : "-"}
                    </td>
                    <td>
                      {first?.left_id && first?.right_id
                        ? `${first.left_id} / ${first.right_id}`
                        : first?.left !== null && first?.left !== undefined && first?.right !== null && first?.right !== undefined
                          ? `${first.left}/${first.right}`
                          : "n/a"}
                    </td>
                    <td>
                      <div className="step2-reachability-actions">
                        <button onClick={() => void handleExecuteHeadAssist(row)} disabled={loading}>
                          先頭手を実行
                        </button>
                        <button onClick={() => void handleExecuteHeadAssistAllSteps(row)} disabled={loading}>
                          全手順を実行
                        </button>
                        {group.options.length > 1 && (
                          <div className="step2-reachability-group-options">
                            <p className="hint">
                              同じ先頭手の候補が {group.options.length} 件あります。
                            </p>
                            <div className="row row-start">
                              <button
                                type="button"
                                onClick={() => void handleExecuteHeadAssistAllSteps(row)}
                                disabled={loading}
                              >
                                この候補をそのまま実行
                              </button>
                              <button
                                type="button"
                                onClick={() =>
                                  setOpenReachabilityFirstStepKey((prev) =>
                                    prev === group.firstStepKey ? null : group.firstStepKey
                                  )
                                }
                                disabled={loading}
                              >
                                {openReachabilityFirstStepKey === group.firstStepKey ? "候補リストを閉じる" : "リストから選ぶ"}
                              </button>
                            </div>
                            {openReachabilityFirstStepKey === group.firstStepKey && (
                              <ul className="step2-reachability-option-list">
                                {group.options.map((option) => (
                                  <li key={`assist-option-${group.firstStepKey}-${option.rank}`}>
                                    <span>rank {option.rank} / {option.steps_to_goal}手</span>
                                    <button
                                      type="button"
                                      onClick={() =>
                                        void handleExecuteHeadAssistAllSteps(option, {
                                          rankOverride: option.rank,
                                          stepsOverride: option.rule_sequence
                                        })
                                      }
                                      disabled={loading}
                                    >
                                      この候補を実行
                                    </button>
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                );})}
              </tbody>
            </table>
          )}
          {reachabilityResult?.counts.has_next && (
            <div className="row">
              <button onClick={() => void handleReachabilityLoadMore()} disabled={loading || !reachabilityJobId}>
                さらに10件表示
              </button>
            </div>
          )}

          <label className="numeration-legacy-source-label">
            process（Perl target出力相当）
            <textarea
              aria-label="step2-process-text"
              className="numeration-legacy-source"
              rows={7}
              value={step2ProcessText}
              readOnly
            />
          </label>
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
              {renderTreeGraphSvg(treeGraph, "tree-graph")}
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

        <section className="card" data-panel="grammarInspect">
          <h2>6. 文法規則の内容確認</h2>
          <p className="hint">
            選択中 Grammar:
            {" "}
            {activeSetupGrammarOption?.display_name || setupGrammarId}
          </p>
          <p className="hint">
            このシステムで用いられる Merge規則は、次の規則です（選択文法の定義に基づく）。
          </p>
          <div className="inspect-table-wrap">
            <table data-testid="merge-rule-table">
              <thead>
                <tr>
                  <th>番号</th>
                  <th>規則名</th>
                  <th>種別</th>
                  <th>原本ファイル</th>
                  <th>比較</th>
                </tr>
              </thead>
              <tbody>
                {inspectMergeRules.length === 0 && (
                  <tr>
                    <td colSpan={5}>規則はまだ読み込まれていません。</td>
                  </tr>
                )}
                {inspectMergeRules.map((row) => (
                  <tr key={`merge-rule-${row.rule_number}`}>
                    <td>{row.rule_number}</td>
                    <td>
                      {row.rule_name}
                      {row.is_core_merge ? "（コア）" : ""}
                    </td>
                    <td>{row.rule_kind}</td>
                    <td>{row.file_name}</td>
                    <td>
                      <button
                        type="button"
                        onClick={() => {
                          void handleOpenRuleCompare(setupGrammarId, row.rule_number);
                        }}
                        disabled={loading}
                      >
                        移植前後を比較
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="row row-end grammar-inspect-footer">
            <button
              type="button"
              className="secondary-btn"
              onClick={() => {
                void jumpToReferenceDocs();
              }}
              disabled={loading}
            >
              資料を閲覧
            </button>
          </div>
        </section>

        <section className="card" data-panel="lexiconInspect">
          <h2>7. 語彙の内容確認</h2>
          <div className="row">
            <p className="hint inspect-summary-inline">
              選択中 Lexicon:
              {" "}
              {activeSetupGrammarOption?.display_name || setupGrammarId}
            </p>
          </div>
          {inspectLexiconSummary && (
            <div className="inspect-summary-grid">
              <div>
                <div className="inspect-summary-label">CSV</div>
                <div className="inspect-summary-value">{inspectLexiconSummary.source_csv}</div>
              </div>
              <div>
                <div className="inspect-summary-label">語彙件数</div>
                <div className="inspect-summary-value">{inspectLexiconSummary.entry_count}</div>
              </div>
              <div>
                <div className="inspect-summary-label">原本CGI</div>
                <div className="inspect-summary-value">
                  {inspectLexiconSummary.legacy_lexicon_cgi_url ? (
                    <a href={`${LEGACY_PERL_BASE_URL}${inspectLexiconSummary.legacy_lexicon_cgi_url}`} target="_blank" rel="noreferrer">
                      lexicon.cgi 相当を開く
                    </a>
                  ) : (
                    "該当なし"
                  )}
                </div>
              </div>
            </div>
          )}
          {inspectLexiconSummary && inspectLexiconSummary.category_counts.length > 0 && (
            <div className="inspect-category-row">
              <div className="inspect-category-chips">
                {inspectLexiconSummary.category_counts.map((row) => (
                  <button
                    key={`cat-${row.category}`}
                    type="button"
                    className={
                      inspectLexiconCategoryFilter === row.category
                        ? "token-chip token-chip-filter active"
                        : "token-chip token-chip-filter"
                    }
                    onClick={() => {
                      const nextCategory =
                        inspectLexiconCategoryFilter === row.category ? null : row.category;
                      void handleOpenLexiconInspect(setupGrammarId, 1, nextCategory);
                    }}
                    disabled={loading}
                  >
                    {row.category || "(空)"}: {row.count}
                  </button>
                ))}
              </div>
              {inspectLexiconCategoryFilter && (
                <button
                  type="button"
                  className="token-chip token-chip-filter inspect-clear-chip"
                  onClick={() => {
                    void handleOpenLexiconInspect(setupGrammarId, 1, null);
                  }}
                  disabled={loading}
                >
                  絞り込み解除（{inspectLexiconCategoryFilter}）
                </button>
              )}
            </div>
          )}
          <div className="inspect-table-wrap">
            <table data-testid="lexicon-inspect-table">
              <thead>
                <tr>
                  <th>no</th>
                  <th>entry</th>
                  <th>phono</th>
                  <th>cat</th>
                  <th>sy</th>
                  <th>se</th>
                </tr>
              </thead>
              <tbody>
                {!inspectLexiconItems || inspectLexiconItems.items.length === 0 ? (
                  <tr>
                    <td colSpan={6}>語彙はまだ読み込まれていません。</td>
                  </tr>
                ) : (
                  inspectLexiconItems.items.map((row) => (
                    <tr key={`lexicon-item-${row.lexicon_id}`}>
                      <td>{row.lexicon_id}</td>
                      <td>{row.entry}</td>
                      <td>{row.phono}</td>
                      <td>{row.category}</td>
                      <td className="mono">{row.sync_features.join(" / ")}</td>
                      <td className="mono">{row.semantics.join(" / ")}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          {inspectLexiconItems && inspectLexiconItems.total_pages > 0 && (
            <div className="row">
              <button
                type="button"
                onClick={() => {
                  void handleOpenLexiconInspect(
                    setupGrammarId,
                    inspectLexiconItems.page - 1,
                    inspectLexiconCategoryFilter
                  );
                }}
                disabled={loading || inspectLexiconItems.page <= 1}
              >
                前へ
              </button>
              <span className="mono">
                page {inspectLexiconItems.page} / {inspectLexiconItems.total_pages}
              </span>
              <button
                type="button"
                onClick={() => {
                  void handleOpenLexiconInspect(
                    setupGrammarId,
                    inspectLexiconItems.page + 1,
                    inspectLexiconCategoryFilter
                  );
                }}
                disabled={loading || inspectLexiconItems.page >= inspectLexiconItems.total_pages}
              >
                次へ
              </button>
            </div>
          )}
        </section>

        <section className="card" data-panel="ruleCompare">
          <h2>8. 移植前後コード比較（規則単位）</h2>
          <div className="row">
            <button
              type="button"
              className="secondary-btn"
              onClick={() => {
                setRenewMenu("reference");
                setRenewPanel("grammarInspect");
              }}
            >
              文法規則の内容確認へ戻る
            </button>
            <label>
              比較対象規則
              <select
                aria-label="rule-compare-select"
                value={inspectCompareRuleNumber?.toString() || ""}
                onChange={(event) => {
                  const nextRuleNumber = Number(event.target.value);
                  if (Number.isInteger(nextRuleNumber) && nextRuleNumber > 0) {
                    setInspectCompareRuleNumber(nextRuleNumber);
                  } else {
                    setInspectCompareRuleNumber(null);
                  }
                }}
              >
                <option value="">（規則を選択）</option>
                {inspectMergeRules.map((row) => (
                  <option key={`compare-rule-${row.rule_number}`} value={row.rule_number}>
                    {row.rule_number}: {row.rule_name}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              onClick={() => {
                if (inspectCompareRuleNumber) {
                  void handleOpenRuleCompare(setupGrammarId, inspectCompareRuleNumber);
                }
              }}
              disabled={loading || !inspectCompareRuleNumber}
            >
              比較を表示
            </button>
          </div>
          {!inspectRuleCompare ? (
            <p className="hint">規則を選んで比較を表示してください。</p>
          ) : (
            <div className="compare-grid">
              <div className="compare-pane">
                <h3>移植前（Perl）: {inspectRuleCompare.perl_file_name}</h3>
                <pre data-testid="perl-rule-source">{inspectRuleCompare.perl_source_text}</pre>
              </div>
              <div className="compare-pane">
                <h3>移植後（Python）: {inspectRuleCompare.python_file_name}</h3>
                <pre data-testid="python-rule-source">{inspectRuleCompare.python_source_text}</pre>
              </div>
            </div>
          )}
        </section>

        <section className="card" data-panel="referenceDocs" ref={referenceSectionRef}>
          <h2>9. 資料参照（素性資料 / 規則資料）</h2>
          <div className="row">
            <button
              type="button"
              className={referenceDocTab === "feature" ? "renew-step-btn active" : "renew-step-btn"}
              onClick={() => setReferenceDocTab("feature")}
            >
              素性資料
            </button>
            <button
              type="button"
              className={referenceDocTab === "rule" ? "renew-step-btn active" : "renew-step-btn"}
              onClick={() => setReferenceDocTab("rule")}
            >
              規則資料
            </button>
          </div>

          {referenceDocTab === "feature" ? (
            <>
              <div className="row">
                <select
                  aria-label="feature-doc-select"
                  value={selectedFeatureDoc}
                  onChange={(event) => setSelectedFeatureDoc(event.target.value)}
                >
                  <option value="">（素性資料を選択）</option>
                  {featureDocs.map((doc) => (
                    <option key={doc.file_name} value={doc.file_name}>
                      {doc.title}
                    </option>
                  ))}
                </select>
                <button
                  onClick={() => {
                    void handleOpenFeatureDoc(selectedFeatureDoc);
                  }}
                  disabled={loading || selectedFeatureDoc === ""}
                >
                  表示
                </button>
              </div>
              <iframe
                title="feature-doc"
                srcDoc={featureDocHtml}
                style={{ width: "100%", height: 260 }}
              />
            </>
          ) : (
            <>
              <div className="row">
                <select
                  aria-label="rule-doc-select"
                  value={selectedRuleDoc}
                  onChange={(event) => setSelectedRuleDoc(event.target.value)}
                >
                  <option value="">（規則資料を選択）</option>
                  {ruleDocs.map((doc) => (
                    <option key={`${doc.rule_number}-${doc.file_name}`} value={doc.file_name}>
                      {doc.rule_number}: {doc.rule_name}
                    </option>
                  ))}
                </select>
                <button
                  onClick={() => {
                    void handleOpenRuleDoc(selectedRuleDoc);
                  }}
                  disabled={loading || selectedRuleDoc === ""}
                >
                  表示
                </button>
              </div>
              <iframe title="rule-doc" srcDoc={ruleDocHtml} style={{ width: "100%", height: 260 }} />
            </>
          )}
        </section>

        <section className="card" data-panel="lexicon">
          {renewPanel === "lexicon" ? (
            <LexiconWorkbench
              grammarId={grammarId}
              focusLexiconId={lexiconFocusLexiconId}
              focusLexiconNonce={lexiconFocusRequestSeq}
            />
          ) : null}
        </section>
          </main>
        </section>
      </div>
      )}
    </div>
  );
}
