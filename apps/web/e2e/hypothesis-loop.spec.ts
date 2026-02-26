import { expect, test } from "@playwright/test";

test("hypothesis loop via sentence input and observation", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Hypothesis Loop Workbench" })).toBeVisible();

  await page.getByLabel("Manual Tokens").fill("ジョン が 本 を 読む -ta");
  await page.getByRole("button", { name: ".num を生成（T0は作らない）" }).click();
  await expect(page.getByTestId("numeration-text")).not.toContainText("(未生成)");
  await page.getByRole("button", { name: "文から T0 を初期化（.num 生成あり）" }).click();

  await expect(page.getByText(/basenum\/newnum:/)).toContainText(/\d+\/\d+/);

  await page.getByRole("button", { name: "Step 3 Target/Rule" }).click();
  await page.getByLabel("left").fill("1");
  await page.getByLabel("right").fill("2");
  await page.getByRole("button", { name: "Load Candidates" }).click();

  const executeButton = page.getByRole("button", { name: "Execute" }).first();
  await expect(executeButton).toBeVisible();
  await executeButton.click();

  await expect(page.getByTestId("current-history")).toContainText("Merge");

  await page.getByRole("button", { name: "Step 4 観察" }).click();
  await page.getByRole("button", { name: /^tree$/ }).click();
  await page.getByRole("button", { name: /^tree_cat$/ }).click();
  await page.getByRole("button", { name: "lf" }).click();
  await page.getByRole("button", { name: "sr" }).click();

  await expect(page.getByTestId("tree-output")).not.toHaveText("", { timeout: 30000 });
  await expect(page.getByTestId("tree-cat-output")).not.toHaveText("", { timeout: 30000 });
  await expect(page.getByTestId("lf-output")).not.toHaveText("", { timeout: 30000 });
  await expect(page.getByTestId("sr-output")).not.toHaveText("", { timeout: 30000 });

  await page.getByRole("button", { name: "Step 5 保存/再開" }).click();
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

  await page.getByLabel("Manual Tokens").fill("ジョン が 本 を 読む -ta");
  await page.getByRole("button", { name: "文から T0 を初期化（.num 生成あり）" }).click();
  await expect(page.getByTestId("current-history")).toContainText("(empty)");

  await page.getByRole("button", { name: "Step 5 保存/再開" }).click();
  await page.getByRole("button", { name: "Save T0" }).click();

  await page.getByRole("button", { name: "Step 3 Target/Rule" }).click();
  await page.getByLabel("left").fill("5");
  await page.getByLabel("right").fill("6");
  await page.getByRole("button", { name: "Load Candidates" }).click();
  await page.getByRole("button", { name: "Execute" }).first().click();
  await expect(page.getByTestId("current-history")).toContainText("Merge");

  await page.getByRole("button", { name: "Step 5 保存/再開" }).click();
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

  await page.getByRole("button", { name: "Step 4 観察" }).click();
  const treeOutput = page.getByTestId("tree-output");
  await page.getByRole("button", { name: /^tree$/ }).click();
  await expect(treeOutput).not.toHaveText("", { timeout: 30000 });
  const treeBeforeResume = await treeOutput.textContent();
  expect(treeBeforeResume).toBeTruthy();

  await page.getByRole("button", { name: "Step 5 保存/再開" }).click();
  await page.getByRole("button", { name: "Export resume" }).click();
  await expect(page.getByLabel("resume-text")).not.toHaveValue("");
  await page.getByRole("button", { name: "Import resume" }).click();
  await page.getByRole("button", { name: "Step 4 観察" }).click();
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
