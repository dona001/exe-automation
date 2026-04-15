"""
Example: Complex workflow — scoped search, keyboard combos, chaining.
"""
from java_bridge import JavaApp

app = JavaApp("http://localhost:9996")
app.activate("ERP System")

# --- Scoped search: only look inside a specific panel ---
app.set_parent("internal frame", "Order Entry")
app.fill("Customer ID", "CUST-001")
app.fill("Order Date", "2026-04-15")
app.press("tab", name="Order Date", role="text")
app.reset_parent()

# --- Chaining actions (Playwright-style) ---
app.locator("text", "Quantity").click().fill("100")
app.locator("text", "Unit Price").click().fill("29.99")

# --- Keyboard shortcuts ---
app.press("enter")                    # press Enter on active window
app.press("tab")                      # press Tab
app.locator("text", "Notes").press("enter")  # Enter on specific element

# --- Hold and release keys (for Shift+Click, Ctrl+A, etc.) ---
elem = app.locator("list item", "Item 1")
elem.press_key("shift")               # hold Shift
app.locator("list item", "Item 5").click()  # Shift+Click to select range
elem.release_key("shift")

# --- Copy element text to clipboard ---
text = app.locator("text", "Total Amount").copy()
print(f"Copied: {text}")

# --- Wait then verify ---
app.click("Submit Order")
app.wait_for("Order Confirmed", timeout=20)
app.screenshot("order_confirmed.png")

status = app.get_text("Order Status")
assert status == "Confirmed", f"Expected 'Confirmed', got '{status}'"
print("Order submitted successfully!")
