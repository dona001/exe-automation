"""
Example client for the TE Server API.
Anyone on the network can use this to automate IBM 3270 terminals.

Usage:
    pip install requests
    python client_example.py
"""
import requests
import time

# Point this to wherever the Docker container is running
BASE_URL = "http://localhost:9995"


def te_api(endpoint, data=None):
    """Helper to call the TE Server API."""
    if data is None:
        data = {}
    resp = requests.post(f"{BASE_URL}/te/{endpoint}",
                         json=data, timeout=30)
    result = resp.json()
    if result["status"] != "200":
        raise Exception(f"API error: {result['error']}")
    return result["data"]


def print_screen(sname="default"):
    """Read and display the current 3270 screen."""
    data = te_api("screentext", {"sname": sname})
    print("=" * 80)
    for row_num in range(1, 25):
        print(data["text"].get(str(row_num), ""))
    print("=" * 80)


# ---------------------------------------------------------------------------
# Example 1: Basic - Read the screen
# ---------------------------------------------------------------------------
def example_read_screen():
    print("\n--- Example 1: Read Screen ---")
    print_screen()


# ---------------------------------------------------------------------------
# Example 2: Login to a mainframe
# ---------------------------------------------------------------------------
def example_login(username, password):
    print("\n--- Example 2: Login ---")

    # Read the login screen first
    print_screen()

    # Type username at row 10, col 20 (adjust to match your screen)
    te_api("entertext_by_row_col", {
        "text": username, "row": 10, "col": 20
    })

    # Type password at row 11, col 20
    te_api("entertext_by_row_col", {
        "text": password, "row": 11, "col": 20
    })

    # Press Enter
    te_api("send_special_key", {"key": "enter"})
    time.sleep(1)

    # See what happened
    print_screen()


# ---------------------------------------------------------------------------
# Example 3: Navigate menus with function keys
# ---------------------------------------------------------------------------
def example_navigate():
    print("\n--- Example 3: Navigate ---")

    # Type a command
    te_api("sendkeys", {"text": "TSO"})
    time.sleep(1)
    print_screen()

    # Press F3 to go back
    te_api("send_special_key", {"key": "F3"})
    time.sleep(1)
    print_screen()


# ---------------------------------------------------------------------------
# Example 4: Search for text on screen
# ---------------------------------------------------------------------------
def example_search():
    print("\n--- Example 4: Search ---")

    result = te_api("search", {"text": "READY"})
    if result["top"] != -1:
        print(f"Found 'READY' at row {result['top']}, col {result['left']}")
    else:
        print("'READY' not found on screen")


# ---------------------------------------------------------------------------
# Example 5: Run a CICS transaction
# ---------------------------------------------------------------------------
def example_cics_transaction(transaction_id):
    print(f"\n--- Example 5: CICS Transaction '{transaction_id}' ---")

    # Clear screen first
    te_api("clearscreen")
    time.sleep(0.5)

    # Type transaction ID and press Enter
    te_api("sendkeys", {"text": transaction_id})
    time.sleep(1)

    # Read the result
    print_screen()


# ---------------------------------------------------------------------------
# Example 6: Batch - Run multiple commands and collect output
# ---------------------------------------------------------------------------
def example_batch_commands(commands):
    print("\n--- Example 6: Batch Commands ---")
    results = []

    for cmd in commands:
        print(f"  Running: {cmd}")
        te_api("sendkeys", {"text": cmd})
        time.sleep(1)

        data = te_api("screentext")
        screen_text = "\n".join(
            data["text"].get(str(r), "") for r in range(1, 25)
        )
        results.append({"command": cmd, "screen": screen_text})

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Check server is running
    resp = requests.get(f"{BASE_URL}/te/ping")
    print(f"Server status: {resp.json()['data']['message']}")

    # Check active sessions
    resp = requests.get(f"{BASE_URL}/te/status")
    print(f"Sessions: {resp.json()['data']['sessions']}")

    # If no auto-connected session, start one manually:
    # te_api("startsession", {"path": "sessions/default.txt", "sname": "default"})

    # Run examples (uncomment what you need):
    example_read_screen()
    # example_login("MYUSER", "MYPASS")
    # example_navigate()
    # example_search()
    # example_cics_transaction("CEMT")
    # example_batch_commands(["STATUS", "CEMT I TASK"])
