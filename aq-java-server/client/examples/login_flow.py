"""
Example: Automate a Java login form.

Prerequisites:
    1. AQJavaServer.exe running on the Windows machine
    2. Java app with login form open
    3. Java Access Bridge enabled
"""
from java_bridge import JavaApp

app = JavaApp("http://localhost:9996")

# Verify server is running
assert app.ping(), "AQJavaServer is not running!"

# Activate the Java application window
app.activate("MyApp Login")

# Fill in credentials and submit
app.fill("Username", "admin")
app.fill("Password", "secret123")
app.click("Login")

# Wait for the dashboard to load
app.wait_for("Welcome", timeout=15)

# Take a screenshot
app.screenshot("login_success.png")

# Read a value from the dashboard
balance = app.get_text("Account Balance")
print(f"Account Balance: {balance}")
