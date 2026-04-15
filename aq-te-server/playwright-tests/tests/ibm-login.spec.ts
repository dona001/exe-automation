/**
 * Example: IBM 3270 Mainframe Login Test
 *
 * This test demonstrates how to automate an IBM mainframe login
 * using Playwright as the test runner + the TE Server API.
 *
 * Adjust row/col positions to match YOUR mainframe's login screen.
 */
import { test, expect } from "../lib/te-fixture";

test.describe("IBM 3270 Mainframe", () => {

  test("should connect and read the login screen", async ({ te }) => {
    // Start session (skip if AUTO_CONNECT_DIR is set in docker-compose)
    await te.startSession("sessions/default.txt");

    // Read the screen
    const screen = await te.getScreenAsString();
    console.log("Login screen:\n", screen);

    // Verify we see a login prompt (adjust text to match your system)
    const pos = await te.search("LOGON");
    expect(pos.top).not.toBe(-1);
  });

  test("should login with valid credentials", async ({ te }) => {
    // Fill in username (adjust row/col to your screen layout)
    await te.fillField(10, 20, "TESTUSER");

    // Fill in password
    await te.fillField(11, 20, "TESTPASS");

    // Press Enter to submit
    await te.pressEnter();

    // Wait for the next screen to load
    await te.waitForText("READY", 15000);

    // Verify we're logged in
    const screen = await te.getScreenAsString();
    expect(screen).toContain("READY");
  });

  test("should navigate to ISPF and back", async ({ te }) => {
    // Enter ISPF
    await te.sendKeys("ISPF");
    await te.waitForText("ISPF Primary Option Menu", 10000);

    // Verify ISPF menu loaded
    const screen = await te.getScreenAsString();
    expect(screen).toContain("ISPF Primary Option Menu");

    // Press F3 to exit back
    await te.pressF(3);
    await te.waitForText("READY", 10000);
  });

  test("should run a TSO command", async ({ te }) => {
    // Run LISTCAT command
    await te.sendKeys("LISTCAT");

    // Wait for output
    await te.pause(2);

    // Read the result
    const screen = await te.getScreenAsString();
    console.log("LISTCAT output:\n", screen);

    // Screen should have some content
    expect(screen.trim().length).toBeGreaterThan(0);
  });

  test("should search for text on screen", async ({ te }) => {
    await te.pressClear();
    await te.sendKeys("STATUS");
    await te.pause(1);

    const pos = await te.search("READY");
    if (pos.top !== -1) {
      console.log(`Found READY at row ${pos.top}, col ${pos.left}`);
      const rowText = await te.getRow(pos.top);
      expect(rowText).toContain("READY");
    }
  });

  test("should disconnect cleanly", async ({ te }) => {
    await te.sendKeys("LOGOFF");
    await te.pause(1);
    await te.disconnect();
  });
});
