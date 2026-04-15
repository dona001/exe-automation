"""
Java Bridge Client — Playwright-style API for Java Swing/AWT automation.

Usage:
    from java_bridge import JavaApp

    app = JavaApp("http://localhost:9996")
    app.activate("My Java App")
    app.fill("Username", "admin")
    app.fill("Password", "secret")
    app.click("Login")
    app.wait_for("Welcome", timeout=10)
    print(app.get_text("Account Balance"))
    app.screenshot("login_done.png")

The AQJavaServer.exe must be running on the same Windows machine
as the Java application you're automating.
"""
import requests
import time
import base64
import os


class JavaElement:
    """Represents a found Java UI element with chainable actions."""

    def __init__(self, app: "JavaApp", role: str, name: str,
                 description: str = "", index: int = 1):
        self.app = app
        self.role = role
        self.name = name
        self.description = description
        self.index = index
        self._locator = {
            "role": role, "name": name,
            "description": description, "index": str(index),
        }

    def click(self) -> "JavaElement":
        self.app._post("click", self._locator)
        return self

    def double_click(self) -> "JavaElement":
        self.app._post("dblclick", self._locator)
        return self

    def fill(self, text: str) -> "JavaElement":
        self.app._post("entertext", {**self._locator, "text": text})
        return self

    def type(self, text: str) -> "JavaElement":
        self.app._post("sendkeys", {**self._locator, "text": text})
        return self

    def press(self, key: str) -> "JavaElement":
        self.app._post("send_special_key", {**self._locator, "key": key})
        return self

    def press_key(self, key: str) -> "JavaElement":
        self.app._post("press_key", {**self._locator, "key": key})
        return self

    def release_key(self, key: str) -> "JavaElement":
        self.app._post("release_key", {**self._locator, "key": key})
        return self

    def get_value(self) -> str:
        resp = self.app._post("getvalue", self._locator)
        return resp.get("value", "")

    def get_attr(self, attr: str) -> str:
        resp = self.app._post("getattr", {**self._locator, "attr": attr})
        return resp.get("value", "")

    def copy(self) -> str:
        resp = self.app._post("copy", self._locator)
        return resp.get("clipboard_content", "")

    def trigger_action(self, action: str) -> "JavaElement":
        self.app._post("trigger_accessible_action",
                        {**self._locator, "action": action})
        return self

    def __repr__(self):
        return f"JavaElement(role='{self.role}', name='{self.name}')"


class JavaTable:
    """Table operations — like Playwright's locator but for Java tables."""

    def __init__(self, app: "JavaApp", role: str, name: str,
                 description: str = "", index: int = 1):
        self.app = app
        self._locator = {
            "role": role, "name": name,
            "description": description, "index": str(index),
        }

    def info(self) -> dict:
        resp = self.app._post("tableinfo", self._locator)
        return {"rows": int(resp["rowCount"]), "cols": int(resp["columnCount"])}

    def cell(self, row: int, col: int) -> dict:
        resp = self.app._post("tablecellinfo",
                               {**self._locator, "row": row, "col": col})
        return resp

    def click_cell(self, row: int, col: int):
        self.app._post("tablecellclick",
                        {**self._locator, "row": row, "col": col})

    def row_count(self) -> int:
        return self.info()["rows"]

    def col_count(self) -> int:
        return self.info()["cols"]


class JavaApp:
    """
    Main entry point — like Playwright's `page` object.

    Wraps the AQJavaServer REST API into a clean, Playwright-style interface.
    """

    def __init__(self, base_url: str = "http://localhost:9996", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _post(self, endpoint: str, body: dict = None) -> dict:
        if body is None:
            body = {}
        resp = requests.post(
            f"{self.base_url}/aq/java/{endpoint}",
            json=body, timeout=self.timeout,
        )
        data = resp.json()
        if data["status"] != "200":
            raise JavaBridgeError(endpoint, data.get("error", "Unknown error"))
        return data.get("data", {})

    def _get(self, endpoint: str) -> dict:
        resp = requests.get(
            f"{self.base_url}/aq/java/{endpoint}",
            timeout=self.timeout,
        )
        return resp.json().get("data", {})

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def ping(self) -> bool:
        """Check if the server is running."""
        try:
            data = self._get("ping")
            return "ok" in str(data)
        except Exception:
            return False

    def activate(self, title: str) -> "JavaApp":
        """
        Activate a Java application window by title (supports regex).

            app.activate("My Java App")
            app.activate(".*Calculator.*")
        """
        self._post("activate", {"title": title})
        return self

    # ------------------------------------------------------------------
    # Locators — Playwright-style element finding
    # ------------------------------------------------------------------

    def locator(self, role: str = "", name: str = "",
                description: str = "", index: int = 1) -> JavaElement:
        """
        Create a locator for a Java UI element.

            app.locator("push button", "Submit").click()
            app.locator("text", "Username").fill("admin")
        """
        return JavaElement(self, role, name, description, index)

    def button(self, name: str, index: int = 1) -> JavaElement:
        """Shortcut for push button locator."""
        return JavaElement(self, "push button", name, "", index)

    def text_field(self, name: str, index: int = 1) -> JavaElement:
        """Shortcut for text field locator."""
        return JavaElement(self, "text", name, "", index)

    def label(self, name: str, index: int = 1) -> JavaElement:
        """Shortcut for label locator."""
        return JavaElement(self, "label", name, "", index)

    def combo_box(self, name: str, index: int = 1) -> JavaElement:
        """Shortcut for combo box locator."""
        return JavaElement(self, "combo box", name, "", index)

    def list_item(self, name: str, index: int = 1) -> JavaElement:
        """Shortcut for list item locator."""
        return JavaElement(self, "list item", name, "", index)

    def table(self, name: str = "", role: str = "table",
              index: int = 1) -> JavaTable:
        """
        Get a table locator for table operations.

            tbl = app.table("Accounts")
            print(tbl.row_count())
            tbl.click_cell(0, 2)
        """
        return JavaTable(self, role, name, "", index)

    # ------------------------------------------------------------------
    # Quick actions — Playwright-style shortcuts
    # ------------------------------------------------------------------

    def click(self, name: str, role: str = "push button") -> "JavaApp":
        """
        Click an element by name.

            app.click("Submit")
            app.click("Row 1", role="list item")
        """
        self.locator(role, name).click()
        return self

    def double_click(self, name: str, role: str = "") -> "JavaApp":
        """Double-click an element."""
        self.locator(role, name).double_click()
        return self

    def fill(self, name: str, text: str) -> "JavaApp":
        """
        Fill a text field by name.

            app.fill("Username", "admin")
            app.fill("Password", "secret123")
        """
        self.text_field(name).fill(text)
        return self

    def type_text(self, name: str, text: str) -> "JavaApp":
        """Type text character by character (with keyboard simulation)."""
        self.text_field(name).type(text)
        return self

    def press(self, key: str, name: str = "", role: str = "") -> "JavaApp":
        """
        Press a special key on an element or the active window.

            app.press("enter")
            app.press("tab", name="Username", role="text")
        """
        if name:
            self.locator(role, name).press(key)
        else:
            self._post("send_special_key_to_win", {"key": key})
        return self

    def get_text(self, name: str, role: str = "") -> str:
        """
        Get the text value of an element.

            balance = app.get_text("Account Balance")
        """
        return self.locator(role, name).get_value()

    def select(self, combo_name: str, item_index: int) -> "JavaApp":
        """
        Select a combo box item by index.

            app.select("Country", 3)
        """
        self._post("cbbyindex", {
            "role": "combo box", "name": combo_name,
            "sindex": str(item_index),
        })
        return self

    def menu(self, path: str) -> "JavaApp":
        """
        Navigate menus by semicolon-separated path.

            app.menu("File;Open")
            app.menu("Edit;Preferences;General")
        """
        self._post("menuselect", {"menu_path": path})
        return self

    # ------------------------------------------------------------------
    # Waiting — like Playwright's expect/waitFor
    # ------------------------------------------------------------------

    def wait_for(self, name: str, role: str = "", timeout: int = None) -> "JavaApp":
        """
        Wait for an element to appear on screen.

            app.wait_for("Welcome")
            app.wait_for("Dashboard", role="internal frame", timeout=20)
        """
        t = timeout or self.timeout
        self._post("waitfor", {
            "role": role, "name": name,
            "description": "", "timeout": t,
        })
        return self

    def wait(self, seconds: float) -> "JavaApp":
        """Explicit wait (use sparingly)."""
        time.sleep(seconds)
        return self

    # ------------------------------------------------------------------
    # Context / Scope
    # ------------------------------------------------------------------

    def set_parent(self, role: str, name: str, description: str = "") -> "JavaApp":
        """
        Scope element search to a parent container (like an internal frame).

            app.set_parent("internal frame", "Account Details")
            app.fill("Name", "John")  # searches only within that frame
        """
        self._post("activateparent", {
            "role": role, "name": name, "description": description,
        })
        return self

    def reset_parent(self) -> "JavaApp":
        """Reset parent scope to the full window."""
        self._post("resetparent")
        return self

    def set_anchor(self, role: str, name: str) -> "JavaApp":
        """Set an anchor element for relative positioning."""
        self._post("setanchor", {"role": role, "name": name, "description": ""})
        return self

    def reset_anchor(self) -> "JavaApp":
        """Reset the anchor element."""
        self._post("resetanchor")
        return self

    # ------------------------------------------------------------------
    # Screenshot
    # ------------------------------------------------------------------

    def screenshot(self, path: str = "screenshot.png") -> str:
        """
        Capture a screenshot and save to file.

            app.screenshot("after_login.png")
        """
        data = self._get("capture")
        img_b64 = data.get("image", "")
        if img_b64:
            with open(path, "wb") as f:
                f.write(base64.b64decode(img_b64))
        return path

    # ------------------------------------------------------------------
    # Keyboard shortcuts to active window
    # ------------------------------------------------------------------

    def type_to_window(self, text: str) -> "JavaApp":
        """Type text directly to the active window (no element targeting)."""
        self._post("sendkeys_to_win", {"text": text})
        return self

    def press_to_window(self, key: str) -> "JavaApp":
        """Send a special key to the active window."""
        self._post("send_special_key_to_win", {"key": key})
        return self


class JavaBridgeError(Exception):
    """Raised when a Java Bridge API call fails."""

    def __init__(self, endpoint: str, message: str):
        self.endpoint = endpoint
        self.message = message
        super().__init__(f"JavaBridge /{endpoint}: {message}")
