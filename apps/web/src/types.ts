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

export type HeadAssistSuggestion = {
  rank: number;
  rule_number: number;
  rule_name: string;
  rule_kind: "double" | "single";
  left: number;
  right: number;
  check?: number;
  unresolved_before: number;
  unresolved_after: number;
  unresolved_delta: number;
  grammatical_after: boolean;
  basenum_before: number;
  basenum_after: number;
  reachable_grammatical: boolean;
  steps_to_grammatical?: number | null;
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
