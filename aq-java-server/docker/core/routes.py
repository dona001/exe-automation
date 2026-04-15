"""
Flask routes for the Java Access Bridge automation API.
Reconstructed from AQJavaServer.exe bytecode analysis.
"""
from flask import request, jsonify
from core import app, logger
from core import jabapi
from json import dumps
import base64
import time
import traceback
import sys
import pyperclip

# Session store: { "default": component_tree_root }
sessions = {}
ANCHOR_ELEM = None


def cleanup(text):
    if not text:
        return ""
    return text.replace("\r\n", "").replace("\n", "").replace('"', "'")


def ok(data=None):
    if data is None:
        data = {}
    return jsonify({"status": "200", "error": "", "data": data})


def error(status, err):
    return jsonify({"status": str(status), "error": f"{err}", "data": {}})


# =========================================================================
# Internal helpers
# =========================================================================

def java_find_all_(request_data, session_elem=None):
    """Find all matching elements in the Java component tree."""
    try:
        java_re_activate_()
        data = request_data
        sess = sessions.get("default")

        if session_elem:
            sess = session_elem
        elif ANCHOR_ELEM:
            sess = ANCHOR_ELEM

        direction = data.get("direction", "right")
        anchor = data.get("anchor")
        elem_def = data.get("elemDef", data)
        role = elem_def.get("role", "")
        name = elem_def.get("name", "")
        description = elem_def.get("description", "")
        elem_text = elem_def.get("elem_text", elem_def.get("text", ""))

        props = {}
        if elem_text:
            props["elem_text"] = elem_text

        results = jabapi.findElementsByProps(sess, role, name, description, props if props else None)

        if anchor and len(results) > 0:
            anchor_elem = java_find_one_(anchor)
            if anchor_elem:
                results = [find_adjacent_elem(results, anchor_elem, direction)]

        return results
    except Exception:
        traceback.print_exc(file=sys.stdout)
        raise Exception("Element not found")


def find_adjacent_elem(elements, anchor, direction="right"):
    """Find the element closest to the anchor in the given direction."""
    anchor_rect = get_elem_rect(anchor)
    min_dist = float("inf")
    closest = elements[0] if elements else None

    for elem in elements:
        elem_rect = get_elem_rect(elem)
        dist = get_dist(anchor_rect, elem_rect, direction)
        if dist < min_dist:
            min_dist = dist
            closest = elem

    return closest


def get_dist(rect1, rect2, direction):
    """Calculate distance between two rects in a given direction."""
    try:
        if direction == "right":
            return rect2["left"] - rect1["right"]
        elif direction == "left":
            return rect1["left"] - rect2["right"]
        elif direction == "below" or direction == "bottom":
            return rect2["top"] - rect1["bottom"]
        elif direction == "above" or direction == "top":
            return rect1["top"] - rect2["bottom"]
        else:
            raise Exception(f"Invalid direction specified: {direction}")
    except Exception:
        return float("inf")


def get_elem_rect(elem):
    """Get the bounding rectangle of an element, adjusted for DPR."""
    return {
        "left": elem.x / jabapi.DPR,
        "top": elem.y / jabapi.DPR,
        "right": (elem.x + elem.width) / jabapi.DPR,
        "bottom": (elem.y + elem.height) / jabapi.DPR,
    }


def java_find_parents_all_(request_data):
    """Find parent/internal frame elements."""
    try:
        data = request_data
        java_re_activate_()
        role = data.get("role", "")
        name = data.get("name", "")
        description = data.get("description", "")
        sess = sessions.get("default")
        results = jabapi.findInternalFrames(sess, role, name, description)
        if len(results) == 0:
            raise Exception(f"Parent with role:{role},name:{name},description:{description} not found")
        return results
    except Exception:
        traceback.print_exc(file=sys.stdout)
        raise


def java_find_one_(request_data, session_elem=None):
    """Find a single element by index from the matching results."""
    results = java_find_all_(request_data, session_elem)
    index = int(request_data.get("index", "1")) - 1
    role = request_data.get("role", "")
    name = request_data.get("name", "")
    description = request_data.get("description", "")

    if index >= len(results):
        raise Exception(
            f"Element Index Out of bounds. Found {len(results)} with "
            f"role:{role},name:{name},description:{description} not found. "
            f"Required index is {index + 1}"
        )
    print("found element")
    return results[index]


def java_elem_find_one_(request_data, session_elem=None):
    """Find a single element (alias for java_find_one_ with session context)."""
    results = java_find_all_(request_data, session_elem)
    index = int(request_data.get("index", "1")) - 1
    role = request_data.get("role", "")
    name = request_data.get("name", "")
    description = request_data.get("description", "")

    if index >= len(results):
        raise Exception(
            f"Element Index Out of bounds. Found {len(results)} with "
            f"role:{role},name:{name},description:{description} not found. "
            f"Required index is {index + 1}"
        )
    print("found element")
    return results[index]


def java_re_activate_():
    """Re-activate/refresh the current session."""
    sess = sessions.get("default")
    if sess:
        jabapi.refresh(sess)


# =========================================================================
# API Routes
# =========================================================================

@app.route("/aq/java/ping")
def api_rpa_ping():
    try:
        return ok({"ok": "Accelq Java Bridge Ping success, server is ready!!!"})
    except Exception as e:
        logger.error(f"Exception occurred {e}")
        return error(500, e), 500


@app.route("/aq/java/capture")
def capture():
    jabapi.java_capture_screen_()
    encoded_string = ""
    with open("Screenshot.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    return ok({"image": encoded_string})


@app.route("/aq/java/activate", methods=["POST"])
def api_java_activate():
    try:
        logger.debug(request.get_json())
        data = request.get_json()
        title = data.get("title")
        session = jabapi.activate(title)
        sessions["default"] = session
        print(f"activate result {session}")
        return ok({"vmID": str(session)})
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Failed to activate"), 500


@app.route("/aq/java/activateparent", methods=["POST"])
def api_java_activateparent():
    try:
        data = request.get_json()
        results = java_find_parents_all_(data)
        if len(results) == 0:
            return error(500, f"Parents with role:{data.get('role')},name:{data.get('name')},description:{data.get('description')} not found"), 500
        sessions["default"] = results[0]
        return ok({"role": cleanup(results[0].role), "name": cleanup(results[0].name), "description": cleanup(results[0].description)})
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Failed to activate parent"), 500


@app.route("/aq/java/resetparent", methods=["POST"])
def api_java_resetparent():
    try:
        sessions["default"] = None
        return ok()
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Failed to reset parent"), 500


@app.route("/aq/java/findall", methods=["POST"])
def api_java_find_all():
    try:
        data = request.get_json()
        results = java_find_all_(data)
        if len(results) == 0:
            role = data.get("role", "")
            name = data.get("name", "")
            desc = data.get("description", "")
            return error(500, f"Elements with role:{role},name:{name},description:{desc} not found"), 500
        return ok({"count": len(results)})
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Find all failed"), 500


@app.route("/aq/java/findone", methods=["POST"])
def api_java_find_one():
    try:
        data = request.get_json()
        elem = java_find_one_(data)
        return ok({"found": f"Name:{elem.name},Role:{elem.role},Description:{elem.description}"})
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Find one failed"), 500


@app.route("/aq/java/waitfor", methods=["POST"])
def api_java_waitfor():
    try:
        data = request.get_json()
        timeout = int(data.get("timeout", 30))
        index = data.get("index", "1")
        role = data.get("role", "")
        name = data.get("name", "")
        description = data.get("description", "")

        for _ in range(timeout):
            try:
                elem = java_find_one_(data)
                return ok({"found": f"Name:{elem.name},Role:{elem.role}"})
            except Exception:
                print("sleeping .....")
                time.sleep(1)

        return error(500, f"Waited for Timeout {timeout}. Element {role}-{name}-{description} Not found"), 500
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Wait for failed"), 500


@app.route("/aq/java/getvalue", methods=["POST"])
def api_java_get_value():
    try:
        data = request.get_json()
        elem = java_find_one_(data)
        value = jabapi.get_value(elem)
        return ok({"value": str(value)})
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Get value failed"), 500


@app.route("/aq/java/tableinfo", methods=["POST"])
def api_java_get_table_info():
    try:
        data = request.get_json()
        elem = java_find_one_(data)
        info = jabapi.get_table_info(elem)
        if not info:
            return error(500, "Failed to get table info for table"), 500
        return ok({"rowCount": str(info.rowCount), "columnCount": str(info.columnCount)})
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Get table info failed"), 500


@app.route("/aq/java/tablecellinfo", methods=["POST"])
def api_java_get_table_cell_info():
    try:
        data = request.get_json()
        elem = java_find_one_(data)
        row = int(data.get("row"))
        col = int(data.get("col"))
        details = jabapi.get_table_cell_details(elem, row, col)
        return ok(details)
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Failed to get table cell info"), 500


@app.route("/aq/java/trigger_accessible_action", methods=["POST"])
def api_java_trigger_accessible_action():
    try:
        data = request.get_json()
        elem = java_find_one_(data)
        action = data.get("action", "")
        if not action:
            return error(500, "Action not specified"), 500
        jabapi.trigger_accessible_action(elem, action)
        return ok()
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Trigger action failed"), 500


@app.route("/aq/java/tablecellclick", methods=["POST"])
def api_java_get_table_cell_click():
    try:
        data = request.get_json()
        elem = java_find_one_(data)
        row = int(data.get("row"))
        col = int(data.get("col"))
        jabapi.click_table_cell(elem, row, col)
        return ok()
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, f"Failed to click table cell Row:{data.get('row')}, Col:{data.get('col')}"), 500


@app.route("/aq/java/getattr", methods=["POST"])
def api_java_getattr():
    try:
        data = request.get_json()
        elem = java_find_one_(data)
        attr = data.get("attr", "")

        if attr.lower() == "name_jaws" or attr.lower() == "name (jaws algorithm)":
            value = jabapi.getJVirtualAccessibleName(elem)
        elif attr.lower() == "elem_text" or attr.lower() == "text":
            value = jabapi.get_value(elem)
        elif attr.lower() == "index_in_parent":
            value = jabapi.getElemIndexInParent(elem)
        elif attr.lower() == "states":
            value = jabapi.getElemStates(elem)
        elif hasattr(elem, attr):
            value = str(getattr(elem, attr))
        else:
            value = ""

        return ok({"value": str(value)})
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Get attr failed"), 500


@app.route("/aq/java/click", methods=["POST"])
def api_java_click():
    try:
        data = request.get_json()
        elem = java_find_one_(data)
        jabapi.clickMouse(elem)
        return ok()
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Click failed"), 500


@app.route("/aq/java/dblclick", methods=["POST"])
def api_java_dblclick():
    try:
        data = request.get_json()
        elem = java_find_one_(data)
        jabapi.dblClick(elem)
        return ok()
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Double click failed"), 500


@app.route("/aq/java/entertext", methods=["POST"])
def api_java_entertext():
    try:
        data = request.get_json()
        elem = java_find_one_(data)
        text = data.get("text", "")
        jabapi.send_keys(elem, text)
        return ok()
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Enter text failed"), 500


@app.route("/aq/java/sendkeys", methods=["POST"])
def api_java_sendkeys():
    try:
        data = request.get_json()
        elem = java_find_one_(data)
        text = data.get("text", "")
        jabapi.send_keys(elem, text)
        return ok()
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Send keys failed"), 500


@app.route("/aq/java/send_special_key", methods=["POST"])
def api_java_send_special_key():
    try:
        data = request.get_json()
        elem = java_find_one_(data)
        key = data.get("key", "")
        jabapi.send_special_key(elem, key)
        return ok()
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Send special key failed"), 500


@app.route("/aq/java/sendkeys_to_win", methods=["POST"])
def api_java_sendkeys_to_win():
    try:
        data = request.get_json()
        text = data.get("text", "")
        jabapi.send_keys_window(text)
        return ok()
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Send keys to window failed"), 500


@app.route("/aq/java/send_special_key_to_win", methods=["POST"])
def api_java_send_special_key_win():
    try:
        data = request.get_json()
        key = data.get("key", "")
        jabapi.send_special_key_window(key)
        return ok()
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Send special key to window failed"), 500


@app.route("/aq/java/press_key", methods=["POST"])
def api_java_press_key():
    try:
        data = request.get_json()
        elem = java_find_one_(data)
        key = data.get("key", "")
        jabapi.press_key(elem, key)
        return ok()
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Press key failed"), 500


@app.route("/aq/java/release_key", methods=["POST"])
def api_java_release_key():
    try:
        data = request.get_json()
        elem = java_find_one_(data)
        key = data.get("key", "")
        jabapi.release_key(elem, key)
        return ok()
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Release key failed"), 500


@app.route("/aq/java/cbbyindex", methods=["POST"])
def api_java_cb_by_index():
    try:
        data = request.get_json()
        elem = java_find_one_(data)
        sindex = data.get("sindex", "0")
        jabapi.select_cb_item_by_index(elem, sindex)
        return ok()
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Combo box select failed"), 500


@app.route("/aq/java/menuselect", methods=["POST"])
def api_java_menuselect():
    try:
        data = request.get_json()
        java_re_activate_()
        sess = sessions.get("default")
        menu_path = data.get("menu_path", "")
        jabapi.menuSelect(menu_path, sess)
        return ok()
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Menu select failed"), 500


@app.route("/aq/java/setanchor", methods=["POST"])
def api_java_set_anchor():
    global ANCHOR_ELEM
    try:
        data = request.get_json()
        elem = java_elem_find_one_(data, sessions.get("default"))
        if not elem:
            return error(500, "Element not found to set as anchor"), 500
        ANCHOR_ELEM = elem
        print("Anchor element set to: " + str(elem))
        return ok()
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Set anchor failed"), 500


@app.route("/aq/java/resetanchor", methods=["POST"])
def api_java_reset_anchor():
    global ANCHOR_ELEM
    try:
        ANCHOR_ELEM = None
        return ok()
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Reset anchor failed"), 500


@app.route("/aq/java/copy", methods=["POST"])
def api_java_copy():
    try:
        elem = java_elem_find_one_(request.get_json())
        jabapi.clickMouse(elem)
        jabapi.copy_to_clipboard()
        time.sleep(0.5)
        content = pyperclip.paste()
        print(f"Clipboard content: {content}")
        return ok({"clipboard_content": content})
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return error(500, "Failed to copy element to clipboard"), 500
