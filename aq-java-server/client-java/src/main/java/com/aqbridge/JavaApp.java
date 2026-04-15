package com.aqbridge;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Base64;
import java.nio.file.Files;
import java.nio.file.Path;
import com.google.gson.Gson;
import com.google.gson.JsonObject;

/**
 * Playwright-style client for automating Java Swing/AWT applications
 * via the AQJavaServer REST API.
 *
 * <pre>{@code
 * JavaApp app = new JavaApp("http://localhost:9996");
 * app.activate("My Java App");
 * app.fill("Username", "admin");
 * app.fill("Password", "secret");
 * app.click("Login");
 * app.waitFor("Welcome", 15);
 * System.out.println(app.getText("Account Balance"));
 * }</pre>
 */
public class JavaApp {

    private final String baseUrl;
    private final HttpClient http;
    private final Gson gson;
    private final int defaultTimeout;

    public JavaApp(String baseUrl) {
        this(baseUrl, 30);
    }

    public JavaApp(String baseUrl, int timeoutSeconds) {
        this.baseUrl = baseUrl.replaceAll("/$", "");
        this.defaultTimeout = timeoutSeconds;
        this.gson = new Gson();
        this.http = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(timeoutSeconds))
                .build();
    }

    // ------------------------------------------------------------------
    // Internal HTTP helpers
    // ------------------------------------------------------------------

    JsonObject post(String endpoint, JsonObject body) {
        try {
            HttpRequest req = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + "/aq/java/" + endpoint))
                    .header("Content-Type", "application/json")
                    .timeout(Duration.ofSeconds(defaultTimeout))
                    .POST(HttpRequest.BodyPublishers.ofString(gson.toJson(body)))
                    .build();

            HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
            JsonObject result = gson.fromJson(resp.body(), JsonObject.class);

            if (!"200".equals(result.get("status").getAsString())) {
                String error = result.has("error") ? result.get("error").getAsString() : "Unknown error";
                throw new JavaBridgeException(endpoint, error);
            }
            return result.has("data") ? result.getAsJsonObject("data") : new JsonObject();
        } catch (JavaBridgeException e) {
            throw e;
        } catch (Exception e) {
            throw new JavaBridgeException(endpoint, e.getMessage());
        }
    }

    private JsonObject get(String endpoint) {
        try {
            HttpRequest req = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + "/aq/java/" + endpoint))
                    .timeout(Duration.ofSeconds(defaultTimeout))
                    .GET()
                    .build();

            HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
            JsonObject result = gson.fromJson(resp.body(), JsonObject.class);
            return result.has("data") ? result.getAsJsonObject("data") : new JsonObject();
        } catch (Exception e) {
            throw new JavaBridgeException(endpoint, e.getMessage());
        }
    }

    private JsonObject buildLocator(String role, String name, String description, int index) {
        JsonObject body = new JsonObject();
        body.addProperty("role", role);
        body.addProperty("name", name);
        body.addProperty("description", description);
        body.addProperty("index", String.valueOf(index));
        return body;
    }

    // ------------------------------------------------------------------
    // Connection
    // ------------------------------------------------------------------

    /** Check if the AQJavaServer is running. */
    public boolean ping() {
        try {
            JsonObject data = get("ping");
            return data.toString().contains("ok");
        } catch (Exception e) {
            return false;
        }
    }

    /** Activate a Java application window by title (supports regex). */
    public JavaApp activate(String title) {
        JsonObject body = new JsonObject();
        body.addProperty("title", title);
        post("activate", body);
        return this;
    }

    // ------------------------------------------------------------------
    // Locators — Playwright-style element finding
    // ------------------------------------------------------------------

    /** Create a locator for any element by role and name. */
    public JavaElement locator(String role, String name) {
        return new JavaElement(this, role, name, "", 1);
    }

    /** Create a locator with description and index. */
    public JavaElement locator(String role, String name, String description, int index) {
        return new JavaElement(this, role, name, description, index);
    }

    /** Shortcut: locate a push button by name. */
    public JavaElement button(String name) {
        return new JavaElement(this, "push button", name, "", 1);
    }

    /** Shortcut: locate a text field by name. */
    public JavaElement textField(String name) {
        return new JavaElement(this, "text", name, "", 1);
    }

    /** Shortcut: locate a label by name. */
    public JavaElement label(String name) {
        return new JavaElement(this, "label", name, "", 1);
    }

    /** Shortcut: locate a combo box by name. */
    public JavaElement comboBox(String name) {
        return new JavaElement(this, "combo box", name, "", 1);
    }

    /** Shortcut: locate a list item by name. */
    public JavaElement listItem(String name) {
        return new JavaElement(this, "list item", name, "", 1);
    }

    /** Get a table locator for table operations. */
    public JavaTable table(String name) {
        return new JavaTable(this, "table", name, "", 1);
    }

    // ------------------------------------------------------------------
    // Quick actions — Playwright-style shortcuts
    // ------------------------------------------------------------------

    /** Click a button by name. */
    public JavaApp click(String name) {
        return click(name, "push button");
    }

    /** Click an element by name and role. */
    public JavaApp click(String name, String role) {
        locator(role, name).click();
        return this;
    }

    /** Double-click an element. */
    public JavaApp doubleClick(String name, String role) {
        locator(role, name).doubleClick();
        return this;
    }

    /** Fill a text field by name. */
    public JavaApp fill(String name, String text) {
        textField(name).fill(text);
        return this;
    }

    /** Type text into a field (keyboard simulation). */
    public JavaApp typeText(String name, String text) {
        textField(name).type(text);
        return this;
    }

    /**
     * Press a special key on the active window.
     * Keys: enter, tab, escape, backspace, delete, shift, ctrl, alt, f1-f12
     */
    public JavaApp press(String key) {
        JsonObject body = new JsonObject();
        body.addProperty("key", key);
        post("send_special_key_to_win", body);
        return this;
    }

    /** Press a special key on a specific element. */
    public JavaApp press(String key, String name, String role) {
        locator(role, name).press(key);
        return this;
    }

    /** Get the text value of an element. */
    public String getText(String name) {
        return getText(name, "");
    }

    /** Get the text value of an element by name and role. */
    public String getText(String name, String role) {
        return locator(role, name).getValue();
    }

    /** Select a combo box item by index. */
    public JavaApp select(String comboName, int itemIndex) {
        JsonObject body = buildLocator("combo box", comboName, "", 1);
        body.addProperty("sindex", String.valueOf(itemIndex));
        post("cbbyindex", body);
        return this;
    }

    /** Navigate menus by semicolon-separated path. e.g. "File;Open" */
    public JavaApp menu(String path) {
        JsonObject body = new JsonObject();
        body.addProperty("menu_path", path);
        post("menuselect", body);
        return this;
    }

    /** Type text directly to the active window. */
    public JavaApp typeToWindow(String text) {
        JsonObject body = new JsonObject();
        body.addProperty("text", text);
        post("sendkeys_to_win", body);
        return this;
    }

    // ------------------------------------------------------------------
    // Waiting
    // ------------------------------------------------------------------

    /** Wait for an element to appear (default timeout). */
    public JavaApp waitFor(String name) {
        return waitFor(name, "", defaultTimeout);
    }

    /** Wait for an element to appear with custom timeout. */
    public JavaApp waitFor(String name, int timeoutSeconds) {
        return waitFor(name, "", timeoutSeconds);
    }

    /** Wait for an element to appear by role with custom timeout. */
    public JavaApp waitFor(String name, String role, int timeoutSeconds) {
        JsonObject body = new JsonObject();
        body.addProperty("role", role);
        body.addProperty("name", name);
        body.addProperty("description", "");
        body.addProperty("timeout", timeoutSeconds);
        post("waitfor", body);
        return this;
    }

    /** Explicit wait in seconds. */
    public JavaApp wait(double seconds) {
        try {
            Thread.sleep((long) (seconds * 1000));
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        return this;
    }

    // ------------------------------------------------------------------
    // Context / Scope
    // ------------------------------------------------------------------

    /** Scope element search to a parent container. */
    public JavaApp setParent(String role, String name) {
        JsonObject body = new JsonObject();
        body.addProperty("role", role);
        body.addProperty("name", name);
        body.addProperty("description", "");
        post("activateparent", body);
        return this;
    }

    /** Reset parent scope to the full window. */
    public JavaApp resetParent() {
        post("resetparent", new JsonObject());
        return this;
    }

    /** Set an anchor element for relative positioning. */
    public JavaApp setAnchor(String role, String name) {
        JsonObject body = new JsonObject();
        body.addProperty("role", role);
        body.addProperty("name", name);
        body.addProperty("description", "");
        post("setanchor", body);
        return this;
    }

    /** Reset the anchor element. */
    public JavaApp resetAnchor() {
        post("resetanchor", new JsonObject());
        return this;
    }

    // ------------------------------------------------------------------
    // Screenshot
    // ------------------------------------------------------------------

    /** Capture a screenshot and save to file. */
    public String screenshot(String filePath) {
        try {
            JsonObject data = get("capture");
            String imgB64 = data.has("image") ? data.get("image").getAsString() : "";
            if (!imgB64.isEmpty()) {
                byte[] bytes = Base64.getDecoder().decode(imgB64);
                Files.write(Path.of(filePath), bytes);
            }
            return filePath;
        } catch (Exception e) {
            throw new JavaBridgeException("capture", e.getMessage());
        }
    }
}
