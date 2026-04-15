package com.aqbridge;

import com.google.gson.JsonObject;

/**
 * Table operations for Java tables.
 *
 * <pre>{@code
 * JavaTable tbl = app.table("Products");
 * int rows = tbl.getRowCount();
 * tbl.clickCell(2, 1);
 * JsonObject cell = tbl.getCell(0, 0);
 * }</pre>
 */
public class JavaTable {

    private final JavaApp app;
    private final String role;
    private final String name;
    private final String description;
    private final int index;

    JavaTable(JavaApp app, String role, String name, String description, int index) {
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

    /** Get table row and column count. */
    public TableInfo getInfo() {
        JsonObject data = app.post("tableinfo", locator());
        int rows = Integer.parseInt(data.get("rowCount").getAsString());
        int cols = Integer.parseInt(data.get("columnCount").getAsString());
        return new TableInfo(rows, cols);
    }

    /** Get row count. */
    public int getRowCount() {
        return getInfo().rows;
    }

    /** Get column count. */
    public int getColCount() {
        return getInfo().cols;
    }

    /** Get cell details at row, col. */
    public JsonObject getCell(int row, int col) {
        JsonObject body = locator();
        body.addProperty("row", row);
        body.addProperty("col", col);
        return app.post("tablecellinfo", body);
    }

    /** Click a specific table cell. */
    public JavaTable clickCell(int row, int col) {
        JsonObject body = locator();
        body.addProperty("row", row);
        body.addProperty("col", col);
        app.post("tablecellclick", body);
        return this;
    }

    /** Simple holder for table dimensions. */
    public static class TableInfo {
        public final int rows;
        public final int cols;

        public TableInfo(int rows, int cols) {
            this.rows = rows;
            this.cols = cols;
        }

        @Override
        public String toString() {
            return String.format("TableInfo(rows=%d, cols=%d)", rows, cols);
        }
    }
}
