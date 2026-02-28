export type DerivationState = {
  grammar_id: string;
  memo: string;
  newnum: number;
  basenum: number;
  history: string;
  base: unknown[];
};

export type RuleCandidate = {
  rule_number: number;
  rule_name: string;
  rule_kind: "double" | "single";
  left?: number;
  right?: number;
  check?: number;
};

export type ReachabilityRuleStep = {
  step: number;
  rule_name: string;
  rule_number: number;
  rule_kind: "double" | "single";
  left?: number | null;
  right?: number | null;
  check?: number | null;
  left_id?: string | null;
  right_id?: string | null;
};

export type ReachabilityEvidence = {
  rank: number;
  steps_to_goal: number;
  rule_sequence: ReachabilityRuleStep[];
  tree_root: Record<string, unknown>;
  process_text?: string | null;
};

export type ReachabilityMetrics = {
  expanded_nodes: number;
  generated_nodes: number;
  packed_nodes: number;
  max_frontier: number;
  elapsed_ms: number;
  max_depth_reached: number;
  actions_attempted: number;
};

export type ReachabilityCounts = {
  count_unit: string;
  count_basis: string;
  tree_signature_basis: string;
  count_status: "exact" | "upper_bound_only" | "unknown";
  goal_count_exact?: string | null;
  total_exact?: string | null;
  total_upper_bound_a_pair_only: string;
  total_upper_bound_b_pair_rulemax: string;
  rule_max_per_pair_bound: number;
  rule_max_per_pair_observed: number;
  shown_count: number;
  offset: number;
  limit: number;
  shown_ratio_exact_percent?: number | null;
  coverage_upper_bound_a_percent: number;
  coverage_upper_bound_b_percent: number;
  has_next: boolean;
};

export type ReachabilityResponse = {
  status: "reachable" | "unreachable" | "unknown" | "failed";
  completed: boolean;
  reason: string;
  metrics: ReachabilityMetrics;
  counts: ReachabilityCounts;
  evidences: ReachabilityEvidence[];
};

export type ReachabilityJobStartResponse = {
  job_id: string;
  status: string;
  created_at: number;
};

export type ReachabilityProgress = {
  percent: number;
  phase: string;
  message: string;
};

export type ReachabilityJobStatusResponse = {
  job_id: string;
  status: "queued" | "running" | "reachable" | "unreachable" | "unknown" | "failed";
  created_at: number;
  updated_at: number;
  progress: ReachabilityProgress;
  metrics?: ReachabilityMetrics | null;
  counts?: ReachabilityCounts | null;
  reason?: string | null;
  completed?: boolean | null;
  error?: string | null;
};

export type ReachabilityEvidencePageResponse = {
  job_id: string;
  status: string;
  counts: ReachabilityCounts;
  evidences: ReachabilityEvidence[];
};

export type TokenResolution = {
  token: string;
  lexicon_id: number;
  candidate_lexicon_ids: number[];
};

export type GeneratedNumeration = {
  memo: string;
  lexicon_ids: number[];
  token_resolutions: TokenResolution[];
  numeration_text: string;
};

export type GrammarOption = {
  grammar_id: string;
  folder: string;
  uses_lexicon_all: boolean;
  display_name: string;
};

export type NumerationFileEntry = {
  path: string;
  file_name: string;
  memo: string;
  source: string;
};

export type ObservationTreeResponse = {
  mode: "tree" | "tree_cat";
  csv_lines: string[];
  csv_text: string;
};

export type LfItem = {
  lexical_id: string;
  category: string;
  idslot: string;
  semantics: string[];
  predication: string[][];
};

export type LfResponse = {
  list_representation: LfItem[];
  unresolved_feature_like_token: boolean;
};

export type SrLayer = {
  object_id: number;
  layer: number;
  kind: "object" | "Predication";
  properties: string[];
};

export type SrResponse = {
  truth_conditional_meaning: SrLayer[];
};

export type LexiconExportResponse = {
  grammar_id: string;
  format: "yaml" | "csv";
  lexicon_path: string;
  entry_count: number;
  content_text: string;
};

export type LexiconValidateResponse = {
  grammar_id: string;
  valid: boolean;
  entry_count: number;
  errors: string[];
  normalized_yaml_text: string;
  preview_csv_text: string;
};

export type LexiconImportResponse = {
  grammar_id: string;
  entry_count: number;
  normalized_yaml_text: string;
  csv_text: string;
};

export type LexiconCommitResponse = {
  grammar_id: string;
  committed: boolean;
  rolled_back: boolean;
  compatibility_passed: boolean;
  run_compatibility_tests: boolean;
  entry_count: number;
  lexicon_path: string;
  backup_path: string;
  message: string;
  errors: string[];
  normalized_yaml_text: string;
  committed_csv_text: string;
  command: string;
  stdout: string;
  stderr: string;
};

export type FeatureDocEntry = {
  file_name: string;
  title: string;
};

export type RuleDocEntry = {
  rule_number: number;
  rule_name: string;
  file_name: string;
};

export type HtmlDocResponse = {
  file_name: string;
  html_text: string;
};

export type GrammarRuleSourceEntry = {
  rule_number: number;
  rule_name: string;
  file_name: string;
  exists: boolean;
};

export type GrammarRuleSourceResponse = {
  grammar_id: string;
  rule_number: number;
  rule_name: string;
  file_name: string;
  source_text: string;
};

export type LexiconSummaryItem = {
  category: string;
  count: number;
};

export type LexiconSummaryResponse = {
  grammar_id: string;
  display_name: string;
  source_csv: string;
  entry_count: number;
  legacy_grammar_no: number | null;
  legacy_lexicon_cgi_url: string | null;
  category_counts: LexiconSummaryItem[];
};

export type LexiconInspectItem = {
  lexicon_id: number;
  entry: string;
  phono: string;
  category: string;
  sync_features: string[];
  idslot: string;
  semantics: string[];
  note: string;
};

export type LexiconItemsPageResponse = {
  grammar_id: string;
  category_filter: string | null;
  page: number;
  page_size: number;
  total_count: number;
  total_pages: number;
  items: LexiconInspectItem[];
};

export type LexiconItemLookupItem = {
  lexicon_id: number;
  found: boolean;
  entry: string;
  phono: string;
  category: string;
  sync_features: string[];
  idslot: string;
  semantics: string[];
  note: string;
};

export type LexiconItemsLookupResponse = {
  grammar_id: string;
  requested_count: number;
  found_count: number;
  missing_ids: number[];
  items: LexiconItemLookupItem[];
};

export type MergeRuleEntry = {
  rule_number: number;
  rule_name: string;
  rule_kind: "single" | "double";
  file_name: string;
  is_core_merge: boolean;
};

export type RuleCompareResponse = {
  grammar_id: string;
  rule_number: number;
  rule_name: string;
  perl_file_name: string;
  perl_source_text: string;
  python_file_name: string;
  python_source_text: string;
};

export type ProcessExportResponse = {
  process_text: string;
};

export type LexiconExtItem = {
  lexicon_id?: number | null;
  entry: string;
  phono: string;
  category: string;
  predicates: string[][];
  sync_features: string[];
  idslot: string;
  semantics: string[];
  note: string;
};

export type LexiconExtItemResponse = {
  grammar_id: string;
  item: LexiconExtItem;
};

export type LexiconExtItemsResponse = {
  grammar_id: string;
  total_count: number;
  page: number;
  page_size: number;
  items: LexiconExtItem[];
};

export type ValueDictionaryKind =
  | "category"
  | "predicate"
  | "sync_feature"
  | "idslot"
  | "semantic";

export type ValueDictionaryItem = {
  id: number;
  kind: ValueDictionaryKind;
  normalized_value: string;
  display_value: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type ValueDictionaryListResponse = {
  source?: "db" | "lexicon_fallback";
  items: ValueDictionaryItem[];
};

export type ValueDictionaryUsageLexiconItem = {
  grammar_id: string;
  lexicon_id: number;
  entry: string;
  category: string;
  match_count: number;
};

export type ValueDictionaryUsageResponse = {
  source?: "db" | "lexicon_fallback";
  id: number;
  kind: ValueDictionaryKind;
  display_value: string;
  total_usages: number;
  usages_by_grammar: Record<string, number>;
  usage_lexicon_items: ValueDictionaryUsageLexiconItem[];
};

export type NumLinkItem = {
  id: number;
  grammar_id: string;
  lexicon_id: number;
  num_path: string;
  memo: string;
  slot_no?: number | null;
  idx_value: string;
  comment: string;
  created_at: string;
  updated_at: string;
};

export type NumLinksResponse = {
  items: NumLinkItem[];
};

export type NoteCurrentResponse = {
  grammar_id: string;
  lexicon_id: number;
  markdown: string;
  updated_at?: string | null;
};

export type NoteRevisionItem = {
  id: number;
  revision_no: number;
  author: string;
  created_at: string;
  change_summary: string;
};

export type NoteRevisionsResponse = {
  items: NoteRevisionItem[];
};

export type NoteRevisionResponse = {
  id: number;
  revision_no: number;
  markdown: string;
  author: string;
  created_at: string;
  change_summary: string;
};

export type LexiconVersionItem = {
  revision_id: string;
  author: string;
  date: string;
  message: string;
};

export type LexiconVersionsResponse = {
  grammar_id: string;
  lexicon_path: string;
  items: LexiconVersionItem[];
};

export type LexiconVersionDiffResponse = {
  grammar_id: string;
  revision_id: string;
  diff_text: string;
};
