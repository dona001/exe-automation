package com.aqbridge;

import com.google.gson.JsonObject;

/**
 * Represents a Java UI element locator with chainable actions.
 * Similar to Playwright's Locator.
 *
 * <pre>{@code
 * app.locator("text", "Username").click().fill("admin");
 * app.button("Submit").click();
 * String val = app.textField("Total").getValue();
 * }</pre>
 */
public class JavaElement {

    private final JavaApp app;
    private final String role;
    private final String name;
    private final String description;
    private final int index;

    JavaElement(JavaApp app, String role, String name, String description, int index) {
        this.app = app;
        this.role = role;
        this.name = name;
        this.description = description;
        this.index = index;
    }

    private JsonObject locator() {
        JsonObject body = new JsonObject();
        body.addProperty("role", role);
        body.addProperty("name", name);
        body.addProperty("description", description);
        body.addProperty("index", String.valueOf(index));
        return body;
    }

    /** Click this element. */
    public JavaElement click() {
        app.post("click", locator());
        return this;
    }

    /** Double-click this element. */
    public JavaElement doubleClick() {
        app.post("dblclick", locator());
        return this;
    }

    /** Fill this element with text (clears existing text first). */
    public JavaElement fill(String text) {
        JsonObject body = locator();
        body.addProperty("text", text);
        app.post("entertext", body);
        return this;
    }

    /** Type text into this element (keyboard simulation). */
    public JavaElement type(String text) {
        JsonObject body = locator();
        body.addProperty("text", text);
        app.post("sendkeys", body);
        return this;
    }

    /** Press a special key on this element (enter, tab, etc.). */
    public JavaElement press(String key) {
        JsonObject body = locator();
        body.addProperty("key", key);
        app.post("send_special_key", body);
        return this;
    }

    /** Press and hold a key on this element. */
    public JavaElement pressKey(String key) {
        JsonObject body = locator();
        body.addProperty("key", key);
        app.post("press_key", body);
        return this;
    }

    /** Release a held key on this element. */
    public JavaElement releaseKey(String key) {
        JsonObject body = locator();
        body.addProperty("key", key);
        app.post("release_key", body);
        return this;
    }

    /** Get the text value of this element. */
    public String getValue() {
        JsonObject data = app.post("getvalue", locator());
        return data.has("value") ? data.get("value").getAsString() : "";
    }

    /** Get an attribute of this element (states, index_in_parent, etc.). */
    public String getAttribute(String attr) {
        JsonObject body = locator();
        body.addProperty("attr", attr);
        JsonObject data = app.post("getattr", body);
        return data.has("value") ? data.get("value").getAsString() : "";
    }

    /** Copy this element's text to clipboard and return it. */
    public String copy() {
        JsonObject data = app.post("copy", locator());
        return data.has("clipboard_content") ? data.get("clipboard_content").getAsString() : "";
    }

    /** Trigger a named accessible action on this element. */
    public JavaElement triggerAction(String action) {
        JsonObject body = locator();
        body.addProperty("action", action);
        app.post("trigger_accessible_action", body);
        return this;
    }

    @Override
    public String toString() {
        return String.format("JavaElement(role='%s', name='%s', index=%d)", role, name, index);
    }
}
