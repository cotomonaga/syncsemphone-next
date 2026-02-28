import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "../App";

type MockResponse = {
  status?: number;
  body: unknown;
};

const DEFAULT_GRAMMAR_OPTIONS = [
  {
    grammar_id: "imi01",
    folder: "imi01",
    uses_lexicon_all: true,
    display_name: "IMI 共同研究用・日本語文法片 01"
  },
  {
    grammar_id: "imi02",
    folder: "imi02",
    uses_lexicon_all: true,
    display_name: "IMI 共同研究用・日本語文法片 02"
  },
  {
    grammar_id: "imi03",
    folder: "imi03",
    uses_lexicon_all: true,
    display_name: "IMI 共同研究用・日本語文法片 03"
  },
  {
    grammar_id: "japanese2",
    folder: "japanese2",
    uses_lexicon_all: false,
    display_name: "日本語（統語意味論版）"
  }
];

const DEFAULT_SET_NUMERATION_FILES = [
  {
    path: "/repo/imi01/set-numeration/00.num",
    file_name: "00.num",
    memo: "白いギターの箱",
    source: "set"
  },
  {
    path: "/repo/imi01/set-numeration/04.num",
    file_name: "04.num",
    memo: "ジョンが本を読んだ",
    source: "set"
  },
  {
    path: "/repo/imi01/set-numeration/1606324760.num",
    file_name: "1606324760.num",
    memo: "ジョンがメアリを追いかけた",
    source: "set"
  }
];

function jsonResponse({ status = 200, body }: MockResponse): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

function maybeCommonResponse(url: string): Response | null {
  if (url.endsWith("/v1/derivation/grammars")) {
    return jsonResponse({ body: DEFAULT_GRAMMAR_OPTIONS });
  }
  if (url.includes("/v1/derivation/numeration/files?grammar_id=imi01&source=set")) {
    return jsonResponse({ body: DEFAULT_SET_NUMERATION_FILES });
  }
  if (url.includes("/v1/derivation/numeration/files?grammar_id=imi01&source=saved")) {
    return jsonResponse({ body: [] });
  }
  if (url.endsWith("/v1/derivation/process/export")) {
    return jsonResponse({
      body: {
        process_text: "imi01\nmemo\n7\n6\n\n[null]"
      }
    });
  }
  return null;
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("App", () => {
  it("starts from Step0 with imi01 defaults", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    expect(await screen.findByRole("heading", { name: "SYNCSEMPHONE NEXT" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Hypothesis Loop Workbench" })).not.toBeInTheDocument();

    expect(
      await screen.findByRole("button", { name: "【Step.0】LexiconとGrammarの選択" })
    ).toBeInTheDocument();

    const grammarSelect = (await screen.findByLabelText("Step0 Grammar")) as HTMLSelectElement;
    expect(grammarSelect.value).toBe("imi01");

    const startButton = screen.getByRole("button", { name: "この設定で開始" });
    expect(startButton).toBeEnabled();

    await user.click(startButton);

    expect(await screen.findByText(/適用中のGrammar:/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "【Step.1】Numerationの形成" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "例文から選ぶ" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "numファイルを選ぶ" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Lexiconから組み立てる" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Numerationを形成" })).toBeInTheDocument();
  });

  it("moves to Step2 Grammar apply after Numeration formation and keeps manual mode", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      if (url.endsWith("/v1/derivation/numeration/tokenize")) {
        return jsonResponse({ body: { tokens: ["ジョン", "が", "本", "を", "読んだ"] } });
      }
      if (url.endsWith("/v1/derivation/numeration/generate")) {
        const payload = init?.body ? JSON.parse(String(init.body)) : {};
        return jsonResponse({
          body: {
            memo: payload.sentence || "ジョンが本を読んだ",
            lexicon_ids: [60, 19, 120],
            token_resolutions: [],
            numeration_text: `${payload.sentence || "ジョンが本を読んだ"}\t60\t19\t120\n \t\t\t\n \t1\t2\t3`
          }
        });
      }
      if (url.endsWith("/v1/reference/grammars/imi01/lexicon-items/by-ids")) {
        return jsonResponse({
          body: {
            grammar_id: "imi01",
            requested_count: 3,
            found_count: 3,
            missing_ids: [],
            items: [
              {
                lexicon_id: 60,
                found: true,
                entry: "ジョン",
                phono: "ジョン",
                category: "N",
                sync_features: [],
                idslot: "id",
                semantics: ["Name:ジョン"],
                note: ""
              },
              {
                lexicon_id: 19,
                found: true,
                entry: "が",
                phono: "が",
                category: "J",
                sync_features: ["0,17,N,,,right,nonhead", "3,17,V,,,left,nonhead", "4,11,ga"],
                idslot: "zero",
                semantics: [],
                note: ""
              },
              {
                lexicon_id: 120,
                found: true,
                entry: "読んだ",
                phono: "ヨンダ",
                category: "T",
                sync_features: [],
                idslot: "0,24",
                semantics: ["Time:past"],
                note: ""
              }
            ]
          }
        });
      }
      if (url.endsWith("/v1/derivation/init")) {
        return jsonResponse({
          body: {
            grammar_id: "imi01",
            memo: "ジョンが本を読んだ",
            newnum: 6,
            basenum: 3,
            history: "",
            base: [
              null,
              ["x1-1", "N", [], [], "x1-1", ["Name:ジョン"], "ジョン", [], ""],
              ["x2-1", "J", [], ["0,17,N,,,right,nonhead"], "", [], "が", [], ""],
              ["x3-1", "T", [], ["0,24"], "", ["Time:past"], "読んだ", [], ""]
            ]
          }
        });
      }
      if (url.endsWith("/v1/derivation/candidates")) {
        const payload = init?.body ? JSON.parse(String(init.body)) : {};
        if (payload.left === 1 && payload.right === 2) {
          return jsonResponse({
            body: [
              {
                rule_number: 1,
                rule_name: "RH-Merge",
                rule_kind: "double",
                left: 1,
                right: 2
              }
            ]
          });
        }
        return jsonResponse({ body: [] });
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "この設定で開始" }));
    await user.click(screen.getByRole("button", { name: "Numerationを形成" }));

    expect(await screen.findByRole("heading", { name: "【Step.2】Grammarの適用" })).toBeInTheDocument();
    expect(screen.getByText(/手動で left\/right と rule を選んで適用します/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Load Candidates" })).not.toBeInTheDocument();
    expect(await screen.findByTestId("candidate-table")).toHaveTextContent("1:RH-Merge");
    expect(screen.getByRole("button", { name: "候補を提案" })).toBeInTheDocument();
  });

  it("shows auto split result immediately after Step0 start without mode toggle", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      if (url.endsWith("/v1/derivation/numeration/tokenize")) {
        return jsonResponse({ body: { tokens: ["ジョン", "が", "本", "を", "読んだ"] } });
      }
      if (url.endsWith("/v1/derivation/numeration/generate")) {
        const payload = init?.body ? JSON.parse(String(init.body)) : {};
        return jsonResponse({
          body: {
            memo: payload.sentence || "ジョンが本を読んだ",
            lexicon_ids: [60, 19, 120],
            token_resolutions: [],
            numeration_text: `${payload.sentence || "ジョンが本を読んだ"}\t60\t19\t120\n \t\t\t\n \t1\t2\t3`
          }
        });
      }
      if (url.endsWith("/v1/reference/grammars/imi01/lexicon-items/by-ids")) {
        return jsonResponse({
          body: {
            grammar_id: "imi01",
            requested_count: 3,
            found_count: 0,
            missing_ids: [60, 19, 120],
            items: []
          }
        });
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "この設定で開始" }));
    const tokenRow = await screen.findByTestId("token-chip-row");

    await waitFor(() => {
      expect(tokenRow).toHaveTextContent("ジョン");
      expect(tokenRow).toHaveTextContent("読んだ");
      expect(tokenRow).not.toHaveTextContent("（まだ分割結果がありません）");
    });
  });

  it("assists left/right selection by ranked head-direction suggestions", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      if (url.endsWith("/v1/derivation/numeration/tokenize")) {
        return jsonResponse({ body: { tokens: ["ジョン", "が", "メアリ", "を", "追いかける", "た"] } });
      }
      if (url.endsWith("/v1/derivation/numeration/generate")) {
        const payload = init?.body ? JSON.parse(String(init.body)) : {};
        return jsonResponse({
          body: {
            memo: payload.sentence || "ジョンがメアリを追いかけた",
            lexicon_ids: [60, 19, 103, 23, 187, 203],
            token_resolutions: [],
            numeration_text:
              `${payload.sentence || "ジョンがメアリを追いかけた"}\t60\t19\t103\t23\t187\t203\n` +
              " \t\t\t\t\t\t\n" +
              " \t1\t2\t3\t4\t5\t6"
          }
        });
      }
      if (url.endsWith("/v1/reference/grammars/imi01/lexicon-items/by-ids")) {
        return jsonResponse({
          body: {
            grammar_id: "imi01",
            requested_count: 6,
            found_count: 6,
            missing_ids: [],
            items: []
          }
        });
      }
      if (url.endsWith("/v1/derivation/init")) {
        return jsonResponse({
          body: {
            grammar_id: "imi01",
            memo: "ジョンがメアリを追いかけた",
            newnum: 7,
            basenum: 6,
            history: "",
            base: [
              null,
              ["x1-1", "N", [], [], "x1-1", ["Name:ジョン"], "ジョン", ["zero", "zero"]],
              ["x2-1", "J", [], ["0,17,N,,,right,nonhead"], "zero", [], "が", ["zero", "zero"]],
              ["x3-1", "N", [], [], "x3-1", ["Name:メアリ"], "メアリ", ["zero", "zero"]],
              ["x4-1", "J", [], ["0,17,N,,,right,nonhead"], "zero", [], "を", ["zero", "zero"]],
              ["x5-1", "V", [], ["2,17,T,,,left,head"], "x5-1", ["Theme:2,33,wo"], "追いかけ-", ["zero", "zero"]],
              ["x6-1", "T", [], ["0,17,V,,,right,nonhead"], "0,24", ["Time:past"], "-ta", ["zero", "zero"]]
            ]
          }
        });
      }
      if (url.endsWith("/v1/derivation/reachability/jobs")) {
        return jsonResponse({
          body: {
            job_id: "job-1",
            status: "queued",
            created_at: 1
          }
        });
      }
      if (url.endsWith("/v1/derivation/reachability/jobs/job-1")) {
        return jsonResponse({
          body: {
            job_id: "job-1",
            status: "reachable",
            created_at: 1,
            updated_at: 2,
            progress: { percent: 100, phase: "done", message: "ok" },
            completed: true,
            reason: "goal_found",
            metrics: {
              expanded_nodes: 12,
              generated_nodes: 18,
              packed_nodes: 10,
              max_frontier: 4,
              elapsed_ms: 8,
              max_depth_reached: 2,
              actions_attempted: 20
            },
            counts: {
              count_unit: "derivation_tree",
              count_basis: "structural_signature_v1",
              tree_signature_basis: "canonical_tree_v1",
              count_status: "upper_bound_only",
              goal_count_exact: null,
              total_exact: null,
              total_upper_bound_a_pair_only: "100",
              total_upper_bound_b_pair_rulemax: "200",
              rule_max_per_pair_bound: 4,
              rule_max_per_pair_observed: 2,
              shown_count: 1,
              offset: 0,
              limit: 10,
              shown_ratio_exact_percent: null,
              coverage_upper_bound_a_percent: 1,
              coverage_upper_bound_b_percent: 0.5,
              has_next: false
            }
          }
        });
      }
      if (url.includes("/v1/derivation/reachability/jobs/job-1/evidences")) {
        return jsonResponse({
          body: {
            job_id: "job-1",
            status: "reachable",
            counts: {
              count_unit: "derivation_tree",
              count_basis: "structural_signature_v1",
              tree_signature_basis: "canonical_tree_v1",
              count_status: "upper_bound_only",
              goal_count_exact: null,
              total_exact: null,
              total_upper_bound_a_pair_only: "100",
              total_upper_bound_b_pair_rulemax: "200",
              rule_max_per_pair_bound: 4,
              rule_max_per_pair_observed: 2,
              shown_count: 1,
              offset: 0,
              limit: 10,
              shown_ratio_exact_percent: null,
              coverage_upper_bound_a_percent: 1,
              coverage_upper_bound_b_percent: 0.5,
              has_next: false
            },
            evidences: [
              {
                rank: 1,
                steps_to_goal: 3,
                rule_sequence: [
                  {
                    step: 1,
                    rule_name: "LH-Merge",
                    rule_number: 2,
                    rule_kind: "double",
                    left: 5,
                    right: 6,
                    check: null,
                    left_id: "x5-1",
                    right_id: "x6-1"
                  }
                ],
                tree_root: {},
                process_text: "dummy"
              }
            ]
          }
        });
      }
      if (url.endsWith("/v1/derivation/candidates")) {
        const payload = init?.body ? JSON.parse(String(init.body)) : {};
        if (payload.left === 5 && payload.right === 6) {
          return jsonResponse({
            body: [
              {
                rule_number: 2,
                rule_name: "LH-Merge",
                rule_kind: "double",
                left: 5,
                right: 6
              }
            ]
          });
        }
        return jsonResponse({ body: [] });
      }
      if (url.endsWith("/v1/derivation/execute")) {
        const payload = init?.body ? JSON.parse(String(init.body)) : {};
        if (payload.rule_name === "LH-Merge") {
          return jsonResponse({
            body: {
              grammar_id: "imi01",
              memo: "ジョンがメアリを追いかけた",
              newnum: 7,
              basenum: 5,
              history: "([x5-1 x6-1] LH-Merge) ",
              base: [
                null,
                ["x1-1", "N", [], [], "x1-1", ["Name:ジョン"], "ジョン", ["zero", "zero"]],
                ["x2-1", "J", [], ["0,17,N,,,right,nonhead"], "zero", [], "が", ["zero", "zero"]],
                ["x3-1", "N", [], [], "x3-1", ["Name:メアリ"], "メアリ", ["zero", "zero"]],
                ["x4-1", "J", [], ["0,17,N,,,right,nonhead"], "zero", [], "を", ["zero", "zero"]],
                ["x5-1", "T", [], ["0,17,V,,,right,nonhead"], "x5-1", ["Time:past"], "-ta", ["zero", "zero"]]
              ]
            }
          });
        }
        throw new Error(`unexpected execute payload: ${JSON.stringify(payload)}`);
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "この設定で開始" }));
    await user.click(screen.getByRole("button", { name: "Numerationを形成" }));

    const assistButton = await screen.findByRole("button", { name: "候補を提案" });
    expect(assistButton).toBeEnabled();
    await user.click(assistButton);
    expect(await screen.findByTestId("reachability-table")).toHaveTextContent("x5-1 / x6-1");

    await user.click(screen.getByRole("button", { name: "先頭手を実行" }));

    await waitFor(() => {
      expect(screen.getByTestId("current-history")).toHaveTextContent("([x5-1 x6-1] LH-Merge)");
    });

    await user.click(screen.getByRole("button", { name: "やりなおし" }));
    await waitFor(() => {
      expect(screen.getByTestId("current-history")).toHaveTextContent("(empty)");
    });
  });

  it("renders merged parent+children in Step2 target pane after execute", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      if (url.endsWith("/v1/derivation/numeration/tokenize")) {
        return jsonResponse({ body: { tokens: ["ジョン", "が"] } });
      }
      if (url.endsWith("/v1/derivation/numeration/generate")) {
        const payload = init?.body ? JSON.parse(String(init.body)) : {};
        return jsonResponse({
          body: {
            memo: payload.sentence || "ジョンが",
            lexicon_ids: [60, 19],
            token_resolutions: [],
            numeration_text: `${payload.sentence || "ジョンが"}\t60\t19\n \t\t\n \t1\t2`
          }
        });
      }
      if (url.endsWith("/v1/reference/grammars/imi01/lexicon-items/by-ids")) {
        return jsonResponse({
          body: {
            grammar_id: "imi01",
            requested_count: 2,
            found_count: 2,
            missing_ids: [],
            items: [
              {
                lexicon_id: 60,
                found: true,
                entry: "ジョン",
                phono: "ジョン",
                category: "N",
                sync_features: [],
                idslot: "id",
                semantics: ["Name:ジョン"],
                note: ""
              },
              {
                lexicon_id: 19,
                found: true,
                entry: "が",
                phono: "が",
                category: "J",
                sync_features: ["0,17,N,,,right,nonhead", "3,17,V,,,left,nonhead", "4,11,ga"],
                idslot: "zero",
                semantics: [],
                note: ""
              }
            ]
          }
        });
      }
      if (url.endsWith("/v1/derivation/init")) {
        return jsonResponse({
          body: {
            grammar_id: "imi01",
            memo: "ジョンが",
            newnum: 3,
            basenum: 2,
            history: "",
            base: [
              null,
              ["x1-1", "N", [], [], "x1-1", ["Name:ジョン"], "ジョン", ["zero", "zero"]],
              [
                "x2-1",
                "J",
                [],
                ["0,17,N,,,right,nonhead", "3,17,V,,,left,nonhead", "4,11,ga"],
                "zero",
                [],
                "が",
                ["zero", "zero"]
              ]
            ]
          }
        });
      }
      if (url.endsWith("/v1/derivation/candidates")) {
        const payload = init?.body ? JSON.parse(String(init.body)) : {};
        if (payload.left === 1 && payload.right === 2) {
          return jsonResponse({
            body: [
              {
                rule_number: 2,
                rule_name: "LH-Merge",
                rule_kind: "double",
                left: 1,
                right: 2
              }
            ]
          });
        }
        return jsonResponse({ body: [] });
      }
      if (url.endsWith("/v1/derivation/execute")) {
        const payload = init?.body ? JSON.parse(String(init.body)) : {};
        if (payload.rule_name === "LH-Merge") {
          return jsonResponse({
            body: {
              grammar_id: "imi01",
              memo: "ジョンが",
              newnum: 3,
              basenum: 1,
              history: "([x1-1 x2-1] LH-Merge) ",
              base: [
                null,
                [
                  "x1-1",
                  "N",
                  [],
                  ["3,17,V,,,left,nonhead", "4,11,ga"],
                  "x1-1",
                  ["Name:ジョン"],
                  null,
                  [
                    ["x1-1", "N", [], [], "x1-1", ["Name:ジョン"], "ジョン", ["zero", "zero"]],
                    ["x2-1", "J", [], [], "zero", [], "が", ["zero", "zero"]]
                  ]
                ]
              ]
            }
          });
        }
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "この設定で開始" }));
    await user.click(screen.getByRole("button", { name: "Numerationを形成" }));

    expect(await screen.findByTestId("candidate-table")).toHaveTextContent("2:LH-Merge");
    await user.click(screen.getByRole("button", { name: "実行" }));

    await waitFor(() => {
      expect(screen.getByTestId("current-history")).toHaveTextContent("([x1-1 x2-1] LH-Merge)");
    });

    const selectionList = await screen.findByTestId("step2-selection-list");
    expect(screen.getByTestId("step2-left-radio-1")).toBeInTheDocument();
    expect(screen.queryByTestId("step2-left-radio-2")).not.toBeInTheDocument();
    expect(selectionList).toHaveTextContent("x1-1");
    expect(selectionList).toHaveTextContent("+V(left)(nonhead)");
    expect(selectionList).toHaveTextContent("ga(★)");
    expect(selectionList).toHaveTextContent("Name: ジョン");
    expect(selectionList).toHaveTextContent("ジョン");
    expect(selectionList).toHaveTextContent("x2-1");
    expect(selectionList).toHaveTextContent("が");
  });

  it("keeps 候補を提案 enabled while auto candidate loading is in progress", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      if (url.endsWith("/v1/derivation/numeration/tokenize")) {
        return jsonResponse({ body: { tokens: ["ジョン", "が", "本", "を", "読んだ"] } });
      }
      if (url.endsWith("/v1/derivation/numeration/generate")) {
        return jsonResponse({
          body: {
            memo: "ジョンが本を読んだ",
            lexicon_ids: [60, 19, 100, 23, 226, 257],
            token_resolutions: [],
            numeration_text: "ジョンが本を読んだ\t60\t19\t100\t23\t226\t257\n \t\t\t\t\t\t\n \t1\t2\t3\t4\t5\t6"
          }
        });
      }
      if (url.endsWith("/v1/reference/grammars/imi01/lexicon-items/by-ids")) {
        return jsonResponse({
          body: {
            grammar_id: "imi01",
            requested_count: 6,
            found_count: 6,
            missing_ids: [],
            items: []
          }
        });
      }
      if (url.endsWith("/v1/derivation/init")) {
        return jsonResponse({
          body: {
            grammar_id: "imi01",
            memo: "ジョンが本を読んだ",
            newnum: 7,
            basenum: 6,
            history: "",
            base: [
              null,
              ["x1-1", "N", [], [], "x1-1", ["Name:ジョン"], "ジョン", ["zero", "zero"]],
              ["x2-1", "J", [], ["0,17,N,,,right,nonhead"], "zero", [], "が", ["zero", "zero"]],
              ["x3-1", "N", [], [], "x3-1", ["Kind:本"], "本", ["zero", "zero"]],
              ["x4-1", "J", [], ["0,17,N,,,right,nonhead"], "zero", [], "を", ["zero", "zero"]],
              ["x5-1", "V", [], [], "x5-1", ["Kind:読む"], "yom-", ["zero", "zero"]],
              ["x6-1", "T", [], ["0,17,naA,,,right,nonhead"], "2,22", ["Time:present"], "だ", ["zero", "zero"]]
            ]
          }
        });
      }
      if (url.endsWith("/v1/derivation/candidates")) {
        return new Promise((resolve) => {
          setTimeout(() => resolve(jsonResponse({ body: [] })), 500);
        });
      }
      if (url.endsWith("/v1/derivation/reachability/jobs")) {
        return jsonResponse({
          body: {
            job_id: "job-2",
            status: "queued",
            created_at: 1
          }
        });
      }
      if (url.endsWith("/v1/derivation/reachability/jobs/job-2")) {
        return jsonResponse({
          body: {
            job_id: "job-2",
            status: "reachable",
            created_at: 1,
            updated_at: 2,
            progress: { percent: 100, phase: "done", message: "ok" },
            completed: true,
            reason: "goal_found",
            metrics: {
              expanded_nodes: 9,
              generated_nodes: 12,
              packed_nodes: 7,
              max_frontier: 3,
              elapsed_ms: 10,
              max_depth_reached: 2,
              actions_attempted: 14
            },
            counts: {
              count_unit: "derivation_tree",
              count_basis: "structural_signature_v1",
              tree_signature_basis: "canonical_tree_v1",
              count_status: "upper_bound_only",
              goal_count_exact: null,
              total_exact: null,
              total_upper_bound_a_pair_only: "120",
              total_upper_bound_b_pair_rulemax: "240",
              rule_max_per_pair_bound: 4,
              rule_max_per_pair_observed: 2,
              shown_count: 1,
              offset: 0,
              limit: 10,
              shown_ratio_exact_percent: null,
              coverage_upper_bound_a_percent: 1,
              coverage_upper_bound_b_percent: 0.5,
              has_next: false
            }
          }
        });
      }
      if (url.includes("/v1/derivation/reachability/jobs/job-2/evidences")) {
        return jsonResponse({
          body: {
            job_id: "job-2",
            status: "reachable",
            counts: {
              count_unit: "derivation_tree",
              count_basis: "structural_signature_v1",
              tree_signature_basis: "canonical_tree_v1",
              count_status: "upper_bound_only",
              goal_count_exact: null,
              total_exact: null,
              total_upper_bound_a_pair_only: "120",
              total_upper_bound_b_pair_rulemax: "240",
              rule_max_per_pair_bound: 4,
              rule_max_per_pair_observed: 2,
              shown_count: 1,
              offset: 0,
              limit: 10,
              shown_ratio_exact_percent: null,
              coverage_upper_bound_a_percent: 1,
              coverage_upper_bound_b_percent: 0.5,
              has_next: false
            },
            evidences: [
              {
                rank: 1,
                steps_to_goal: 4,
                rule_sequence: [
                  {
                    step: 1,
                    rule_name: "RH-Merge",
                    rule_number: 1,
                    rule_kind: "double",
                    left: 1,
                    right: 2,
                    check: null,
                    left_id: "x1-1",
                    right_id: "x2-1"
                  }
                ],
                tree_root: {},
                process_text: "dummy"
              }
            ]
          }
        });
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "この設定で開始" }));
    await user.click(screen.getByRole("button", { name: "Numerationを形成" }));

    const assistButton = await screen.findByRole("button", { name: "候補を提案" });
    expect(assistButton).toBeEnabled();
    await user.click(assistButton);
    expect(await screen.findByTestId("reachability-table")).toHaveTextContent("1:RH-Merge");
  });

  it("toggles More as text and shows checkmark", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    const grammarSelect = (await screen.findByLabelText("Step0 Grammar")) as HTMLSelectElement;
    expect(grammarSelect.options).toHaveLength(3);

    const moreToggle = screen.getByLabelText("More toggle");
    expect(moreToggle).toHaveTextContent("More");

    await user.click(moreToggle);
    expect(screen.getByLabelText("More toggle")).toHaveTextContent("✓ More");
    expect(grammarSelect.options).toHaveLength(4);

    await user.click(screen.getByLabelText("More toggle"));
    expect(screen.getByLabelText("More toggle")).toHaveTextContent("More");
    expect(grammarSelect.options).toHaveLength(3);
  });

  it("switches Step1 numeration entry modes", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "この設定で開始" }));

    await user.click(screen.getByRole("button", { name: "numファイルを選ぶ" }));
    expect(screen.getByLabelText("Step1 Upload Numeration")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "例文から選ぶ" }));
    expect(screen.getByLabelText("Step1 Example Sentence")).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: "[白いギターの箱]" })
    ).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "[ジョンが本を読んだ]" })).toBeInTheDocument();
  });

  it("shows numeration lexicon reference when example sentence is selected", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      if (url.endsWith("/v1/derivation/numeration/load")) {
        return jsonResponse({
          body: {
            path: "/repo/imi01/set-numeration/04.num",
            memo: "ジョンが本を読んだ",
            numeration_text: "ジョンが本を読んだ\t60\t19\n \t+\t+\n \t1\t2"
          }
        });
      }
      if (url.endsWith("/v1/reference/grammars/imi01/lexicon-items/by-ids")) {
        return jsonResponse({
          body: {
            requested_count: 2,
            found_count: 2,
            missing_ids: [],
            items: [
              {
                lexicon_id: 60,
                found: true,
                entry: "John",
                phono: "ジョン",
                category: "N",
                sync_features: [],
                idslot: "id",
                semantics: ["Name:John"],
                note: ""
              },
              {
                lexicon_id: 19,
                found: true,
                entry: "を",
                phono: "を",
                category: "J",
                sync_features: ["0,17,N,,,right,nonhead", "3,17,V,,,left,nonhead", "4,11,wo"],
                idslot: "zero",
                semantics: ["Case:object"],
                note: ""
              }
            ]
          }
        });
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "この設定で開始" }));
    await user.click(screen.getByRole("button", { name: "例文から選ぶ" }));

    expect(screen.queryByLabelText("観察文（原文）")).not.toBeInTheDocument();
    const sentencePanel = screen.getByRole("button", { name: "例文から選ぶ" }).closest("section");
    expect(sentencePanel).not.toBeNull();
    expect(await within(sentencePanel!).findByText("numerationの語彙情報参照")).toBeInTheDocument();
    const lexiconTable = await within(sentencePanel!).findByTestId("numeration-lexicon-table");
    expect(lexiconTable).toHaveTextContent("Name: John");
    expect(lexiconTable).toHaveTextContent("を");
    expect(lexiconTable).toHaveTextContent("+N(right)(nonhead)");
    expect(lexiconTable).toHaveTextContent("+V(left)(nonhead)");
    expect(lexiconTable).toHaveTextContent("wo(★)");
  });

  it("keeps selected example sentence when switching to Lexicon build mode", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      if (url.endsWith("/v1/derivation/numeration/load")) {
        return jsonResponse({
          body: {
            path: "/repo/imi01/set-numeration/00.num",
            memo: "白い ギター の 箱",
            numeration_text: "白い ギター の 箱\t8\t45\t21\t88\n \t\t\t\n \t1\t2\t3\t4"
          }
        });
      }
      if (url.endsWith("/v1/reference/grammars/imi01/lexicon-items/by-ids")) {
        return jsonResponse({
          body: {
            requested_count: 4,
            found_count: 4,
            missing_ids: [],
            items: [
              {
                lexicon_id: 8,
                found: true,
                entry: "白い",
                phono: "シロイ",
                category: "D",
                sync_features: [],
                idslot: "1",
                semantics: ["white"],
                note: ""
              },
              {
                lexicon_id: 45,
                found: true,
                entry: "ギター",
                phono: "git",
                category: "N",
                sync_features: [],
                idslot: "2",
                semantics: ["guitar"],
                note: ""
              },
              {
                lexicon_id: 21,
                found: true,
                entry: "の",
                phono: "no",
                category: "P",
                sync_features: [],
                idslot: "3",
                semantics: ["of"],
                note: ""
              },
              {
                lexicon_id: 88,
                found: true,
                entry: "箱",
                phono: "hako",
                category: "N",
                sync_features: [],
                idslot: "4",
                semantics: ["box"],
                note: ""
              }
            ]
          }
        });
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "この設定で開始" }));

    await user.click(screen.getByRole("button", { name: "例文から選ぶ" }));
    expect(screen.queryByRole("textbox", { name: "Sentence" })).not.toBeInTheDocument();

    // load が成功するまで語彙参照が反映されるのを待つ
    const examplePanel = screen.getByRole("button", { name: "例文から選ぶ" }).closest("section");
    expect(examplePanel).not.toBeNull();
    await within(examplePanel!).findByTestId("numeration-lexicon-table");

    await user.click(screen.getByRole("button", { name: "Lexiconから組み立てる" }));

    const sentenceInput = await screen.findByRole("textbox", { name: "Sentence" });
    expect(sentenceInput).toHaveValue("白い ギター の 箱");
    expect(screen.queryByRole("textbox", { name: "Manual Tokens" })).not.toBeInTheDocument();
    expect(screen.getByTestId("token-input-mode")).toHaveTextContent("自動");
  });

  it("shows upload format error for invalid tab-delimited num text", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "この設定で開始" }));
    await user.click(screen.getByRole("button", { name: "numファイルを選ぶ" }));

    await user.type(screen.getByLabelText("Step1 Upload Numeration"), "invalid");
    expect(screen.getByTestId("step1-upload-error")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Numerationを形成" })).toBeDisabled();
  });

  it("opens lexicon inspection from Step0 and paginates", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      if (url.includes("/v1/reference/grammars/imi01/lexicon-summary")) {
        return jsonResponse({
          body: {
            grammar_id: "imi01",
            display_name: "IMI 共同研究用・日本語文法片 01",
            source_csv: "lexicon-all.csv",
            entry_count: 260,
            legacy_grammar_no: 3,
            legacy_lexicon_cgi_url: "/v1/legacy/perl/lexicon.cgi?grammar=3",
            category_counts: [
              { category: "N", count: 80 },
              { category: "V", count: 55 }
            ]
          }
        });
      }
      if (url.includes("/v1/reference/grammars/imi01/lexicon-items")) {
        return jsonResponse({
          body: {
            grammar_id: "imi01",
            category_filter: null,
            page: 1,
            page_size: 20,
            total_count: 260,
            total_pages: 13,
            items: [
              {
                lexicon_id: 60,
                entry: "John",
                phono: "ジョン",
                category: "N",
                sync_features: ["1,1"],
                idslot: "1",
                semantics: ["Name:John"],
                note: ""
              }
            ]
          }
        });
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "Lexicon内容確認" }));

    expect(await screen.findByRole("heading", { name: "7. 語彙の内容確認" })).toBeInTheDocument();
    expect(screen.getByTestId("lexicon-inspect-table")).toHaveTextContent("John");
    expect(screen.getByRole("link", { name: "lexicon.cgi 相当を開く" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "語彙を更新" })).not.toBeInTheDocument();
  });

  it("filters lexicon table by clicking category summary chip", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      if (url.includes("/v1/reference/grammars/imi01/lexicon-summary")) {
        return jsonResponse({
          body: {
            grammar_id: "imi01",
            display_name: "IMI 共同研究用・日本語文法片 01",
            source_csv: "lexicon-all.csv",
            entry_count: 260,
            legacy_grammar_no: 3,
            legacy_lexicon_cgi_url: "/v1/legacy/perl/lexicon.cgi?grammar=3",
            category_counts: [
              { category: "N", count: 80 },
              { category: "V", count: 55 }
            ]
          }
        });
      }
      if (url.includes("/v1/reference/grammars/imi01/lexicon-items") && url.includes("category=N")) {
        return jsonResponse({
          body: {
            grammar_id: "imi01",
            category_filter: "N",
            page: 1,
            page_size: 20,
            total_count: 80,
            total_pages: 4,
            items: [
              {
                lexicon_id: 60,
                entry: "John",
                phono: "ジョン",
                category: "N",
                sync_features: ["1,1"],
                idslot: "1",
                semantics: ["Name:John"],
                note: ""
              }
            ]
          }
        });
      }
      if (url.includes("/v1/reference/grammars/imi01/lexicon-items")) {
        return jsonResponse({
          body: {
            grammar_id: "imi01",
            category_filter: null,
            page: 1,
            page_size: 20,
            total_count: 260,
            total_pages: 13,
            items: [
              {
                lexicon_id: 203,
                entry: "読む",
                phono: "よむ",
                category: "V",
                sync_features: ["3,1"],
                idslot: "2",
                semantics: ["Read:__"],
                note: ""
              }
            ]
          }
        });
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "Lexicon内容確認" }));
    expect(await screen.findByTestId("lexicon-inspect-table")).toHaveTextContent("読む");

    await user.click(screen.getByRole("button", { name: "N: 80" }));

    await waitFor(() => {
      expect(screen.getByTestId("lexicon-inspect-table")).toHaveTextContent("John");
    });
    const clearButton = screen.getByRole("button", { name: "絞り込み解除（N）" });
    expect(clearButton.className).toContain("token-chip");
    expect(clearButton.className).toContain("token-chip-filter");

    await user.click(clearButton);

    await waitFor(() => {
      expect(screen.getByTestId("lexicon-inspect-table")).toHaveTextContent("読む");
    });
    expect(screen.queryByRole("button", { name: "絞り込み解除（N）" })).not.toBeInTheDocument();
    expect(fetchMock.mock.calls.some((call) => String(call[0]).includes("category=N"))).toBe(true);
  });

  it("shows reference docs without grammar rule source editor", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      if (url.includes("/v1/reference/features")) {
        return jsonResponse({
          body: [{ file_name: "feat1.txt", title: "主語一致素性" }]
        });
      }
      if (url.includes("/v1/reference/rules/imi01")) {
        return jsonResponse({
          body: [{ rule_number: 1, rule_name: "RH-Merge", file_name: "RH-Merge_03.txt" }]
        });
      }
      if (url.includes("/v1/reference/features/feat1.txt")) {
        return jsonResponse({ body: { html_text: "<p>feature</p>" } });
      }
      if (url.includes("/v1/reference/rules/doc/RH-Merge_03.txt")) {
        return jsonResponse({ body: { html_text: "<p>rule</p>" } });
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "素性とルールの確認" }));
    await user.click(screen.getByRole("button", { name: "資料参照" }));

    expect(await screen.findByRole("heading", { name: "9. 資料参照（素性資料 / 規則資料）" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "素性資料" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "規則資料" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "主語一致素性" })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "feat1.txt" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "機能ドキュメントを再読み込み" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "規則ドキュメントを再読み込み" })).not.toBeInTheDocument();
    expect(screen.queryByText("文法ルール原本の閲覧・編集")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("grammar-rule-source-editor")).not.toBeInTheDocument();
  });

  it("auto-loads grammar rules on opening grammar inspect from menu", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      if (url.includes("/v1/reference/grammars/imi01/merge-rules")) {
        return jsonResponse({
          body: [
            {
              rule_number: 1,
              rule_name: "RH-Merge",
              rule_kind: "double",
              file_name: "RH-Merge_03.pl",
              is_core_merge: true
            }
          ]
        });
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "素性とルールの確認" }));

    await waitFor(() => {
      expect(screen.getByTestId("merge-rule-table")).toHaveTextContent("RH-Merge");
    });
    expect(screen.queryByRole("button", { name: "規則一覧を更新" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "資料を閲覧" })).toBeInTheDocument();
  });

  it("loads merge rules and rule compare from Step0", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      if (url.includes("/v1/reference/grammars/imi01/merge-rules")) {
        return jsonResponse({
          body: [
            {
              rule_number: 1,
              rule_name: "RH-Merge",
              rule_kind: "double",
              file_name: "RH-Merge_03.pl",
              is_core_merge: true
            },
            {
              rule_number: 2,
              rule_name: "LH-Merge",
              rule_kind: "double",
              file_name: "LH-Merge_03.pl",
              is_core_merge: true
            }
          ]
        });
      }
      if (url.includes("/v1/reference/grammars/imi01/rule-compare/1")) {
        return jsonResponse({
          body: {
            grammar_id: "imi01",
            rule_number: 1,
            rule_name: "RH-Merge",
            perl_file_name: "RH-Merge_03.pl",
            perl_source_text: "sub RH_Merge { ... }",
            python_file_name: "execute.py",
            python_source_text: "if rule_name == \"RH-Merge\": ..."
          }
        });
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "Grammar内容確認" }));

    expect(await screen.findByTestId("merge-rule-table")).toHaveTextContent("RH-Merge");

    await user.click(screen.getAllByRole("button", { name: "移植前後を比較" })[0]);

    expect(await screen.findByRole("heading", { name: "8. 移植前後コード比較（規則単位）" })).toBeInTheDocument();
    expect(screen.getByTestId("perl-rule-source")).toHaveTextContent("RH_Merge");
    expect(screen.getByTestId("python-rule-source")).toHaveTextContent("RH-Merge");
  });

  it("toggles auto/manual token mode and updates tokens when split mode changes", async () => {
    const tokenizeCalls: Array<{ splitMode: string; sentence: string }> = [];
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      if (url.endsWith("/v1/derivation/numeration/tokenize")) {
        const payload = init?.body ? JSON.parse(String(init.body)) : {};
        const split = payload.split_mode || "C";
        const sentence = payload.sentence || "";
        tokenizeCalls.push({ splitMode: split, sentence });
        const tokens =
          sentence.includes("白いギターの箱") && split === "A"
            ? ["白", "い", "ギター", "の", "箱"]
            : sentence.includes("白いギターの箱") && split === "B"
              ? ["白い", "ギター", "の", "箱"]
              : sentence.includes("白いギターの箱") && split === "C"
                ? ["白い", "ギター", "の", "箱", "（補助）"]
                : split === "A"
                  ? ["ジョ", "ン", "が"]
                  : split === "B"
                    ? ["ジョン", "が"]
                    : ["ジョンが"];
        return jsonResponse({
          body: { tokens }
        });
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "この設定で開始" }));

    expect(screen.getByTestId("token-input-mode")).toHaveTextContent("自動");
    await user.click(screen.getByRole("button", { name: "手動" }));
    expect(screen.getByTestId("token-input-mode")).toHaveTextContent("手動");
    const sentenceInput = screen.getByRole("textbox", { name: "Sentence" });
    await user.clear(sentenceInput);
    await user.type(sentenceInput, "ジョン,が,本を");

    await waitFor(() => {
      expect(screen.getByTestId("token-chip-row")).toHaveTextContent("ジョン,が,本を");
    });

    await user.click(screen.getByTestId("token-chip-row"));
    const manualTokenEditor = await screen.findByRole("textbox", { name: "Manual Token Editor" });
    await user.clear(manualTokenEditor);
    await user.type(manualTokenEditor, "ジョ,ン,が,本を");
    await fireEvent.keyDown(manualTokenEditor, { key: "Enter" });
    await waitFor(() => {
      const tokens = Array.from(screen.getByTestId("token-chip-row").querySelectorAll("span.token-chip")).map(
        (node) => node.textContent || ""
      );
      expect(tokens).toEqual(["ジョ", "ン", "が", "本を"]);
    });

    await user.click(screen.getByRole("button", { name: "自動（Sudachi）" }));
    expect(await screen.findByTestId("token-input-mode")).toHaveTextContent("自動");
    await user.clear(sentenceInput);
    await user.type(sentenceInput, "白いギターの箱");

    const splitSelect = screen.getByLabelText("Sudachi Split Mode");
    const getTokenChips = () =>
      Array.from(screen.getByTestId("token-chip-row").querySelectorAll("span.token-chip")).map(
        (node) => node.textContent || ""
      );
    let tokensA: string[] = [];
    let tokensB: string[] = [];
    let tokensC: string[] = [];

    fireEvent.change(splitSelect, { target: { value: "C" } });
    await waitFor(() => {
      tokensC = getTokenChips();
      expect(tokensC).toEqual(["白い", "ギター", "の", "箱", "（補助）"]);
    });

    fireEvent.change(splitSelect, { target: { value: "A" } });
    await waitFor(() => {
      tokensA = getTokenChips();
      expect(tokensA).toEqual(["白", "い", "ギター", "の", "箱"]);
    });

    fireEvent.change(splitSelect, { target: { value: "B" } });
    await waitFor(() => {
      tokensB = getTokenChips();
      expect(tokensB).toEqual(["白い", "ギター", "の", "箱"]);
    });

    expect(tokensC).not.toEqual(tokensA);
    expect(tokensC).not.toEqual(tokensB);
    expect(tokensA).not.toEqual(tokensB);

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/v1/derivation/numeration/tokenize"),
      expect.objectContaining({
        method: "POST"
      })
    );
    expect(
      tokenizeCalls.some((entry) => entry.splitMode === "C" && entry.sentence === "白いギターの箱")
    ).toBe(true);
    expect(
      tokenizeCalls.some((entry) => entry.splitMode === "A" && entry.sentence === "白いギターの箱")
    ).toBe(true);
    expect(
      tokenizeCalls.some((entry) => entry.splitMode === "B" && entry.sentence === "白いギターの箱")
    ).toBe(true);
  });

  it("commits manual split tokens on blur", async () => {
    const user = userEvent.setup();
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      throw new Error(`unexpected url: ${url}`);
    });

    render(<App />);

    await user.click(await screen.findByRole("button", { name: "この設定で開始" }));
    await user.click(screen.getByRole("button", { name: "手動" }));
    const sentenceInput = await screen.findByRole("textbox", { name: "Sentence" });
    await user.clear(sentenceInput);
    await user.type(sentenceInput, "ジョン,が,本を,読んだ");

    await waitFor(() => {
      const chips = screen.getByTestId("token-chip-row").querySelectorAll("span.token-chip");
      expect(chips).toHaveLength(1);
      expect(chips[0]).toHaveTextContent("ジョン,が,本を,読んだ");
    });

    await user.click(screen.getByTestId("token-chip-row"));
    const manualTokenEditor = await screen.findByRole("textbox", { name: "Manual Token Editor" });
    await user.clear(manualTokenEditor);
    await user.type(manualTokenEditor, "ジョン,が,本を 読んだ");
    await user.click(sentenceInput);

    await waitFor(() => {
      const chips = screen.getByTestId("token-chip-row").querySelectorAll("span.token-chip");
      expect(Array.from(chips).map((node) => node.textContent)).toEqual(["ジョン", "が", "本を", "読んだ"]);
    });
  });

  it("shows lexicon reference in Lexicon build mode and updates by split result", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      if (url.endsWith("/v1/derivation/numeration/tokenize")) {
        const payload = init?.body ? JSON.parse(String(init.body)) : {};
        const split = payload.split_mode || "C";
        const tokens =
          split === "A"
            ? ["白", "い", "ギター", "の", "箱"]
            : split === "B"
              ? ["白い", "ギター", "の", "箱"]
              : ["白い", "ギター", "の", "箱", "（補助）"];
        return jsonResponse({ body: { tokens } });
      }
      if (url.endsWith("/v1/derivation/numeration/generate")) {
        const payload = init?.body ? JSON.parse(String(init.body)) : {};
        const split = payload.split_mode || "C";
        const lexiconId = split === "A" ? 201 : split === "B" ? 202 : 203;
        return jsonResponse({
          body: {
            memo: payload.sentence || "",
            lexicon_ids: [lexiconId],
            token_resolutions: [],
            numeration_text: `${payload.sentence || ""}\t${lexiconId}\n \t+\n \t1`
          }
        });
      }
      if (url.endsWith("/v1/reference/grammars/imi01/lexicon-items/by-ids")) {
        const payload = init?.body ? JSON.parse(String(init.body)) : {};
        const ids = Array.isArray(payload.ids) ? payload.ids : [];
        return jsonResponse({
          body: {
            requested_count: ids.length,
            found_count: ids.length,
            missing_ids: [],
            items: ids.map((lexiconId: number) => ({
              lexicon_id: lexiconId,
              found: true,
              entry: `ID-${lexiconId}`,
              phono: `phono-${lexiconId}`,
              category: "N",
              sync_features: [],
              idslot: "id",
              semantics: [`Sem-${lexiconId}`],
              note: ""
            }))
          }
        });
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "この設定で開始" }));
    expect(screen.getByTestId("token-input-mode")).toHaveTextContent("自動");

    const sentenceInput = await screen.findByRole("textbox", { name: "Sentence" });
    await user.clear(sentenceInput);
    await user.type(sentenceInput, "白いギターの箱");

    const buildPanel = screen.getByRole("button", { name: "Lexiconから組み立てる" }).closest("section");
    expect(buildPanel).not.toBeNull();
    expect(await within(buildPanel!).findByText("numerationの語彙情報参照")).toBeInTheDocument();

    await waitFor(() => {
      expect(within(buildPanel!).getByTestId("numeration-lexicon-table")).toHaveTextContent("Sem-203");
    });

    fireEvent.change(screen.getByLabelText("Sudachi Split Mode"), { target: { value: "A" } });
    await waitFor(() => {
      expect(within(buildPanel!).getByTestId("numeration-lexicon-table")).toHaveTextContent("Sem-201");
    });
  });

  it("allows replacing a multi-candidate lexicon item in Step1 numeration reference", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      if (url.endsWith("/v1/derivation/numeration/tokenize")) {
        return jsonResponse({ body: { tokens: ["うさぎ", "が", "いる", "る"] } });
      }
      if (url.endsWith("/v1/derivation/numeration/generate")) {
        const payload = init?.body ? JSON.parse(String(init.body)) : {};
        return jsonResponse({
          body: {
            memo: payload.sentence || "うさぎがいる",
            lexicon_ids: [270, 19, 271, 204],
            token_resolutions: [
              { token: "うさぎ", lexicon_id: 270, candidate_lexicon_ids: [270] },
              { token: "が", lexicon_id: 19, candidate_lexicon_ids: [19, 183] },
              { token: "いる", lexicon_id: 271, candidate_lexicon_ids: [271] },
              { token: "る", lexicon_id: 204, candidate_lexicon_ids: [204, 308] }
            ],
            numeration_text: `${payload.sentence || "うさぎがいる"}\t270\t19\t271\t204\n \t\t\t\t\n \t1\t2\t3\t4`
          }
        });
      }
      if (url.endsWith("/v1/derivation/numeration/compose")) {
        const payload = init?.body ? JSON.parse(String(init.body)) : {};
        const ids = Array.isArray(payload.lexicon_ids) ? payload.lexicon_ids : [];
        return jsonResponse({
          body: {
            numeration_text:
              `${payload.memo || "うさぎがいる"}\t${ids.join("\t")}\n` +
              ` \t${Array.from({ length: ids.length }, () => "").join("\t")}\n` +
              ` \t${ids.map((_: unknown, i: number) => String(i + 1)).join("\t")}`
          }
        });
      }
      if (url.endsWith("/v1/reference/grammars/imi01/lexicon-items/by-ids")) {
        const payload = init?.body ? JSON.parse(String(init.body)) : {};
        const ids = Array.isArray(payload.ids) ? payload.ids : [];
        return jsonResponse({
          body: {
            grammar_id: "imi01",
            requested_count: ids.length,
            found_count: ids.length,
            missing_ids: [],
            items: ids.map((lexiconId: number) => ({
              lexicon_id: lexiconId,
              found: true,
              entry: `ID-${lexiconId}`,
              phono: `phono-${lexiconId}`,
              category: lexiconId === 204 || lexiconId === 308 ? "T" : "N",
              sync_features: lexiconId === 308 ? ["0,17,N,,,right,nonhead"] : [],
              idslot: "id",
              semantics: [`Sem-${lexiconId}`],
              note: ""
            }))
          }
        });
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "この設定で開始" }));
    const sentenceInput = await screen.findByRole("textbox", { name: "Sentence" });
    await user.clear(sentenceInput);
    await user.type(sentenceInput, "うさぎがいる");

    const buildPanel = screen.getByRole("button", { name: "Lexiconから組み立てる" }).closest("section");
    expect(buildPanel).not.toBeNull();

    await waitFor(() => {
      expect(within(buildPanel!).getByTestId("numeration-lexicon-table")).toHaveTextContent("Sem-204");
    });

    await user.click(await within(buildPanel!).findByTestId("step1-candidate-toggle-4"));
    const candidatePanel = await within(buildPanel!).findByTestId("step1-candidate-panel-4");
    expect(candidatePanel).toHaveTextContent("ID 308");
    expect(candidatePanel).toHaveTextContent("+N(right)(nonhead)");
    await user.click(within(candidatePanel).getByRole("button", { name: "この候補に差し替え" }));

    await waitFor(() => {
      expect(within(buildPanel!).getByTestId("numeration-lexicon-table")).toHaveTextContent("Sem-308");
    });
  });

  it("allows replacing a multi-candidate lexicon item in Step2 target panel", async () => {
    const initRequests: string[] = [];
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      if (url.endsWith("/v1/derivation/numeration/tokenize")) {
        return jsonResponse({ body: { tokens: ["うさぎ", "が", "いる", "る"] } });
      }
      if (url.endsWith("/v1/derivation/numeration/generate")) {
        const payload = init?.body ? JSON.parse(String(init.body)) : {};
        return jsonResponse({
          body: {
            memo: payload.sentence || "うさぎがいる",
            lexicon_ids: [270, 19, 271, 204],
            token_resolutions: [
              { token: "うさぎ", lexicon_id: 270, candidate_lexicon_ids: [270] },
              { token: "が", lexicon_id: 19, candidate_lexicon_ids: [19, 183] },
              { token: "いる", lexicon_id: 271, candidate_lexicon_ids: [271] },
              { token: "る", lexicon_id: 204, candidate_lexicon_ids: [204, 308] }
            ],
            numeration_text: `${payload.sentence || "うさぎがいる"}\t270\t19\t271\t204\n \t\t\t\t\n \t1\t2\t3\t4`
          }
        });
      }
      if (url.endsWith("/v1/derivation/numeration/compose")) {
        const payload = init?.body ? JSON.parse(String(init.body)) : {};
        const ids = Array.isArray(payload.lexicon_ids) ? payload.lexicon_ids : [];
        return jsonResponse({
          body: {
            numeration_text:
              `${payload.memo || "うさぎがいる"}\t${ids.join("\t")}\n` +
              ` \t${Array.from({ length: ids.length }, () => "").join("\t")}\n` +
              ` \t${ids.map((_: unknown, i: number) => String(i + 1)).join("\t")}`
          }
        });
      }
      if (url.endsWith("/v1/reference/grammars/imi01/lexicon-items/by-ids")) {
        const payload = init?.body ? JSON.parse(String(init.body)) : {};
        const ids = Array.isArray(payload.ids) ? payload.ids : [];
        return jsonResponse({
          body: {
            grammar_id: "imi01",
            requested_count: ids.length,
            found_count: ids.length,
            missing_ids: [],
            items: ids.map((lexiconId: number) => ({
              lexicon_id: lexiconId,
              found: true,
              entry: `ID-${lexiconId}`,
              phono: `phono-${lexiconId}`,
              category: lexiconId === 204 || lexiconId === 308 ? "T" : "N",
              sync_features: lexiconId === 308 ? ["0,17,N,,,right,nonhead"] : [],
              idslot: "id",
              semantics: [`Sem-${lexiconId}`],
              note: ""
            }))
          }
        });
      }
      if (url.endsWith("/v1/derivation/init")) {
        const payload = init?.body ? JSON.parse(String(init.body)) : {};
        const numerationText = String(payload.numeration_text || "");
        initRequests.push(numerationText);
        const ids = numerationText
          .split("\n")[0]
          .split("\t")
          .slice(1)
          .map((value) => Number.parseInt(value, 10))
          .filter((value) => Number.isInteger(value) && value > 0);
        const tenseLexiconId = ids[3] ?? 204;
        return jsonResponse({
          body: {
            grammar_id: "imi01",
            memo: "うさぎがいる",
            newnum: 5,
            basenum: 4,
            history: "",
            base: [
              null,
              ["x1-1", "N", [], [], "x1-1", ["Sem-270"], "うさぎ", ["zero", "zero"]],
              ["x2-1", "J", [], ["0,17,N,,,right,nonhead"], "zero", ["Sem-19"], "が", ["zero", "zero"]],
              ["x3-1", "V", [], [], "x3-1", ["Sem-271"], "いる", ["zero", "zero"]],
              ["x4-1", "T", [], ["0,17,V,,,right,nonhead"], "0,24", [`Sem-${tenseLexiconId}`], "る", ["zero", "zero"]]
            ]
          }
        });
      }
      if (url.endsWith("/v1/derivation/candidates")) {
        return jsonResponse({ body: [] });
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "この設定で開始" }));
    const sentenceInput = await screen.findByRole("textbox", { name: "Sentence" });
    await user.clear(sentenceInput);
    await user.type(sentenceInput, "うさぎがいる");
    await user.click(screen.getByRole("button", { name: "Numerationを形成" }));

    expect(await screen.findByRole("heading", { name: "【Step.2】Grammarの適用" })).toBeInTheDocument();
    const selectionList = await screen.findByTestId("step2-selection-list");
    expect(selectionList).toHaveTextContent("Sem-204");

    await user.click(await within(selectionList).findByTestId("step2-candidate-toggle-4"));
    const panel = await within(selectionList).findByTestId("step2-candidate-panel-4");
    expect(panel).toHaveTextContent("ID 308");
    await user.click(within(panel).getByRole("button", { name: "この候補に差し替え" }));

    await waitFor(() => {
      expect(screen.getByTestId("step2-selection-list")).toHaveTextContent("Sem-308");
      expect(initRequests.some((text) => text.includes("\t308"))).toBe(true);
    });
  });

  it("shows lexicon information table for .num text", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      if (url.includes("/v1/reference/grammars/imi01/lexicon-items/by-ids")) {
        return jsonResponse({
          body: {
            grammar_id: "imi01",
            requested_count: 3,
            found_count: 2,
            missing_ids: [9999],
            items: [
              {
                lexicon_id: 60,
                found: true,
                entry: "John",
                phono: "ジョン",
                category: "N",
                sync_features: [],
                idslot: "id",
                semantics: ["Name:John"],
                note: ""
              },
              {
                lexicon_id: 309,
                found: true,
                entry: "φ",
                phono: "phi",
                category: "J",
                sync_features: ["0,17,N,,,right,nonhead", "3,17,V,,,left,nonhead", "4,11,ga"],
                idslot: "zero",
                semantics: [],
                note: ""
              },
              {
                lexicon_id: 9999,
                found: false,
                entry: "",
                phono: "",
                category: "",
                sync_features: [],
                idslot: "",
                semantics: [],
                note: ""
              }
            ]
          }
        });
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "numファイルを選ぶ" }));
    await user.type(
      screen.getByLabelText("Step1 Upload Numeration"),
      "memo\t60\t309\t9999\n\t+\t+\t+\n\t1\t2\t3"
    );

    const uploadPanel = screen.getByRole("button", { name: "numファイルをアップロード" }).closest("section");
    expect(uploadPanel).not.toBeNull();
    const numerationLexiconHeadings = await within(uploadPanel!).findAllByText("numerationの語彙情報参照");
    expect(numerationLexiconHeadings.length).toBe(1);
    const lexiconTable = await within(uploadPanel!).findByTestId("numeration-lexicon-table");
    expect(lexiconTable).toHaveTextContent("x1-1");
    expect(lexiconTable).toHaveTextContent("Name: John");
    expect(lexiconTable).toHaveTextContent("ジョン");
    expect(lexiconTable).toHaveTextContent("+N(right)(nonhead)");
    expect(lexiconTable).toHaveTextContent("+V(left)(nonhead)");
    expect(lexiconTable).toHaveTextContent("ga(★)");
    expect(await within(uploadPanel!).findByText("語彙ID 9999 は辞書にありません")).toBeInTheDocument();
    expect(await within(uploadPanel!).findByText("語彙ID が見つかりませんでした: 9999")).toBeInTheDocument();
  });
});
