/**
 * Playwright fixture that manages the TE Server Docker container lifecycle.
 *
 * - Before all tests: starts the Docker container
 * - After all tests: stops and removes the container
 * - Provides a `te` client instance to each test
 */
import { test as base } from "@playwright/test";
import { TEClient } from "./te-client";
import { execSync } from "child_process";
import path from "path";

const TE_SERVER_PORT = 9995;
const TE_SERVER_URL = `http://localhost:${TE_SERVER_PORT}`;
const DOCKER_DIR = path.resolve(__dirname, "../../docker-te-server");

/**
 * Wait for the TE server to be ready (accepting requests).
 */
async function waitForServer(
  url: string,
  timeoutMs: number = 30000
): Promise<void> {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const resp = await fetch(`${url}/te/ping`, {
        signal: AbortSignal.timeout(2000),
      });
      const data = await resp.json();
      if (data?.data?.pingstatus === "ok") {
        console.log("TE Server is ready!");
        return;
      }
    } catch {
      // Server not ready yet
    }
    await new Promise((r) => setTimeout(r, 1000));
  }
  throw new Error(`TE Server did not start within ${timeoutMs}ms`);
}

/**
 * Start the Docker container.
 */
function startContainer(): void {
  console.log("Starting TE Server Docker container...");
  execSync("docker compose up --build -d", {
    cwd: DOCKER_DIR,
    stdio: "inherit",
  });
}

/**
 * Stop and remove the Docker container.
 */
function stopContainer(): void {
  console.log("Stopping TE Server Docker container...");
  execSync("docker compose down", {
    cwd: DOCKER_DIR,
    stdio: "inherit",
  });
}

// ---------------------------------------------------------------------------
// Playwright fixture
// ---------------------------------------------------------------------------

type TEFixtures = {
  te: TEClient;
};

export const test = base.extend<TEFixtures>({
  te: async ({}, use) => {
    const client = new TEClient({
      baseUrl: TE_SERVER_URL,
      sessionName: "default",
    });
    await use(client);
  },
});

export { expect } from "@playwright/test";

// ---------------------------------------------------------------------------
// Global setup/teardown hooks
// ---------------------------------------------------------------------------

export async function globalSetup(): Promise<void> {
  startContainer();
  await waitForServer(TE_SERVER_URL);
}

export async function globalTeardown(): Promise<void> {
  stopContainer();
}
