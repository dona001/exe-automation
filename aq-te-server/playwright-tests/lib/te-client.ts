/**
 * IBM 3270 Terminal Emulator Client
 *
 * Wraps the TE Server REST API into a clean, typed interface
 * for use in Playwright tests.
 */

export interface ScreenPosition {
  top: number;
  left: number;
}

export interface TEClientOptions {
  baseUrl?: string;
  sessionName?: string;
  timeout?: number;
}

export class TEClient {
  private baseUrl: string;
  private sessionName: string;
  private timeout: number;

  constructor(options: TEClientOptions = {}) {
    this.baseUrl = options.baseUrl || "http://localhost:9995";
    this.sessionName = options.sessionName || "default";
    this.timeout = options.timeout || 30000;
  }

  // -----------------------------------------------------------------------
  // Internal helpers
  // -----------------------------------------------------------------------

  private async api(endpoint: string, body: Record<string, unknown> = {}): Promise<any> {
    const payload = { sname: this.sessionName, ...body };

    const resp = await fetch(`${this.baseUrl}/te/${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(this.timeout),
    });

    const result = await resp.json();
    if (result.status !== "200") {
      throw new Error(`TE API error on /${endpoint}: ${result.error}`);
    }
    return result.data;
  }

  private async apiGet(endpoint: string): Promise<any> {
    const resp = await fetch(`${this.baseUrl}/te/${endpoint}`, {
      signal: AbortSignal.timeout(this.timeout),
    });
    return resp.json();
  }

  // -----------------------------------------------------------------------
  // Session management
  // -----------------------------------------------------------------------

  async ping(): Promise<boolean> {
    try {
      const data = await this.apiGet("ping");
      return data?.data?.pingstatus === "ok";
    } catch {
      return false;
    }
  }

  async startSession(sessionFilePath: string): Promise<void> {
    await this.api("startsession", { path: sessionFilePath });
  }

  async disconnect(): Promise<void> {
    await this.api("disconnect");
  }

  // -----------------------------------------------------------------------
  // Screen reading
  // -----------------------------------------------------------------------

  async getScreenText(): Promise<Record<number, string>> {
    const data = await this.api("screentext");
    return data.text;
  }

  async getScreenAsString(): Promise<string> {
    const rows = await this.getScreenText();
    return Object.values(rows).join("\n");
  }

  async getFieldText(row: number, col: number, length?: number): Promise<string> {
    const body: Record<string, unknown> = { row, col };
    if (length) body.length = length;
    const data = await this.api("fieldtext_by_row_col", body);
    return data.text;
  }

  async search(text: string): Promise<ScreenPosition> {
    return await this.api("search", { text });
  }

  // -----------------------------------------------------------------------
  // Input
  // -----------------------------------------------------------------------

  async sendKeys(text: string): Promise<void> {
    await this.api("sendkeys", { text });
  }

  async sendKeysNoEnter(text: string): Promise<void> {
    await this.api("sendkeysnoreturn", { text });
  }

  async fillField(row: number, col: number, text: string): Promise<void> {
    await this.api("entertext_by_row_col", { row, col, text });
  }

  async clearField(row: number, col: number): Promise<void> {
    await this.api("clear_text_by_row_col", { row, col });
  }

  // -----------------------------------------------------------------------
  // Special keys
  // -----------------------------------------------------------------------

  async pressEnter(): Promise<void> {
    await this.api("send_special_key", { key: "enter" });
  }

  async pressTab(): Promise<void> {
    await this.api("send_special_key", { key: "tab" });
  }

  async pressClear(): Promise<void> {
    await this.api("clearscreen");
  }

  async pressKey(key: string): Promise<void> {
    await this.api("send_special_key", { key });
  }

  async pressF(n: number): Promise<void> {
    await this.api("send_special_key", { key: `F${n}` });
  }

  async pressPA(n: number): Promise<void> {
    await this.api("send_special_key", { key: `PA${n}` });
  }

  // -----------------------------------------------------------------------
  // Navigation
  // -----------------------------------------------------------------------

  async moveTo(row: number, col: number): Promise<void> {
    await this.api("moveto", { row, col });
  }

  async pause(seconds: number): Promise<void> {
    await this.api("pause", { time: seconds });
  }

  async execCommand(cmd: string): Promise<void> {
    await this.api("exec", { cmd });
  }

  // -----------------------------------------------------------------------
  // Wait helpers (useful for test assertions)
  // -----------------------------------------------------------------------

  /**
   * Wait until specific text appears on screen.
   * Polls every `intervalMs` until `timeoutMs` is reached.
   */
  async waitForText(
    text: string,
    timeoutMs: number = 10000,
    intervalMs: number = 500
  ): Promise<ScreenPosition> {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const pos = await this.search(text);
      if (pos.top !== -1) return pos;
      await new Promise((r) => setTimeout(r, intervalMs));
    }
    throw new Error(
      `Timed out waiting for "${text}" on 3270 screen after ${timeoutMs}ms`
    );
  }

  /**
   * Wait until specific text disappears from screen.
   */
  async waitForTextGone(
    text: string,
    timeoutMs: number = 10000,
    intervalMs: number = 500
  ): Promise<void> {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const pos = await this.search(text);
      if (pos.top === -1) return;
      await new Promise((r) => setTimeout(r, intervalMs));
    }
    throw new Error(
      `Timed out waiting for "${text}" to disappear after ${timeoutMs}ms`
    );
  }

  /**
   * Get a specific row's text (1-indexed).
   */
  async getRow(row: number): Promise<string> {
    return this.getFieldText(row, 1, 80);
  }

  /**
   * Print the current screen to console (for debugging).
   */
  async printScreen(): Promise<void> {
    const screen = await this.getScreenAsString();
    console.log("=".repeat(80));
    console.log(screen);
    console.log("=".repeat(80));
  }
}
