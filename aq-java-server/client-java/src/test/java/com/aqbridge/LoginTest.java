package com.aqbridge;

import org.testng.Assert;
import org.testng.annotations.*;

/**
 * Example: TestNG tests for a Java Swing login application.
 *
 * Run AQJavaServer.exe first, then:
 *   mvn test
 */
public class LoginTest {

    private JavaApp app;

    @BeforeClass
    public void setup() {
        app = new JavaApp("http://localhost:9996", 30);
        Assert.assertTrue(app.ping(), "AQJavaServer is not running");
        app.activate("My Java App");
    }

    @Test(priority = 1)
    public void testLoginScreenVisible() {
        app.waitFor("Username", "text", 10);
        app.waitFor("Password", "text", 5);
        app.waitFor("Login", "push button", 5);
    }

    @Test(priority = 2)
    public void testLoginWithValidCredentials() {
        app.fill("Username", "admin");
        app.fill("Password", "password123");
        app.click("Login");
        app.waitFor("Dashboard", 15);
    }

    @Test(priority = 3)
    public void testDashboardShowsWelcome() {
        String text = app.getText("Welcome Message");
        Assert.assertTrue(text.contains("Welcome"), "Expected welcome message");
    }

    @Test(priority = 4)
    public void testReadAccountBalance() {
        String balance = app.getText("Account Balance");
        Assert.assertNotNull(balance);
        Assert.assertFalse(balance.isEmpty(), "Balance should not be empty");
        System.out.println("Account Balance: " + balance);
    }

    @Test(priority = 5)
    public void testNavigateViaMenu() {
        app.menu("File;Settings");
        app.waitFor("Settings", "internal frame", 10);
        app.screenshot("settings_screen.png");

        // Go back
        app.press("escape");
        app.waitFor("Dashboard", 10);
    }

    @Test(priority = 6)
    public void testTableOperations() {
        JavaTable tbl = app.table("Records");
        JavaTable.TableInfo info = tbl.getInfo();
        Assert.assertTrue(info.rows > 0, "Table should have rows");

        // Click first cell
        tbl.clickCell(0, 0);
    }

    @Test(priority = 7)
    public void testComboBoxSelection() {
        app.select("Country", 3);
        String selected = app.comboBox("Country").getValue();
        Assert.assertNotNull(selected);
    }

    @Test(priority = 8)
    public void testElementChaining() {
        // Playwright-style chaining
        app.locator("text", "Search")
           .click()
           .fill("test query")
           .press("enter");

        app.waitFor("Results", 10);
    }

    @Test(priority = 9)
    public void testScopedSearch() {
        // Search only within a specific panel
        app.setParent("internal frame", "Order Entry");
        app.fill("Customer ID", "CUST-001");
        app.resetParent();
    }

    @Test(priority = 100)
    public void testLogout() {
        app.menu("File;Logout");
        app.waitFor("Username", "text", 10);
    }

    @AfterClass
    public void teardown() {
        app.screenshot("final_state.png");
    }
}
