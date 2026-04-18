package com.aqbridge.te;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.Map;
import java.nio.file.Files;
import java.nio.file.Path;
import com.google.gson.Gson;
import com.google.gson.JsonObject;

/**
 * Playwright-style client for automating IBM 3270 terminals via AQTEServer.
 *
 * <pre>{@code
 * TEApp te = new TEApp("http://localhost:9995");
 * te.startSession("session.ws");
 * te.waitForText("LOGON", 10);
 * te.fillField(10, 20, "MYUSER");
 * te.fillField(11, 20, "MYPASS");
 * te.pressEnter();
 * te.waitForText("READY", 15);
 * String screen = te.getScreenText();
 * te.disconnect();
 * }</pre>
 */
public class TEApp {

    private final String baseUrl;
    private final HttpClient http;
    private final Gson gson;
    private final int defaultTimeout;

    public TEApp(String baseUrl) {
        this(baseUrl, 30);
    }

    public TEApp(String baseUrl, int timeoutSeconds) {
        this.baseUrl = baseUrl.replaceAll("/$", "");
        this.defaultTimeout = timeoutSeconds;
        this.gson = new Gson();
        this.http = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(timeoutSeconds))
                .build();
    }

    // ------------------------------------------------------------------
    // Internal
    // ------------------------------------------------------------------

    JsonObject post(String endpoint, JsonObject body) {
        try {
            HttpRequest req = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + "/te/" + endpoint))
                    .header("Content-Type", "application/json")
                    .timeout(Duration.ofSeconds(defaultTimeout))
                    .POST(HttpRequest.BodyPublishers.ofString(gson.toJson(body)))
                    .build();
            HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
            JsonObject result = gson.fromJson(resp.body(), JsonObject.class);
            if (!"200".equals(result.get("status").getAsString())) {
                String error = result.has("error") ? result.get("error").getAsString() : "Unknown";
                throw new TEBridgeException(endpoint, error);
            }
            return result.has("data") ? result.getAsJsonObject("data") : new JsonObject();
        } catch (TEBridgeException e) {
            throw e;
        } catch (Exception e) {
            throw new TEBridgeException(endpoint, e.getMessage());
        }
    }

    private JsonObject get(String endpoint) {
        try {
            HttpRequest req = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + "/te/" + endpoint))
                    .timeout(Duration.ofSeconds(defaultTimeout))
                    .GET().build();
            HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
            JsonObject result = gson.fromJson(resp.body(), JsonObject.class);
            return result.has("data") ? result.getAsJsonObject("data") : new JsonObject();
        } catch (Exception e) {
            throw new TEBridgeException(endpoint, e.getMessage());
        }
    }

    private JsonObject body() {
        return new JsonObject();
    }

    // ------------------------------------------------------------------
    // Connection & Session
    // ------------------------------------------------------------------

    /** Check if the TE server is running. */
    public boolean ping() {
        try {
            JsonObject data = get("ping");
            return data.toString().contains("pingstatus");
        } catch (Exception e) {
            return false;
        }
    }

    /** Initialize the TE connection. */
    public TEApp init() {
        post("init", body());
        return this;
    }

    /** Start a terminal session with a session file path. */
    public TEApp startSession(String sessionFilePath) {
        JsonObject b = body();
        b.addProperty("path", sessionFilePath);
        post("startsession", b);
        return this;
    }

    /** Disconnect the terminal session. */
    public TEApp disconnect() {
        post("disconnect", body());
        return this;
    }

    /** Stop a terminal emulator process by name. */
    public TEApp stopProcess(String processName) {
        JsonObject b = body();
        b.addProperty("pname", processName);
        post("stopteprocess", b);
        return this;
    }

    // ------------------------------------------------------------------
    // Screen Reading
    // ------------------------------------------------------------------

    /** Get the full screen text as a map of row number → text. */
    public Map<Integer, String> getScreen() {
        JsonObject data = post("screentext", body());
        JsonObject text = data.getAsJsonObject("text");
        Map<Integer, String> screen = new LinkedHashMap<>();
        for (String key : text.keySet()) {
            screen.put(Integer.parseInt(key), text.get(key).getAsString());
        }
        return screen;
    }

    /** Get the full screen as a single string (24 rows joined by newline). */
    public String getScreenText() {
        Map<Integer, String> screen = getScreen();
        StringBuilder sb = new StringBuilder();
        for (int i = 1; i <= 24; i++) {
            sb.append(screen.getOrDefault(i, "")).append("\n");
        }
        return sb.toString();
    }

    /** Read text at a specific row and column with given length. */
    public String getFieldText(int row, int col, int length) {
        JsonObject b = body();
        b.addProperty("row", row);
        b.addProperty("col", col);
        b.addProperty("length", length);
        JsonObject data = post("fieldtext_by_row_col", b);
        return data.has("text") ? data.get("text").getAsString() : "";
    }

    /** Read text at a specific row and column (full row width). */
    public String getFieldText(int row, int col) {
        JsonObject b = body();
        b.addProperty("row", row);
        b.addProperty("col", col);
        JsonObject data = post("fieldtext_by_row_col", b);
        return data.has("text") ? data.get("text").getAsString() : "";
    }

    /** Search for text on screen. Returns row/col position or null if not found. */
    public int[] search(String text) {
        JsonObject b = body();
        b.addProperty("text", text);
        JsonObject data = post("search", b);
        int top = data.has("top") ? data.get("top").getAsInt() : -1;
        int left = data.has("left") ? data.get("left").getAsInt() : -1;
        if (top == -1) return null;
        return new int[]{top, left};
    }

    /** Check if text exists on the current screen. */
    public boolean screenContains(String text) {
        return search(text) != null;
    }

    // ------------------------------------------------------------------
    // Input
    // ------------------------------------------------------------------

    /** Send text and press Enter. */
    public TEApp sendKeys(String text) {
        JsonObject b = body();
        b.addProperty("text", text);
        post("sendkeys", b);
        return this;
    }

    /** Send text without pressing Enter. */
    public TEApp sendKeysNoReturn(String text) {
        JsonObject b = body();
        b.addProperty("text", text);
        post("sendkeysnoreturn", b);
        return this;
    }

    /** Fill a field at specific row/col position. */
    public TEApp fillField(int row, int col, String text) {
        JsonObject b = body();
        b.addProperty("row", row);
        b.addProperty("col", col);
        b.addProperty("text", text);
        post("entertext_by_row_col", b);
        return this;
    }

    /** Fill a field found by search text (label). */
    public TEApp fillFieldByLabel(String label, String text) {
        JsonObject b = body();
        b.addProperty("srchtext", label);
        b.addProperty("text", text);
        post("entertext_by_srchtext", b);
        return this;
    }

    /** Clear a field at specific row/col. */
    public TEApp clearField(int row, int col) {
        JsonObject b = body();
        b.addProperty("row", row);
        b.addProperty("col", col);
        post("clear_text_by_row_col", b);
        return this;
    }

    /** Clear a field found by search text. */
    public TEApp clearFieldByLabel(String label) {
        JsonObject b = body();
        b.addProperty("srchtext", label);
        post("clear_field_text_by_srchtext", b);
        return this;
    }

    // ------------------------------------------------------------------
    // Special Keys
    // ------------------------------------------------------------------

    /** Press Enter. */
    public TEApp pressEnter() {
        return pressKey("ENTER");
    }

    /** Press Tab. */
    public TEApp pressTab() {
        return pressKey("TAB");
    }

    /** Press F-key (1-24). */
    public TEApp pressF(int n) {
        return pressKey("F" + n);
    }

    /** Press PA key (1-3). */
    public TEApp pressPA(int n) {
        return pressKey("A" + n);
    }

    /** Press Clear. */
    public TEApp pressClear() {
        post("clearscreen", body());
        return this;
    }

    /** Press any special key by name. */
    public TEApp pressKey(String key) {
        JsonObject b = body();
        b.addProperty("key", key);
        post("send_special_key", b);
        return this;
    }

    /** Press and hold a key (shift, ctrl, alt). */
    public TEApp pressAndHold(String key) {
        JsonObject b = body();
        b.addProperty("key", key);
        b.addProperty("mode", "down");
        post("pressandholdkey", b);
        return this;
    }

    /** Release a held key. */
    public TEApp releaseHeld(String key) {
        JsonObject b = body();
        b.addProperty("key", key);
        b.addProperty("mode", "up");
        post("pressandholdkey", b);
        return this;
    }

    // ------------------------------------------------------------------
    // Navigation
    // ------------------------------------------------------------------

    /** Move cursor to a specific row/col. */
    public TEApp moveTo(int row, int col) {
        JsonObject b = body();
        b.addProperty("row", row);
        b.addProperty("col", col);
        post("moveto", b);
        return this;
    }

    /** Move to element found by search text. */
    public TEApp moveToLabel(String label) {
        JsonObject b = body();
        b.addProperty("srchtext", label);
        post("move_to_element_by_srchtext", b);
        return this;
    }

    /** Pause for specified seconds. */
    public TEApp pause(double seconds) {
        JsonObject b = body();
        b.addProperty("time", seconds);
        post("pause", b);
        return this;
    }

    // ------------------------------------------------------------------
    // Waiting
    // ------------------------------------------------------------------

    /**
     * Wait for text to appear on screen (polls every 500ms).
     *
     * @param text           text to search for
     * @param timeoutSeconds max seconds to wait
     * @throws TEBridgeException if text not found within timeout
     */
    public TEApp waitForText(String text, int timeoutSeconds) {
        long deadline = System.currentTimeMillis() + (timeoutSeconds * 1000L);
        while (System.currentTimeMillis() < deadline) {
            if (screenContains(text)) {
                return this;
            }
            try {
                Thread.sleep(500);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
        throw new TEBridgeException("waitForText",
                "Text '" + text + "' not found within " + timeoutSeconds + "s");
    }

    /** Wait for text with default timeout. */
    public TEApp waitForText(String text) {
        return waitForText(text, defaultTimeout);
    }

    /**
     * Wait for text to disappear from screen.
     */
    public TEApp waitForTextGone(String text, int timeoutSeconds) {
        long deadline = System.currentTimeMillis() + (timeoutSeconds * 1000L);
        while (System.currentTimeMillis() < deadline) {
            if (!screenContains(text)) {
                return this;
            }
            try {
                Thread.sleep(500);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
        throw new TEBridgeException("waitForTextGone",
                "Text '" + text + "' still present after " + timeoutSeconds + "s");
    }

    /** Wait for the host to be ready (input not inhibited). */
    public TEApp waitForReady(int timeoutSeconds) {
        long deadline = System.currentTimeMillis() + (timeoutSeconds * 1000L);
        while (System.currentTimeMillis() < deadline) {
            try {
                JsonObject data = post("isready", body());
                if ("yes".equals(data.get("res").getAsString())) {
                    return this;
                }
            } catch (Exception e) {
                // ignore, retry
            }
            try {
                Thread.sleep(500);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
        throw new TEBridgeException("waitForReady", "Host not ready within " + timeoutSeconds + "s");
    }

    // ------------------------------------------------------------------
    // Status
    // ------------------------------------------------------------------

    /** Check if the terminal is ready for input. */
    public boolean isReady() {
        try {
            JsonObject data = post("isready", body());
            return "yes".equals(data.get("res").getAsString());
        } catch (Exception e) {
            return false;
        }
    }

    /** Check if there's a message waiting. */
    public boolean isMessageWaiting() {
        try {
            JsonObject data = post("ismesswaiting", body());
            return "yes".equals(data.get("res").getAsString());
        } catch (Exception e) {
            return false;
        }
    }

    /** Get cursor position as [row, col]. */
    public int[] getCursorPosition() {
        JsonObject data = post("position", body());
        return new int[]{
                data.get("row").getAsInt(),
                data.get("col").getAsInt()
        };
    }

    // ------------------------------------------------------------------
    // Screenshot
    // ------------------------------------------------------------------

    /** Capture screenshot and save to file. Returns base64 string. */
    public String screenshot(String filePath) {
        try {
            JsonObject data = get("capture");
            String imgB64 = data.has("image") ? data.get("image").getAsString() : "";
            if (!imgB64.isEmpty()) {
                Files.write(Path.of(filePath), Base64.getDecoder().decode(imgB64));
            }
            return imgB64;
        } catch (Exception e) {
            throw new TEBridgeException("capture", e.getMessage());
        }
    }

    /** Print the current screen to stdout (for debugging). */
    public TEApp printScreen() {
        String screen = getScreenText();
        System.out.println("=".repeat(80));
        System.out.println(screen);
        System.out.println("=".repeat(80));
        return this;
    }
}
