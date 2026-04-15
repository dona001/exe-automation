package com.aqbridge;

import org.testng.Assert;
import org.testng.annotations.*;

/**
 * Example: TestNG tests with auto server lifecycle.
 *
 * The server starts before tests and stops after — no manual EXE launch needed.
 *
 * Set the EXE path via environment variable or system property:
 *   -DAQJAVA_EXE=C:\tools\AQJavaServer\AQJavaServer.exe
 *
 * Or if the server is already running, just set:
 *   -DAQJAVA_URL=http://localhost:9996
 */
public class LoginTest {

    private static JavaBridgeServer server;
    private JavaApp app;

    @BeforeSuite
    public void startServer() {
        String exePath = System.getProperty("AQJAVA_EXE",
                System.getenv().getOrDefault("AQJAVA_EXE", ""));
        String serverUrl = System.getProperty("AQJAVA_URL",
                System.getenv().getOrDefault("AQJAVA_URL", ""));

        if (!serverUrl.isEmpty()) {
            // Server already running externally
            app = new JavaApp(serverUrl);
            Assert.assertTrue(app.ping(), "Server not reachable at " + serverUrl);
        } else if (!exePath.isEmpty()) {
            // Auto-start the EXE
            server = new JavaBridgeServer(exePath);
            server.start(30);
            app = server.connect();
        } else {
            // Default: assume localhost:9996
            app = new JavaApp("http://localhost:9996");
            Assert.assertTrue(app.ping(),
                    "AQJavaServer not running. Set AQJAVA_EXE or AQJAVA_URL");
        }
    }

    @AfterSuite
    public void stopServer() {
        if (server != null) {
            server.stop();
        }
    }

    @BeforeClass
    public void activateApp() {
        app.activate("My Java App");
    }

    // -----------------------------------------------------------------
    // Tests
    // -----------------------------------------------------------------

    @Test(priority = 1)
    public void testLoginScreenVisible() {
        app.waitFor("Username", "text", 10);
        app.waitFor("Password", "text", 5);
        app.waitFor("Login", "push button", 5);
    }

    @Test(priority = 2)
    public void testLogin() {
        app.fill("Username", "admin");
        app.fill("Password", "password123");
        app.click("Login");
        app.waitFor("Dashboard", 15);
    }

    @Test(priority = 3)
    public void testDashboardContent() {
        String text = app.getText("Welcome Message");
        Assert.assertTrue(text.contains("Welcome"));

        String balance = app.getText("Account Balance");
        Assert.assertFalse(balance.isEmpty());
    }

    @Test(priority = 4)
    public void testTableData() {
        JavaTable tbl = app.table("Records");
        Assert.assertTrue(tbl.getRowCount() > 0);
        tbl.clickCell(0, 0);
    }

    @Test(priority = 5)
    public void testLocatorChaining() {
        app.locator("text", "Search")
           .click()
           .fill("test query")
           .press("enter");

        app.waitFor("Results", 10);
    }

    @Test(priority = 100)
    public void testLogout() {
        app.menu("File;Logout");
        app.waitFor("Username", "text", 10);
    }
}
