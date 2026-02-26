import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 120000,
  retries: 0,
  use: {
    baseURL: "http://127.0.0.1:5173",
    trace: "retain-on-failure"
  },
  webServer: [
    {
      command:
        "PYTHONPATH=../../packages/domain/src:../../apps/api python3 -m uvicorn app.main:app --app-dir ../../apps/api --host 127.0.0.1 --port 8000",
      url: "http://127.0.0.1:8000/v1/healthz",
      reuseExistingServer: true,
      timeout: 120000
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5173",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: true,
      timeout: 120000
    }
  ]
});
