"""
AQTEServer - Dockerized headless 3270 terminal automation REST API.
Rewritten from the decompiled AQTEServer.exe to run in Linux containers
using s3270 (headless x3270) instead of wc3270 (Windows GUI).
"""
from flask import Flask, request, jsonify, abort
from py3270 import Emulator
import time
import traceback
import sys
import os

app = Flask(__name__)

# Session store: { session_name: Emulator }
sessions = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ok(data=None, req=None):
    if data is None:
        data = {}
    return jsonify({"status": "200", "error": "", "data": data})


def error(status, err, req=None):
    return jsonify({"status": str(status), "error": str(err), "data": {}})


def check_request_valid():
    if not request.get_json():
        abort(400)


def get_session(sname=None):
    if not sname or sname == "":
        sname = "default"
    if sname not in sessions:
        raise Exception(f"Session '{sname}' not found. Start a session first.")
    return sessions[sname]


def read_session_file(path):
    """Parse a simple key=value session file."""
    info = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                key, val = line.split("=", 1)
                info[key.strip().lower()] = val.strip()
    return info


# ---------------------------------------------------------------------------
# Routes - Session Management
# ---------------------------------------------------------------------------

@app.route("/te/ping")
def ping():
    return ok({"pingstatus": "ok", "message": "PING success, remote aq server is ready!!!"})


@app.route("/te/init", methods=["POST"])
def init():
    return ok()


@app.route("/te/startsession", methods=["POST"])
def start_session():
    try:
        check_request_valid()
        data = request.get_json()
        sname = data.get("sname") or "default"
        sfile = data.get("path")

        if not sfile:
            return error(400, "Missing 'path' to session file"), 400

        sinfo = read_session_file(sfile)
        if "host" not in sinfo:
            raise Exception("Invalid session file — 'host' property not found")

        # Terminate existing session if any
        if sname in sessions:
            try:
                sessions[sname].terminate()
                time.sleep(0.5)
            except Exception:
                pass

        # s3270 is the headless (no GUI) version of x3270
        em = Emulator(visible=False, args=["-model", "2"])
        em.connect(sinfo["host"])
        em.wait_for_field()
        sessions[sname] = em

        return ok()
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return error(500, e), 500


@app.route("/te/disconnect", methods=["POST"])
def disconnect():
    try:
        check_request_valid()
        data = request.get_json()
        sname = data.get("sname") or "default"

        if sname in sessions:
            try:
                sessions[sname].terminate()
            except Exception:
                pass
            del sessions[sname]

        return ok()
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return error(500, e), 500


# ---------------------------------------------------------------------------
# Routes - Screen Reading
# ---------------------------------------------------------------------------

@app.route("/te/screentext", methods=["POST"])
def get_screen_text():
    try:
        check_request_valid()
        data = request.get_json()
        sname = data.get("sname") or "default"
        sess = get_session(sname)

        rows, cols = 24, 80
        screen = {}
        for i in range(rows):
            screen[i + 1] = sess.string_get(i + 1, 1, cols)

        return ok({"text": screen})
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return error(500, e), 500


@app.route("/te/fieldtext_by_row_col", methods=["POST"])
def get_field_text_by_row_col():
    try:
        check_request_valid()
        data = request.get_json()
        sname = data.get("sname") or "default"
        row = int(data.get("row"))
        col = int(data.get("col"))
        length = data.get("length")
        if not length or length == "":
            length = 80
        length = int(length)

        text = get_session(sname).string_get(row, col, length)
        return ok({"text": text})
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return error(500, e), 500


@app.route("/te/search", methods=["POST"])
def search_text():
    try:
        check_request_valid()
        data = request.get_json()
        sname = data.get("sname") or "default"
        text = data.get("text", "")
        sess = get_session(sname)

        # Support index syntax: "TEXT:::1" for second match
        parts = text.split(":::")
        search_text = parts[0]
        index = int(parts[1]) if len(parts) > 1 else 0

        rows, cols = 24, 80
        matches = []
        for i in range(rows):
            row_text = sess.string_get(i + 1, 1, cols)
            if search_text.lower() in row_text.lower():
                left = row_text.lower().index(search_text.lower()) + 1
                matches.append({"top": i + 1, "left": left})

        if len(matches) > index:
            return ok(matches[index])
        return ok({"top": -1, "left": -1})
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return error(500, e), 500


# ---------------------------------------------------------------------------
# Routes - Input / Typing
# ---------------------------------------------------------------------------

@app.route("/te/sendkeys", methods=["POST"])
def send_keys():
    try:
        check_request_valid()
        data = request.get_json()
        sname = data.get("sname") or "default"
        text = data.get("text", "")
        sess = get_session(sname)

        sess.send_string(text)
        sess.send_enter()
        sess.wait_for_field()
        return ok()
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return error(500, e), 500


@app.route("/te/sendkeysnoreturn", methods=["POST"])
def send_keys_no_return():
    try:
        check_request_valid()
        data = request.get_json()
        sname = data.get("sname") or "default"
        text = data.get("text", "")

        get_session(sname).send_string(text)
        return ok()
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return error(500, e), 500


@app.route("/te/entertext_by_row_col", methods=["POST"])
def enter_text_by_row_col():
    try:
        check_request_valid()
        data = request.get_json()
        sname = data.get("sname") or "default"
        text = data.get("text", "")
        row = int(data.get("row"))
        col = int(data.get("col"))

        sess = get_session(sname)

        if text == "<CLEAR_FIELD>":
            sess.move_to(row, col)
            sess.delete_field()
            return ok()

        if text == "<SET_CURSOR>":
            sess.move_to(row, col)
            return ok()

        sess.fill_field(row, col, text, len(text))
        return ok()
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return error(500, e), 500


@app.route("/te/clear_text_by_row_col", methods=["POST"])
def clear_text_by_row_col():
    try:
        check_request_valid()
        data = request.get_json()
        sname = data.get("sname") or "default"
        row = int(data.get("row"))
        col = int(data.get("col"))

        sess = get_session(sname)
        sess.move_to(row, col)
        sess.delete_field()
        return ok()
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return error(500, e), 500


# ---------------------------------------------------------------------------
# Routes - Special Keys
# ---------------------------------------------------------------------------

@app.route("/te/send_special_key", methods=["POST"])
def send_special_key():
    try:
        check_request_valid()
        data = request.get_json()
        sname = data.get("sname") or "default"
        key = data.get("key", "").lower()
        sess = get_session(sname)

        if key in ("\\", "/"):
            sess.send_string(key)
            return ok()

        if key == "clear":
            sess.exec_command(b"Clear")
        elif key == "enter":
            sess.send_enter()
        elif key == "tab":
            sess.exec_command(b"Tab")
        elif key == "erase-line" or key == "eraseeof":
            sess.exec_command(b"EraseEOF")
        elif key == "backspace":
            sess.exec_command(b"BackSpace")
        elif key == "delete":
            sess.exec_command(b"Delete")
        elif key == "home":
            sess.exec_command(b"Home")
        elif key == "insert":
            sess.exec_command(b"Insert")
        elif key == "newline":
            sess.exec_command(b"Newline")
        elif key == "reset":
            sess.exec_command(b"Reset")
        elif key.startswith("f") and key[1:].isdigit():
            num = int(key[1:])
            sess.exec_command(f"PF({num})".encode("ascii"))
        elif key.startswith("pa") and key[2:].isdigit():
            num = int(key[2:])
            sess.exec_command(f"PA({num})".encode("ascii"))
        else:
            raise Exception(f"Unsupported key: {key}")

        sess.wait_for_field()
        return ok()
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return error(500, e), 500


# ---------------------------------------------------------------------------
# Routes - Navigation & Misc
# ---------------------------------------------------------------------------

@app.route("/te/moveto", methods=["POST"])
def move_to():
    try:
        check_request_valid()
        data = request.get_json()
        sname = data.get("sname") or "default"
        row = int(data.get("row"))
        col = int(data.get("col"))

        get_session(sname).move_to(row, col)
        return ok()
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return error(500, e), 500


@app.route("/te/clearscreen", methods=["POST"])
def clear_screen():
    try:
        check_request_valid()
        data = request.get_json()
        sname = data.get("sname") or "default"

        get_session(sname).exec_command(b"Clear")
        get_session(sname).wait_for_field()
        return ok()
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return error(500, e), 500


@app.route("/te/pause", methods=["POST"])
def pause():
    try:
        check_request_valid()
        data = request.get_json()
        t = data.get("time", 1)
        time.sleep(float(t))
        return ok()
    except Exception as e:
        return error(500, e), 500


@app.route("/te/exec", methods=["POST"])
def exec_cmd():
    try:
        check_request_valid()
        data = request.get_json()
        sname = data.get("sname") or "default"
        command = data.get("cmd", "")

        get_session(sname).exec_command(command.encode("ascii"))
        return ok({"status": "ok"})
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return error(500, e), 500


# ---------------------------------------------------------------------------
# Auto-connect on startup
# ---------------------------------------------------------------------------

def auto_connect():
    """
    Automatically start sessions from session files in the auto-connect directory.
    Set AUTO_CONNECT_DIR env var to a directory containing .txt session files.
    Each file becomes a session named after the filename (without extension).
    e.g. sessions/default.txt -> session name "default"
    """
    auto_dir = os.environ.get("AUTO_CONNECT_DIR", "")
    if not auto_dir:
        return

    if not os.path.isdir(auto_dir):
        print(f"AUTO_CONNECT_DIR '{auto_dir}' not found, skipping auto-connect")
        return

    for fname in sorted(os.listdir(auto_dir)):
        if not fname.endswith(".txt"):
            continue

        sname = fname.rsplit(".", 1)[0]  # "default.txt" -> "default"
        fpath = os.path.join(auto_dir, fname)

        try:
            sinfo = read_session_file(fpath)
            if "host" not in sinfo:
                print(f"  SKIP {fname} — no 'host' property")
                continue

            print(f"  Auto-connecting session '{sname}' -> {sinfo['host']} ...")
            em = Emulator(visible=False, args=["-model", "2"])
            em.connect(sinfo["host"])
            em.wait_for_field()
            sessions[sname] = em
            print(f"  Session '{sname}' connected!")
        except Exception as e:
            print(f"  FAILED to auto-connect '{sname}': {e}")
            traceback.print_exc(file=sys.stdout)


# ---------------------------------------------------------------------------
# Health check - includes session status
# ---------------------------------------------------------------------------

@app.route("/te/status")
def status():
    session_info = {}
    for sname, em in sessions.items():
        try:
            # Try a lightweight operation to check if session is alive
            em.string_get(1, 1, 1)
            session_info[sname] = "connected"
        except Exception:
            session_info[sname] = "disconnected"
    return ok({"sessions": session_info})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("TE_PORT", 9995))

    print(f"Starting TE Server on port {port}...")
    auto_connect()

    app.run(debug=False, host="0.0.0.0", port=port, threaded=True)
