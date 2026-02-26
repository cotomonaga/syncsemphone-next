import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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
    display_name: "imi01"
  },
  {
    grammar_id: "imi02",
    folder: "imi02",
    uses_lexicon_all: true,
    display_name: "imi02"
  },
  {
    grammar_id: "imi03",
    folder: "imi03",
    uses_lexicon_all: true,
    display_name: "imi03"
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
  return null;
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("App", () => {
  it("generates numeration and initializes T0 from sentence", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(async (input) => {
        const url = String(input);
        const common = maybeCommonResponse(url);
        if (common) {
          return common;
        }
        if (url.endsWith("/v1/derivation/init/from-sentence")) {
          return jsonResponse({
            body: {
              numeration: {
                memo: "manual",
                lexicon_ids: [60, 19, 23, 203, 52],
                token_resolutions: [
                  { token: "ジョン", lexicon_id: 60, candidate_lexicon_ids: [60] },
                  { token: "が", lexicon_id: 19, candidate_lexicon_ids: [19] }
                ],
                numeration_text: "synthetic\t60\t19\t23\t203\t52\n\t\t\t\t\n\t1\t2\t3\t4\t5"
              },
              state: {
                grammar_id: "imi03",
                memo: "synthetic",
                newnum: 5,
                basenum: 5,
                history: "",
                base: [null, [1], [2], [3], [4], [5]]
              }
            }
          });
        }
        if (url.endsWith("/v1/derivation/numeration/generate")) {
          return jsonResponse({
            body: {
              memo: "manual",
              lexicon_ids: [60, 19],
              token_resolutions: [
                { token: "ジョン", lexicon_id: 60, candidate_lexicon_ids: [60] },
                { token: "が", lexicon_id: 19, candidate_lexicon_ids: [19] }
              ],
              numeration_text: "synthetic\t60\t19\n\t\t\n\t1\t2"
            }
          });
        }
        throw new Error(`unexpected url: ${url}`);
      });

    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: ".num を生成（T0は作らない）" }));
    expect(await screen.findByTestId("numeration-text")).toHaveTextContent("synthetic");

    await user.click(screen.getByRole("button", { name: "文から T0 を初期化（.num 生成あり）" }));
    expect(await screen.findByText(/basenum\/newnum: 5\/5/)).toBeInTheDocument();

    expect(fetchMock).toHaveBeenCalled();
  });

  it("runs candidate execute and observation loop", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(async (input) => {
        const url = String(input);
        const common = maybeCommonResponse(url);
        if (common) {
          return common;
        }
        if (url.endsWith("/v1/derivation/init/from-sentence")) {
          return jsonResponse({
            body: {
              numeration: {
                memo: "manual",
                lexicon_ids: [60, 19],
                token_resolutions: [],
                numeration_text: "synthetic\t60\t19\n\t\t\n\t1\t2"
              },
              state: {
                grammar_id: "imi03",
                memo: "synthetic",
                newnum: 2,
                basenum: 2,
                history: "",
                base: [null, [1], [2]]
              }
            }
          });
        }
        if (url.endsWith("/v1/derivation/candidates")) {
          return jsonResponse({
            body: [
              {
                rule_number: 1,
                rule_name: "RH-Merge",
                rule_kind: "double",
                left: 1,
                right: 2,
                check: null
              }
            ]
          });
        }
        if (url.endsWith("/v1/derivation/execute")) {
          return jsonResponse({
            body: {
              grammar_id: "imi03",
              memo: "synthetic",
              newnum: 3,
              basenum: 3,
              history: "([1 2] RH-Merge) ",
              base: [null, [1], [2], [3]]
            }
          });
        }
        if (url.endsWith("/v1/observation/tree")) {
          return jsonResponse({
            body: {
              mode: "tree",
              csv_lines: ["id,label", "1,Node"],
              csv_text: "id,label\n1,Node"
            }
          });
        }
        if (url.endsWith("/v1/semantics/lf")) {
          return jsonResponse({
            body: {
              list_representation: [
                {
                  lexical_id: "1",
                  category: "N",
                  idslot: "1",
                  semantics: ["Name:ジョン"],
                  predication: []
                }
              ],
              unresolved_feature_like_token: false
            }
          });
        }
        if (url.endsWith("/v1/semantics/sr")) {
          return jsonResponse({
            body: {
              truth_conditional_meaning: [
                {
                  object_id: 1,
                  layer: 1,
                  kind: "object",
                  properties: ["John"]
                }
              ]
            }
          });
        }
        if (url.endsWith("/v1/derivation/resume/export")) {
          return jsonResponse({
            body: {
              resume_text: "line1\nline2"
            }
          });
        }
        if (url.endsWith("/v1/derivation/resume/import")) {
          return jsonResponse({
            body: {
              grammar_id: "imi03",
              memo: "synthetic",
              newnum: 3,
              basenum: 3,
              history: "([1 2] RH-Merge) ",
              base: [null, [1], [2], [3]]
            }
          });
        }
        throw new Error(`unexpected url: ${url}`);
      });

    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: "文から T0 を初期化（.num 生成あり）" }));
    await user.click(screen.getByRole("button", { name: "Load Candidates" }));
    await user.click(await screen.findByRole("button", { name: "Execute" }));

    expect(await screen.findByText(/RH-Merge/)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "tree" }));
    await user.click(screen.getByRole("button", { name: "lf" }));
    await user.click(screen.getByRole("button", { name: "sr" }));

    expect(await screen.findByTestId("tree-output")).toHaveTextContent("id,label");
    expect(await screen.findByTestId("lf-output")).toHaveTextContent("Name:ジョン");
    expect(await screen.findByTestId("sr-output")).toHaveTextContent("1-1-object");

    await user.click(screen.getByRole("button", { name: "Export resume" }));
    await user.click(screen.getByRole("button", { name: "Import resume" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalled();
    });
  });

  it("deduplicates grammar label when display_name equals grammar_id", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/v1/derivation/grammars")) {
        return jsonResponse({
          body: [
            {
              grammar_id: "imi03",
              folder: "imi03",
              uses_lexicon_all: true,
              display_name: "imi03"
            }
          ]
        });
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: "文法一覧を更新" }));

    const grammarSelect = screen.getByLabelText("Grammar") as HTMLSelectElement;
    expect(grammarSelect.options[0].textContent).toBe("imi03");
  });

  it("toggles manual/auto token mode and updates tokens when split mode changes", async () => {
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

    expect(screen.getByTestId("token-input-mode")).toHaveTextContent("手動");
    expect(screen.getByLabelText("Manual Tokens")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "自動（Sudachi）" }));

    expect(await screen.findByTestId("token-input-mode")).toHaveTextContent("自動");
    expect(screen.queryByLabelText("Manual Tokens")).not.toBeInTheDocument();

    const splitSelect = screen.getByLabelText("Sudachi Split Mode");
    fireEvent.change(splitSelect, { target: { value: "A" } });

    await waitFor(() => {
      expect(screen.getByTestId("token-chip-row")).toHaveTextContent("ジョ");
      expect(screen.getByTestId("token-chip-row")).toHaveTextContent("ン");
    });
  });

  it("shows step1 help popover on question icon click", async () => {
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

    await user.click(screen.getByRole("button", { name: ".num を生成の説明" }));
    expect(
      await screen.findByText("観察文を分割して語彙候補を解決し、.num テキストだけを更新します。T0 はまだ作りません。")
    ).toBeInTheDocument();
  });

  it("shows brief T0 description in step1", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      throw new Error(`unexpected url: ${url}`);
    });

    render(<App />);

    expect(
      await screen.findByText(
        "T0 は規則適用前の最初の派生状態です。Step3 の候補探索や規則実行は、この T0 を起点に進みます。"
      )
    ).toBeInTheDocument();
  });

  it("renders isolated Perl legacy iframe in legacy mode", async () => {
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

    await user.click(screen.getByRole("button", { name: "Legacy UI" }));
    const frame = await screen.findByTitle("legacy-perl-ui");
    expect(frame).toBeInTheDocument();
    expect(frame).toHaveAttribute("src");
    expect(frame.getAttribute("src")).toContain("/v1/legacy/perl/index-IMI.cgi");
  });

  it("opens grammar editor and auto-loads first rule source", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      if (url.includes("/v1/reference/features/plain-category.html")) {
        return jsonResponse({
          body: { file_name: "plain-category.html", html_text: "<html><body>feature</body></html>" }
        });
      }
      if (url.includes("/v1/reference/features")) {
        return jsonResponse({
          body: [{ file_name: "plain-category.html" }]
        });
      }
      if (url.includes("/v1/reference/rules/doc/RH-Merge_03.html")) {
        return jsonResponse({
          body: { file_name: "RH-Merge_03.html", html_text: "<html><body>rule</body></html>" }
        });
      }
      if (url.includes("/v1/reference/rules/imi03")) {
        return jsonResponse({
          body: [{ rule_number: 1, rule_name: "RH-Merge", file_name: "RH-Merge_03.html" }]
        });
      }
      if (url.includes("/v1/reference/grammars/imi03/rule-sources/1")) {
        return jsonResponse({
          body: {
            grammar_id: "imi03",
            rule_number: 1,
            rule_name: "RH-Merge",
            file_name: "RH-Merge_03.pl",
            source_text: "sub rule { return 1; }\n"
          }
        });
      }
      if (url.includes("/v1/reference/grammars/imi03/rule-sources")) {
        return jsonResponse({
          body: [
            {
              rule_number: 1,
              rule_name: "RH-Merge",
              file_name: "RH-Merge_03.pl",
              exists: true
            }
          ]
        });
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: "文法定義を閲覧・編集" }));

    expect(await screen.findByText("ルール一覧を読み込みました（1件）")).toBeInTheDocument();
    expect(await screen.findByLabelText("grammar-rule-source-editor")).toHaveValue(
      "sub rule { return 1; }\n"
    );
    expect(await screen.findByTestId("grammar-rule-source-meta")).toHaveTextContent("1:RH-Merge");
  });

  it("loads lexicon viewer output", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      if (url.includes("/v1/lexicon/imi03?format=yaml")) {
        return jsonResponse({
          body: {
            grammar_id: "imi03",
            format: "yaml",
            lexicon_path: "/tmp/lexicon-all.csv",
            entry_count: 3,
            content_text: "meta:\\n  grammar_id: \\\"imi03\\\"\\nentries:\\n  - no: 1"
          }
        });
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: "Load Lexicon" }));

    expect(await screen.findByText(/entries: 3/)).toBeInTheDocument();
    expect(await screen.findByTestId("lexicon-output")).toHaveTextContent("grammar_id");
  });

  it("validates and imports lexicon yaml", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      const common = maybeCommonResponse(url);
      if (common) {
        return common;
      }
      const method = init?.method || "GET";
      if (url.includes("/v1/lexicon/imi03/validate") && method === "POST") {
        return jsonResponse({
          body: {
            grammar_id: "imi03",
            valid: true,
            entry_count: 1,
            errors: [],
            normalized_yaml_text: "meta:\\n  grammar_id: \\\"imi03\\\"",
            preview_csv_text: "1\\tx\\tx\\tN\\t0\\t\\t\\t\\t0\\t\\t\\t\\t\\t\\tid\\t0\\t\\t\\t\\t\\t\\t\\t\\t\\t\\t\\t\\t\\t\\t0"
          }
        });
      }
      if (url.includes("/v1/lexicon/imi03/import") && method === "POST") {
        return jsonResponse({
          body: {
            grammar_id: "imi03",
            entry_count: 1,
            normalized_yaml_text: "meta:\\n  grammar_id: \\\"imi03\\\"",
            csv_text: "1\\tx\\tx\\tN"
          }
        });
      }
      if (url.includes("/v1/lexicon/imi03/commit") && method === "POST") {
        return jsonResponse({
          body: {
            grammar_id: "imi03",
            committed: true,
            rolled_back: false,
            compatibility_passed: true,
            run_compatibility_tests: true,
            entry_count: 1,
            lexicon_path: "/tmp/lexicon-all.csv",
            backup_path: "/tmp/lexicon-all.csv.bak.1",
            message: "Committed lexicon YAML to CSV successfully",
            errors: [],
            normalized_yaml_text: "meta:\\n  grammar_id: \\\"imi03\\\"",
            committed_csv_text: "1\\tx\\tx\\tN",
            command: "pytest ...",
            stdout: "ok",
            stderr: ""
          }
        });
      }
      throw new Error(`unexpected url: ${url}`);
    });

    const user = userEvent.setup();
    render(<App />);

    fireEvent.change(screen.getByLabelText("Lexicon YAML Input"), {
      target: { value: "entries: []" }
    });
    await user.click(screen.getByRole("button", { name: "Validate YAML" }));
    expect(await screen.findByTestId("lexicon-csv-preview")).toHaveTextContent("1\\tx\\tx\\tN");

    await user.click(screen.getByRole("button", { name: "Import YAML" }));
    expect(await screen.findByTestId("lexicon-output")).toHaveTextContent("grammar_id");

    await user.click(screen.getByRole("button", { name: "Commit YAML" }));
    expect(await screen.findByTestId("lexicon-commit-message")).toHaveTextContent(
      "Committed lexicon YAML to CSV successfully"
    );
  });
});
