package com.aqbridge.te;

import org.testng.Assert;
import org.testng.annotations.*;

/**
 * Example: TestNG tests for IBM 3270 mainframe automation.
 *
 * Run AQTEServer.exe first (or set AQTE_EXE for auto-start), then:
 *   mvn test -DAQTE_EXE=C:\tools\AQTEServer\AQTEServer.exe
 */
public class MainframeLoginTest {

    private static TEBridgeServer server;
    private TEApp te;

    @BeforeSuite
    public void startServer() {
        String exePath = System.getProperty("AQTE_EXE",
                System.getenv().getOrDefault("AQTE_EXE", ""));
        String serverUrl = System.getProperty("AQTE_URL",
                System.getenv().getOrDefault("AQTE_URL", ""));

        if (!serverUrl.isEmpty()) {
            te = new TEApp(serverUrl);
        } else if (!exePath.isEmpty()) {
            server = new TEBridgeServer(exePath);
            server.start(30);
            te = server.connect();
        } else {
            te = new TEApp("http://localhost:9995");
        }
        Assert.assertTrue(te.ping(), "AQTEServer not reachable");
    }

    @AfterSuite
    public void stopServer() {
        if (server != null) server.stop();
    }

    @Test(priority = 1)
    public void testStartSession() {
        te.startSession("session.ws");
        te.waitForText("LOGON", 15);
    }

    @Test(priority = 2)
    public void testLoginScreen() {
        String screen = te.getScreenText();
        Assert.assertTrue(screen.contains("USERID") || screen.contains("LOGON"),
                "Login screen should be visible");
        te.printScreen();
    }

    @Test(priority = 3)
    public void testLogin() {
        // Fill credentials at specific positions
        te.fillField(10, 20, "TESTUSER");
        te.fillField(11, 20, "TESTPASS");
        te.pressEnter();

        // Wait for main menu
        te.waitForText("READY", 15);
    }

    @Test(priority = 4)
    public void testNavigateToISPF() {
        te.sendKeys("ISPF");
        te.waitForText("ISPF Primary Option Menu", 10);

        String screen = te.getScreenText();
        Assert.assertTrue(screen.contains("ISPF"));
    }

    @Test(priority = 5)
    public void testF3Back() {
        te.pressF(3);
        te.waitForText("READY", 10);
    }

    @Test(priority = 6)
    public void testSearchText() {
        int[] pos = te.search("READY");
        Assert.assertNotNull(pos, "READY should be on screen");
        System.out.println("Found READY at row=" + pos[0] + ", col=" + pos[1]);
    }

    @Test(priority = 7)
    public void testReadFieldByRowCol() {
        String text = te.getFieldText(1, 1, 40);
        Assert.assertNotNull(text);
        Assert.assertFalse(text.trim().isEmpty());
    }

    @Test(priority = 8)
    public void testFillByLabel() {
        // Fill field next to a label
        te.fillFieldByLabel("COMMAND", "STATUS");
        te.pressEnter();
        te.pause(1);
    }

    @Test(priority = 9)
    public void testClearScreen() {
        te.pressClear();
        te.pause(0.5);
    }

    @Test(priority = 10)
    public void testScreenshot() {
        te.screenshot("mainframe_screen.png");
    }

    @Test(priority = 100)
    public void testLogoff() {
        te.sendKeys("LOGOFF");
        te.pause(1);
        te.disconnect();
    }
}
