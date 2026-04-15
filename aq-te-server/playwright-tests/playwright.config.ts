import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 60000,
  retries: 0,

  // Start/stop Docker container automatically
  globalSetup: "./global-setup.ts",
  globalTeardown: "./global-teardown.ts",

  projects: [
    {
      name: "ibm-3270",
      testMatch: "**/*.spec.ts",
    },
  ],
});
