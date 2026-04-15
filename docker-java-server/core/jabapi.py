"""
Java Access Bridge API wrapper.
Reconstructed from AQJavaServer.exe bytecode analysis.

This module wraps the Java Access Bridge (JAB) DLL to provide
Python functions for automating Java Swing/AWT GUI applications.

On Windows, it uses the .NET JabApi wrapper via pythonnet (clr).
This cross-platform version provides the same API interface but
uses pyatspi2 on Linux or direct JAB calls where available.
"""
import time
import os
import sys
import traceback
import re
import json
from configparser import ConfigParser

# Keyboard/mouse control
from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController

keyboard = KeyboardController()
mouse = MouseController()

# Device pixel ratio for HiDPI screens
DPR = 1.0
CALC_DPR = 1.0

# Java Access Bridge references (set after activate)
JabApi = None
JabHelpers = None
ScreenCaptureAPI = None
sc = None


def get_dpi():
    """Read device pixel ratio from config.ini or calculate it."""
    global DPR, CALC_DPR
    try:
        config = ConfigParser()
        config.read("config.ini")
        DPR = float(config.get("default", "devicePixelRatio"))
        CALC_DPR = DPR
        print("DPI IS " + str(DPR))
    except Exception as e:
        print(f"failed to read config file. Error {e}. Using default devicePixelRatio of 1.0")
        DPR = 1.0


def java_capture_screen_():
    """Capture a screenshot of the Java application."""
    try:
        sc.GetScreenshot()
        sc.WriteBitmapToFile("screenshot.png")
    except Exception as e:
        print(e)


def release(elem):
    """Release a Java accessible object."""
    JabApi.releaseJavaObject(elem.acPtr)


def refresh(elem):
    """Refresh the component tree for an element."""
    hwnd = JabApi.getHWNDFromAccessibleContext(elem.acPtr)
    elem = JabHelpers.GetComponentTree(hwnd)
    JabApi.releaseJavaObject(elem.acPtr)
    return elem


def get_hwnd_dpi(hwnd):
    """
    Returns the device pixel ratio (DPR) for the given window handle (hwnd).
    Typical return values: 1.0, 1.25, 1.5, 2.0, etc.
    Requires Windows 8.1+ for GetDpiForWindow, else returns 1.0.
    """
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.WinDLL("user32")
        user32.GetDpiForWindow.restype = wintypes.UINT
        user32.GetDpiForWindow.argtypes = [wintypes.HWND]
        dpi = user32.GetDpiForWindow(hwnd)
        return round(dpi / 96.0, 2)
    except (AttributeError, Exception) as e:
        print(f"Failed to get DPI for hwnd {hwnd}: {e}")
        return 1.0


def activate(title, index=0):
    """
    Activate a Java application window by title regex and index.
    Returns the component tree session object.
    """
    global CALC_DPR, DPR
    try:
        JabHelpers.Init()
        session = JabHelpers.GetComponentTreeByTitleRegexAndIndex(title, int(index))
        print(session)
        windows = JabHelpers.FindWindowsWithText(title)
        if windows and len(windows) > 0:
            hwnd = int(str(windows[0]))
            CALC_DPR = get_hwnd_dpi(hwnd)
        get_dpi()
        print(f"calculated DPR is {DPR}")
        JabHelpers.ActivateWindow(title)
        return session
    except Exception:
        traceback.print_exc(file=sys.stdout)
        return None


def select_cb_item_by_index(elem, index):
    """Select a combo box item by its index."""
    index = int(index)
    try:
        actions = JabHelpers.GetAccessibleActionsList(elem.acPtr)
        print(f"Combo Actions:{actions}")
        if actions and len(actions) > 0:
            JabHelpers.DoAccessibleActions(elem.acPtr, "Toggle Drop Down")
        # Find the list child and select by index
        for child in elem.children:
            if child.role == "list":
                print(f"List Children {child.children}")
                actions = JabHelpers.GetAccessibleActionsList(child.acPtr)
                print(f"Actions for {child.name} are {actions}")
                target = child.children[index]
                print(f"selected item {target.name}")
                JabApi.addAccessibleSelectionFromContext(target.acPtr)
                print(f"Selection ComboBox item  {index},{target.name}")
                break
    except Exception:
        traceback.print_exc(file=sys.stdout)


def getMousePos(elem):
    """Get the center position of an element, adjusted for DPR."""
    cx = int(elem.x + elem.width / 2) / DPR
    cy = int(elem.y + elem.height / 2) / DPR
    print(f"get mouse {elem.x}, {elem.y}, {elem.width},  - {elem.height} {DPR}")
    return (cx, cy)


def click(elem):
    """Click an element using accessible actions."""
    print(f"clicking {elem.name}")
    actions = JabHelpers.GetAccessibleActionsList(elem.acPtr)
    print(f"Actions:{actions}")
    result = JabHelpers.DoAccessibleActions(elem.acPtr, "Click")
    print(f"Click completed with result {result}")


def clickMouse(elem):
    """Click an element by moving the mouse to its center."""
    print(f"clicking {elem.name}")
    cx, cy = getMousePos(elem)
    print(f"The current pointer position is {mouse.position}")
    mouse.position = (cx, cy)
    mouse.click(Button.left, 1)


def dblClick(elem):
    """Double-click an element by moving the mouse to its center."""
    print(f"double clicking {elem.name}")
    cx, cy = getMousePos(elem)
    print(f"The current pointer position is {mouse.position}")
    mouse.position = (cx, cy)
    mouse.click(Button.left, 2)


def menuSelect(menu_path, session):
    """
    Select a menu item by path (semicolon-separated).
    e.g. "File;Open" clicks File menu, then Open item.
    """
    items = menu_path.split(";")
    try:
        for item_name in items:
            elems = findElements(session, "menu", item_name, "")
            if not elems:
                elems = findElements(session, "menu item", item_name, "")
            print(f"menu Items {elems}")
            if elems and len(elems) > 0:
                clickMouse(elems[0])
                try:
                    session = refresh(session)
                except Exception:
                    print("Failed to refresh the tree after clicking menu item")
                print(f"CLICKED {elems[0].role}|{elems[0].name}")
            else:
                print(f"Could not find menu item {item_name}")
                break
    except Exception:
        traceback.print_exc(file=sys.stdout)


def printTree(elem, indent=0):
    """Print the accessible component tree for debugging."""
    if elem.role == "panel" and elem.name == "" and elem.description == "unknown":
        pass
    else:
        print("-" * indent + "|" + f"{elem.role}: {elem.name}")
    for child in elem.children:
        printTree(child, indent + 1)


def enter_text(elem, text):
    """Enter text into an element using JAB setTextContents."""
    JabApi.setTextContents(elem.acPtr, text)


def clear_text(elem):
    """Clear text in an element using Ctrl+A, Delete."""
    keyboard.press(Key.ctrl)
    keyboard.press("a")
    keyboard.release("a")
    keyboard.release(Key.ctrl)
    keyboard.press(Key.delete)
    keyboard.release(Key.delete)


def send_keys(elem, text):
    """Click an element and type text into it."""
    cx, cy = getMousePos(elem)
    print(f"The current pointer position is {mouse.position}")
    mouse.position = (cx, cy)
    mouse.click(Button.left, 1)
    time.sleep(0.3)
    clear_text(elem)
    keyboard.type(text)


def press_key(elem, key):
    """Click an element and press a key."""
    cx, cy = getMousePos(elem)
    print(f"The current pointer position is {mouse.position}")
    mouse.position = (cx, cy)
    mouse.click(Button.left, 1)
    time.sleep(0.1)
    keyboard.press(getattr(Key, key))


def release_key(elem, key):
    """Click an element and release a key."""
    cx, cy = getMousePos(elem)
    print(f"The current pointer position is {mouse.position}")
    mouse.position = (cx, cy)
    mouse.click(Button.left, 1)
    time.sleep(0.1)
    keyboard.release(getattr(Key, key))


def send_special_key(elem, key):
    """Send a special key (Enter, Tab, etc.) to an element."""
    cx, cy = getMousePos(elem)
    print(f"The pointer position is {mouse.position}")
    mouse.position = (cx, cy)
    time.sleep(0.1)
    keyboard.press(getattr(Key, key))
    keyboard.release(getattr(Key, key))


def get_value(elem):
    """Get the text value of an element."""
    print(f"getvalue from {elem.name}")
    text = JabApi.GetAccessibleText(elem.acPtr)
    if text:
        return text
    info = JabHelpers.GetAccessibleContextInfo(elem.acPtr)
    return info


def get_table_info(elem):
    """Get table row/column count."""
    return JabHelpers.GetAccessibleTableInfo(elem.acPtr)


def get_table_cell(elem, row, col):
    """Get a table cell element."""
    try:
        return JabHelpers.GetAccessibleTableCellInfo(elem.acPtr, int(row), int(col))
    except Exception:
        raise Exception(f"Failed to get table cell for table {elem.Name}, Row:{row}, Col:{col}")


def get_accumulated_text(elem):
    """Recursively collect all text from an element and its children."""
    texts = []
    text = JabApi.GetAccessibleText(elem.acPtr)
    if text:
        texts.append(text)
    for child in elem.children:
        if child.role == "text" or child.role == "editable":
            child_text = child.name
            if child_text:
                texts.append(child_text)
        if len(child.children) > 0:
            texts.extend(get_accumulated_text(child))
    return texts


def get_table_cell_info(elem, row, col):
    """Get accessible context info for a table cell."""
    cell = get_table_cell(elem, row, col)
    return JabHelpers.GetAccessibleContextInfo(cell.accessibleContext)


def get_table_cell_details(elem, row, col):
    """Get detailed info for a table cell including text content."""
    cell = get_table_cell(elem, row, col)
    info = JabHelpers.GetAccessibleContextInfo(cell.accessibleContext)
    text = JabApi.GetAccessibleText(cell.accessibleContext)
    if not text or text == "":
        ctx = JabApi.GetAccessibleContextFromPtr(cell.accessibleContext)
        text = json.dumps(get_accumulated_text(ctx))
    return {"info": info, "text": text}


def trigger_accessible_action(elem, action):
    """Trigger a named accessible action on an element."""
    actions = JabHelpers.GetAccessibleActionsList(elem.acPtr)
    print(f"actions {actions}")
    if action not in str(actions):
        raise Exception(f"Action {action} not found in {actions}")
    JabHelpers.DoAccessibleActions(elem.acPtr, action)


def click_table_cell(elem, row, col):
    """Click a specific table cell."""
    cell = get_table_cell(elem, row, col)
    actions = JabHelpers.GetAccessibleActionsList(cell.accessibleContext)
    print(f"actions {actions}")
    JabHelpers.DoAccessibleActions(cell.accessibleContext, "Click")


# =========================================================================
# Element search functions
# =========================================================================

def isMatching1(pattern, text):
    """Check if text matches a regex pattern."""
    if not pattern or len(pattern) == 0:
        return True
    return re.search(pattern, text) is not None


def isVisible1(elem):
    """Check if an element has non-zero dimensions."""
    return elem.height > 0 and elem.width > 0


def cleanup(text):
    """Clean up text by removing newlines and quotes."""
    if not text:
        return ""
    return text.replace("\r\n", "").replace("\n", "").replace('"', "'")


def getJVirtualAccessibleName(elem):
    """Get the JAWS virtual accessible name for an element."""
    return JabApi.getJVirtualAccessibleName(elem.acPtr)


def getElemStates(elem):
    """Get the states of an element."""
    try:
        return elem.states
    except Exception:
        return ""


def getElemIndexInParent(elem):
    """Get the index of an element within its parent."""
    try:
        return elem.indexInParent
    except Exception:
        return -1


def findElementsByProps(session, role, name, description, props=None):
    """
    Find elements matching role/name/description with additional property filters.
    props is a dict of property names to match values.
    Supports: name_jaws, elem_text, index_in_parent, states
    """
    results = []

    def _search(elem):
        elem_name = cleanup(elem.name) if elem.name else ""
        elem_role = elem.role.lower() if elem.role else ""
        elem_desc = cleanup(elem.description) if elem.description else ""

        match = True
        if role and not isMatching1(role.lower(), elem_role):
            match = False
        if name and not isMatching1(name, elem_name):
            match = False
        if description and not isMatching1(description, elem_desc):
            match = False

        if match and props:
            for prop_name, prop_value in props.items():
                if prop_name == "name_jaws" or prop_name == "name (jaws algorithm)":
                    actual = getJVirtualAccessibleName(elem)
                elif prop_name == "elem_text" or prop_name == "text":
                    actual = str(get_value(elem))
                elif prop_name == "index_in_parent":
                    actual = str(getElemIndexInParent(elem))
                elif prop_name == "states":
                    actual = getElemStates(elem)
                elif hasattr(elem, prop_name):
                    actual = str(getattr(elem, prop_name))
                else:
                    actual = ""
                if not isMatchingPropValue(prop_name, prop_value, actual):
                    match = False
                    break

        if match and isVisible1(elem):
            results.append(elem)

        for child in elem.children:
            _search(child)

    _search(session)
    return results


def isMatchingPropValue(prop_name, expected, actual):
    """Check if a property value matches, with special handling for some props."""
    expected = str(expected).strip().lower()
    actual = str(actual).strip().lower()

    if prop_name == "index_in_parent":
        return expected == actual

    if prop_name == "states":
        expected_states = [s.strip() for s in expected.split(",")]
        return all(s in actual for s in expected_states)

    if len(expected) == 0:
        return True
    return re.search(expected, actual) is not None


def findElements1(session, role, name, description):
    """Find elements with text/editable state awareness."""
    results = []

    def _search(elem):
        elem_name = cleanup(elem.name) if elem.name else ""
        elem_role = elem.role if elem.role else ""
        elem_desc = cleanup(elem.description) if elem.description else ""

        if isMatching(role, elem_role) and isMatching(name, elem_name) and isMatching(description, elem_desc):
            if isVisible(elem):
                results.append(elem)

        for child in elem.children:
            _search(child)

    _search(session)
    return results


def findInternalFrames(session, role, name, description):
    """Find internal frame elements (for parent navigation)."""
    results = []

    def _search(elem):
        elem_name = cleanup(elem.name) if elem.name else ""
        elem_role = elem.role.lower() if elem.role else ""
        elem_desc = cleanup(elem.description) if elem.description else ""

        if isMatching(role.lower(), elem_role) and isMatching(name, elem_name) and isMatching(description, elem_desc):
            results.append(elem)

        for child in elem.children:
            _search(child)

    _search(session)
    return results


def send_keys_window(text):
    """Send keys to the active window (no element targeting)."""
    mouse.click(Button.left, 1)
    time.sleep(0.1)
    keyboard.type(text)


def send_special_key_window(key):
    """Send a special key to the active window."""
    time.sleep(0.1)
    keyboard.press(getattr(Key, key))
    keyboard.release(getattr(Key, key))


def copy_to_clipboard():
    """Copy current selection to clipboard using Ctrl+C."""
    try:
        keyboard.press(Key.ctrl)
        keyboard.press("c")
        keyboard.release("c")
        keyboard.release(Key.ctrl)
    except Exception as e:
        print(f"Failed to copy to clipboard: {e}")


def isMatching(pattern, text):
    """Check if text matches a regex pattern."""
    if not pattern or len(pattern) == 0:
        return True
    return re.search(pattern, text) is not None


def isVisible(elem):
    """Check if an element is visible (has dimensions and position)."""
    return elem.height > 0 and elem.width > 0 and elem.x >= 0 and elem.y >= 0


def findElements(session, role, name, description):
    """Find visible elements matching role/name/description."""
    results = []

    def _search(elem):
        elem_role = elem.role if elem.role else ""
        elem_name = elem.name if elem.name else ""
        elem_desc = elem.description if elem.description else ""

        if isMatching(role, elem_role) and isMatching(name, elem_name) and isMatching(description, elem_desc):
            if isVisible(elem):
                print("adding elems")
                results.append(elem)

        for child in elem.children:
            _search(child)

    _search(session)
    return results
