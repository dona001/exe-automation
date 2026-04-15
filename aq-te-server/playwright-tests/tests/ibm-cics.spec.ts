/**
 * Example: CICS Transaction Test
 *
 * Shows how to automate CICS transactions on a 3270 terminal.
 * Adjust transaction IDs and field positions to your environment.
 */
import { test, expect } from "../lib/te-fixture";

test.describe("CICS Transactions", () => {

  test.beforeEach(async ({ te }) => {
    // Clear screen before each test
    await te.pressClear();
    await te.pause(0.5);
  });

  test("should run CEMT INQUIRE TASK", async ({ te }) => {
    await te.sendKeys("CEMT I TASK");
    await te.waitForText("TASK", 10000);

    const screen = await te.getScreenAsString();
    console.log("CEMT I TASK:\n", screen);
    expect(screen).toContain("TASK");

    // Exit transaction
    await te.pressF(3);
  });

  test("should handle a custom transaction", async ({ te }) => {
    // Type transaction ID
    await te.sendKeysNoEnter("XXXX");

    // Fill in input fields
    await te.pressTab();
    await te.sendKeysNoEnter("INPUT_VALUE");

    // Submit
    await te.pressEnter();
    await te.pause(2);

    // Read result
    const screen = await te.getScreenAsString();
    console.log("Transaction result:\n", screen);

    // Go back
    await te.pressF(3);
  });

  test("should navigate multi-screen transaction", async ({ te }) => {
    await te.sendKeys("CEMT I PROG");
    await te.waitForText("PROG", 10000);

    // Page down through results
    await te.pressF(8); // PF8 = Page Down in CICS
    await te.pause(1);

    const page2 = await te.getScreenAsString();
    console.log("Page 2:\n", page2);

    // Page back up
    await te.pressF(7); // PF7 = Page Up
    await te.pause(1);

    // Exit
    await te.pressF(3);
  });
});
