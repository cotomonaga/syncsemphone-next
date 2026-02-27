import { expect, test, type Page } from "@playwright/test";

async function expectRenewedLayoutHealthy(page: Page) {
  await expect(page.locator(".page")).toBeVisible();
  const metrics = await page.evaluate(() => {
    const pageEl = document.querySelector(".page");
    const pageRect = pageEl?.getBoundingClientRect();
    return {
      viewportWidth: window.innerWidth,
      pageWidth: pageRect?.width ?? 0,
      overflowX: document.documentElement.scrollWidth - window.innerWidth
    };
  });
  expect(metrics.pageWidth).toBeGreaterThanOrEqual(metrics.viewportWidth - 80);
  expect(metrics.overflowX).toBeLessThanOrEqual(1);
}

async function expectStep1LayoutHealthy(page: Page) {
  await expect(page.getByRole("heading", { name: "【Step.1】Numerationの形成" })).toBeVisible();
  await expect(page.getByRole("textbox", { name: "Sentence" })).toBeVisible();
  await expect(page.getByLabel("Sudachi Split Mode")).toBeVisible();
  await expect(page.getByTestId("token-chip-row")).toBeVisible();
  const panelMetrics = await page.evaluate(() => {
    const panel = document.querySelector("[data-panel='sentence']");
    const rect = panel?.getBoundingClientRect();
    return {
      viewportWidth: window.innerWidth,
      panelWidth: rect?.width ?? 0
    };
  });
  expect(panelMetrics.panelWidth).toBeGreaterThan(panelMetrics.viewportWidth * 0.55);
}

test("hypothesis loop via sentence input and observation", async ({ page }) => {
  await page.goto("/");
  await expectRenewedLayoutHealthy(page);

  await expect(page.getByRole("heading", { name: "SYNCSEMPHONE NEXT" })).toBeVisible();
  await page.getByRole("button", { name: "この設定で開始" }).click();
  await expectStep1LayoutHealthy(page);

  await page.getByRole("textbox", { name: "Sentence" }).fill("ジョンがメアリを追いかけた");
  await page.getByRole("button", { name: "Numerationを形成" }).click();
  await expect(page.getByTestId("numeration-text")).not.toContainText("(未生成)");
  await expect(page.getByRole("heading", { name: "【Step.2】Grammarの適用" })).toBeVisible();

  await expect(page.getByText(/basenum\/newnum:/)).toContainText(/\d+\/\d+/);

  const firstRuleRow = page.locator("[data-testid='candidate-table'] tbody tr").first();
  const executeButton = firstRuleRow.getByRole("button", { name: "実行" });
  await expect(executeButton).toBeEnabled({ timeout: 30000 });
  await executeButton.click();

  await expect(page.getByTestId("current-history")).toContainText("Merge");

  await page.getByRole("button", { name: "【Step.3】観察" }).click();
  await expectRenewedLayoutHealthy(page);
  await page.getByRole("button", { name: /^tree$/ }).click();
  await page.getByRole("button", { name: /^tree_cat$/ }).click();
  await page.getByRole("button", { name: "lf" }).click();
  await page.getByRole("button", { name: "sr" }).click();

  await expect(page.getByTestId("tree-output")).not.toHaveText("", { timeout: 30000 });
  await expect(page.getByTestId("tree-cat-output")).not.toHaveText("", { timeout: 30000 });
  await expect(page.getByTestId("lf-output")).not.toHaveText("", { timeout: 30000 });
  await expect(page.getByTestId("sr-output")).not.toHaveText("", { timeout: 30000 });

  await page.getByRole("button", { name: "【Step.4】保存/再開" }).click();
  await page.getByRole("button", { name: "Export resume" }).click();
  await expect(page.getByLabel("resume-text")).not.toHaveValue("");

  await page.getByRole("button", { name: "Import resume" }).click();
  await expect(page.getByTestId("current-history")).toContainText("Merge");

  await page.getByRole("button", { name: "Save A" }).click();
  await page.getByRole("button", { name: "Save B" }).click();
  await page.getByRole("button", { name: "Load A" }).click();
  await expect(page.getByText(/A history:/)).toContainText("Merge");
});

test("snapshot and resume consistency for observation loop", async ({ page }) => {
  await page.goto("/");
  await expectRenewedLayoutHealthy(page);
  await page.getByRole("button", { name: "この設定で開始" }).click();
  await expectStep1LayoutHealthy(page);

  await page.getByRole("textbox", { name: "Sentence" }).fill("ジョンがメアリを追いかけた");
  await page.getByRole("button", { name: "Numerationを形成" }).click();
  await expect(page.getByRole("heading", { name: "【Step.2】Grammarの適用" })).toBeVisible();
  await expect(page.getByTestId("current-history")).toContainText("(empty)");

  await page.getByRole("button", { name: "【Step.4】保存/再開" }).click();
  await page.getByRole("button", { name: "Save T0" }).click();

  await page.getByRole("button", { name: "【Step.2】Grammarの適用" }).click();
  const firstRuleRow = page.locator("[data-testid='candidate-table'] tbody tr").first();
  const executeButton = firstRuleRow.getByRole("button", { name: "実行" });
  await expect(executeButton).toBeEnabled({ timeout: 30000 });
  await executeButton.click();
  await expect(page.getByTestId("current-history")).toContainText("Merge");

  await page.getByRole("button", { name: "【Step.4】保存/再開" }).click();
  await page.getByRole("button", { name: "Save T1" }).click();
  await page.getByRole("button", { name: "Save T2" }).click();

  await page.getByRole("button", { name: "Load T0" }).click();
  await expect(page.getByTestId("current-history")).toContainText("(empty)");
  await page.getByRole("button", { name: "Save A" }).click();

  await page.getByRole("button", { name: "Load T1" }).click();
  await expect(page.getByTestId("current-history")).toContainText("Merge");
  await page.getByRole("button", { name: "Save B" }).click();
  await expect(page.getByText(/A history:/)).toContainText("B history:");
  await expect(page.getByText(/A history:/)).toContainText("Merge");

  await page.getByRole("button", { name: "【Step.3】観察" }).click();
  await expectRenewedLayoutHealthy(page);
  const treeOutput = page.getByTestId("tree-output");
  await page.getByRole("button", { name: /^tree$/ }).click();
  await expect(treeOutput).not.toHaveText("", { timeout: 30000 });
  const treeBeforeResume = await treeOutput.textContent();
  expect(treeBeforeResume).toBeTruthy();

  await page.getByRole("button", { name: "【Step.4】保存/再開" }).click();
  await page.getByRole("button", { name: "Export resume" }).click();
  await expect(page.getByLabel("resume-text")).not.toHaveValue("");
  await page.getByRole("button", { name: "Import resume" }).click();
  await page.getByRole("button", { name: "【Step.3】観察" }).click();
  await page.getByRole("button", { name: /^tree$/ }).click();
  await expect(treeOutput).not.toHaveText("", { timeout: 30000 });
  const treeAfterResume = await treeOutput.textContent();
  const normalizedBefore = (treeBeforeResume ?? "").replace(/\s+/g, " ").trim();
  const normalizedAfter = (treeAfterResume ?? "").replace(/\s+/g, " ").trim();
  expect(normalizedAfter).toBe(normalizedBefore);

  await page.getByRole("button", { name: /^tree_cat$/ }).click();
  await page.getByRole("button", { name: "lf" }).click();
  await page.getByRole("button", { name: "sr" }).click();
  await expect(page.getByTestId("tree-cat-output")).not.toHaveText("", { timeout: 30000 });
  await expect(page.getByTestId("lf-output")).not.toHaveText("", { timeout: 30000 });
  await expect(page.getByTestId("sr-output")).not.toHaveText("", { timeout: 30000 });
});
