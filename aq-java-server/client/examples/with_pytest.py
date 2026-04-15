"""
Example: Use with pytest as a test framework (like Playwright tests).

Run:
    pip install pytest
    pytest with_pytest.py -v
"""
import pytest
from java_bridge import JavaApp, JavaBridgeError


@pytest.fixture(scope="session")
def app():
    """Shared JavaApp instance for all tests."""
    client = JavaApp("http://localhost:9996", timeout=30)
    assert client.ping(), "AQJavaServer is not running"
    client.activate("My Java App")
    yield client


class TestLogin:
    def test_login_screen_visible(self, app):
        app.wait_for("Username", role="text", timeout=10)
        app.wait_for("Password", role="text", timeout=5)
        app.wait_for("Login", role="push button", timeout=5)

    def test_login_with_valid_credentials(self, app):
        app.fill("Username", "admin")
        app.fill("Password", "password123")
        app.click("Login")
        app.wait_for("Dashboard", timeout=15)

    def test_dashboard_shows_welcome(self, app):
        text = app.get_text("Welcome Message")
        assert "Welcome" in text

    def test_logout(self, app):
        app.menu("File;Logout")
        app.wait_for("Username", role="text", timeout=10)


class TestTableOperations:
    def test_table_has_data(self, app):
        tbl = app.table("Records")
        info = tbl.info()
        assert info["rows"] > 0
        assert info["cols"] > 0

    def test_click_table_cell(self, app):
        tbl = app.table("Records")
        tbl.click_cell(0, 0)  # click first cell

    def test_element_not_found_raises(self, app):
        with pytest.raises(JavaBridgeError):
            app.locator("push button", "NonExistentButton12345").click()
