# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.10.0 (default, Mar  2 2025, 19:23:58) [Clang 16.0.0 (clang-1600.0.26.3)]
# Embedded file name: pyrobot.py
"""

A pure python windows automation library loosely modeled after Java's Robot Class.

TODO:
  * Mac support
  * Allow window section for relative coordinates.
  * ability to 'paint' target window.

I can never remember how these map...
----  LEGEND ----

BYTE      = c_ubyte
WORD      = c_ushort
DWORD     = c_ulong
LPBYTE    = POINTER(c_ubyte)
LPTSTR    = POINTER(c_char)
HANDLE    = c_void_p
PVOID     = c_void_p
LPVOID    = c_void_p
UNIT_PTR  = c_ulong
SIZE_T    = c_ulong

"""
import sys, time, ctypes, multiprocessing
from ctypes import *
from ctypes.wintypes import *
user32 = windll.user32
gdi = windll.gdi32
kernel32 = windll.kernel32
cdll = cdll.msvcrt

class WIN32CON(object):
    LEFT_DOWN = 2
    LEFT_UP = 4
    MIDDLE_DOWN = 32
    MIDDLE_UP = 64
    MOVE = 1
    RIGHT_DOWN = 8
    RIGHT_UP = 16
    WHEEL = 2048
    XDOWN = 128
    XUP = 256
    HWHEEL = 4096


win32con = WIN32CON

class BITMAP(ctypes.Structure):
    _fields_ = [
     (
      'bmType', c_int),
     (
      'bmWidth', c_int),
     (
      'bmHeight', c_int),
     (
      'bmHeightBytes', c_int),
     (
      'bmPlanes', c_short),
     (
      'bmBitsPixel', c_short),
     (
      'bmBits', c_void_p)]


class BITMAPFILEHEADER(ctypes.Structure):
    _fields_ = [
     (
      'bfType', ctypes.c_short),
     (
      'bfSize', ctypes.c_uint32),
     (
      'bfReserved1', ctypes.c_short),
     (
      'bfReserved2', ctypes.c_short),
     (
      'bfOffBits', ctypes.c_uint32)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
     (
      'biSize', ctypes.c_uint32),
     (
      'biWidth', ctypes.c_int),
     (
      'biHeight', ctypes.c_int),
     (
      'biPlanes', ctypes.c_short),
     (
      'biBitCount', ctypes.c_short),
     (
      'biCompression', ctypes.c_uint32),
     (
      'biSizeImage', ctypes.c_uint32),
     (
      'biXPelsPerMeter', ctypes.c_long),
     (
      'biYPelsPerMeter', ctypes.c_long),
     (
      'biClrUsed', ctypes.c_uint32),
     (
      'biClrImportant', ctypes.c_uint32)]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [
     (
      'bmiHeader', BITMAPINFOHEADER),
     (
      'bmiColors', ctypes.c_ulong * 3)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
     (
      'dx', LONG),
     (
      'dy', LONG),
     (
      'mouseData', DWORD),
     (
      'dwFlags', DWORD),
     (
      'time', DWORD),
     (
      'dwExtraInfo', POINTER(ULONG))]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
     (
      'wVk', WORD),
     (
      'wScan', WORD),
     (
      'dwFlags', DWORD),
     (
      'time', DWORD),
     (
      'dwExtraInfo', POINTER(ULONG))]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
     (
      'uMsg', DWORD),
     (
      'wParamL', WORD),
     (
      'wParamH', DWORD)]


class INPUT(ctypes.Structure):

    class _I(Union):
        _fields_ = [
         (
          'mi', MOUSEINPUT),
         (
          'ki', KEYBDINPUT),
         (
          'hi', HARDWAREINPUT)]

    _anonymous_ = 'i'
    _fields_ = [
     (
      'type', DWORD),
     (
      'i', _I)]


class RECT(ctypes.Structure):
    _fields_ = [
     (
      'left', c_long),
     (
      'top', c_long),
     (
      'right', c_long),
     (
      'bottom', c_long)]


class KeyConsts(object):
    _key_names = [
     0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 7, 13, 14, 
     15, 16, 17, 18, 19, 20, 7, 21, 22, 23, 24, 7, 25, 26, 27, 
     28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 
     42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 
     7, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 
     70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 
     84, 10, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 
     97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 
     110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 
     122, 123, 124, 125, 126, 127, 128, 129, 126, 130, 131, 132, 
     133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 
     145, 146, 147, 148, 149, 150, 151, 152, 153, 10, 154, 155, 
     156, 157, 158, 159, 160, 10, 126, 161, 162, 163, 164, 165, 
     10, 129, 166, 129, 167, 129, 168, 126, 129, 169, 170, 171, 
     172, 173, 174, 10, 175, 11, 176]
    _vk_codes = [32, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 16, 17, 18, 19, 20, 21, 21, 21, 22, 23, 24, 25, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58 - 40, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 144, 145, 146, 151, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 186, 187, 188, 189, 190, 191, 192, 193, 216, 219, 220, 221, 222, 223, 224, 225, 226, 227, 229, 230, 231, 232, 233, 246, 247, 248, 249, 250, 251, 252, 253, 254, 46]
    _shifted_keys = '~!@#$%^&*()_+|}{":?><'
    _unshifted_keys = "`1234567890-=\\][';/.,"
    special_map = {key: val for key, val in zip(_shifted_keys, _unshifted_keys)}
    key_mapping = {key: code for key, code in zip(_key_names, _vk_codes)}


class Keys(object):
    space = 32
    left_mouse_button = 1
    right_mouse_button = 2
    control_break_processing = 3
    middle_mouse_button_three_button_mouse = 4
    x1_mouse_button = 5
    x2_mouse_button = 6
    undefined = 7
    backspace = 8
    tab = 9
    reserved = 10
    clear = 12
    enter = 13
    undefined = 14
    shift = 16
    ctrl = 17
    alt = 18
    pause = 19
    caps_lock = 20
    undefined = 22
    undefined = 26
    esc = 27
    spacebar = 32
    page_up = 33
    page_down = 34
    end = 35
    home = 36
    left_arrow = 37
    up_arrow = 38
    right_arrow = 39
    down_arrow = 40
    select = 41
    print_key = 42
    execute = 43
    print_screen = 44
    ins = 45
    delete = 46
    help_key = 47
    zero = 48
    one = 49
    two = 50
    three = 51
    four = 52
    five = 53
    six = 54
    seven = 55
    eight = 56
    nine = 57
    undefined = 18
    a = 65
    b = 66
    c = 67
    d = 68
    e = 69
    f = 70
    g = 71
    h = 72
    i = 73
    j = 74
    k = 75
    l = 76
    m = 77
    n = 78
    o = 79
    p = 80
    q = 81
    r = 82
    s = 83
    t = 84
    u = 85
    v = 86
    w = 87
    x = 88
    y = 89
    z = 90
    left_windows__natural_board = 91
    right_windows__natural_board = 92
    applications__natural_board = 93
    reserved = 94
    computer_sleep = 95
    numeric_pad_0 = 96
    numeric_pad_1 = 97
    numeric_pad_2 = 98
    numeric_pad_3 = 99
    numeric_pad_4 = 100
    numeric_pad_5 = 101
    numeric_pad_6 = 102
    numeric_pad_7 = 103
    numeric_pad_8 = 104
    numeric_pad_9 = 105
    multiply = 106
    add = 107
    separator = 108
    subtract = 109
    decimal = 110
    divide = 111
    f1 = 112
    f2 = 113
    f3 = 114
    f4 = 115
    f5 = 116
    f6 = 117
    f7 = 118
    f8 = 119
    f9 = 120
    f10 = 121
    f11 = 122
    f12 = 123
    f13 = 124
    f14 = 125
    f15 = 126
    f16 = 127
    f17 = 128
    f18 = 129
    f19 = 130
    f20 = 131
    f21 = 132
    f22 = 133
    f23 = 134
    f24 = 135
    unassigned = 136
    num_lock = 144
    scroll_lock = 145
    oem_specific = 146
    unassigned = 151
    left_shift = 160
    right_shift = 161
    left_control = 162
    right_control = 163
    left_menu = 164
    right_menu = 165
    browser_back = 166
    browser_forward = 167
    browser_refresh = 168
    browser_stop = 169
    browser_search = 170
    browser_favorites = 171
    browser_start_and_home = 172
    volume_mute = 173
    volume_down = 174
    volume_up = 175
    next_track = 176
    previous_track = 177
    stop_media = 178
    play_pause_media = 179
    start_mail = 180
    select_media = 181
    start_application_1 = 182
    start_application_2 = 183
    reserved = 184
    semicolon = 186
    equals = 187
    comma = 188
    minus = 189
    peiod = 190
    forward_slash = 191
    back_tick = 192
    reserved = 193
    unassigned = 216
    open_brace = 219
    backslash = 220
    close_brace = 221
    apostrophe = 222
    reserved = 224
    oem_specific = 225
    either_the_angle_bracket__or_the_backslash__on_the_rt_102__board = 226
    oem_specific = 227
    oem_specific = 230
    unassigned = 232
    oem_specific = 233
    attn = 246
    crsel = 247
    exsel = 248
    erase_eof = 249
    play = 250
    zoom = 251
    reserved = 252
    pa1 = 253
    clear = 254


class Robot(object):
    """
  A pure python windows automation library loosely modeled after Java's Robot Class.
  """

    def __init__(self, wname=None):
        wname = wname if wname is not None else user32.GetDesktopWindow()
        try:
            wname.lower()
            hwnd = self.get_window_hwnd(wname)
            if hwnd:
                self.hwnd = hwnd
            else:
                raise Exception('Invalid window name/hwnd')
        except AttributeError:
            self.hwnd = wname

        return

    def set_mouse_pos(self, x, y):
        """
    Moves mouse pointer to given screen coordinates.
    """
        wx, wy = self.pos
        user32.SetCursorPos(x + wx, y + wy)
        return

    def get_mouse_pos(self):
        """
    Returns current mouse coordinates
    """
        coords = pointer(c_long(0))
        user32.GetCursorPos(coords)
        x, y = coords[0], coords[1]
        wx, wy = self.pos
        return (x - wx, y - wy)

    def get_pixel(self, x=None, y=None):
        """
    Returns the pixel color of the given screen coordinate or the current mouse position
    """
        if x is None or y is None:
            x, y = self.get_mouse_pos()
            wx, wy = self.pos
            x, y = x + wx, y + wy
        else:
            wx, wy = self.pos
            x, y = wx + x, wy + y
        RGBInt = gdi.GetPixel(user32.GetDC(0), x, y)
        red = RGBInt & 255
        green = RGBInt >> 8 & 255
        blue = RGBInt >> 16 & 255
        return (red, green, blue)

    def mouse_down(self, button):
        """
    Presses one mouse button. Left, right, or middle
    """
        press_events = {'left': (
                  win32con.LEFT_DOWN, None, None, None, None), 
           'right': (
                   win32con.RIGHT_DOWN, None, None, None, None), 
           'middle': (
                    win32con.MIDDLE_DOWN, None, None, None, None)}
        user32.mouse_event(*press_events[button.lower()])
        return

    def mouse_up(self, button):
        """
    Releases mouse button. Left, right, or middle
    """
        release_events = {'left': (
                  win32con.LEFT_UP, None, None, None, None), 
           'right': (
                   win32con.RIGHT_UP, None, None, None, None), 
           'middle': (
                    win32con.MIDDLE_UP, None, None, None, None)}
        user32.mouse_event(*release_events[button.lower()])
        return

    def click_mouse(self, button):
        """
    Simulates a full mouse click. One down event, one up event.
    """
        self.mouse_down(button)
        self.mouse_up(button)
        return

    def double_click_mouse(self, button):
        """
    Two full mouse clicks. One down event, one up event.
    """
        self.click_mouse(button)
        self.sleep(0.1)
        self.click_mouse(button)
        return

    def move_and_click(self, x, y, button):
        """convenience function: Move to corrdinate and click mouse"""
        self.set_mouse_pos(x, y)
        self.click_mouse(button)
        return

    def scroll_mouse_wheel(self, direction, clicks):
        """
    Scrolls the mouse wheel either up or down X number of 'clicks'

    direction: String: 'up' or 'down'

    clicks: int: how many times to click
    """
        for num in range(clicks):
            self._scrollup() if direction.lower() == 'up' else self._scrolldown()

        return

    def _scrollup(self):
        user32.mouse_event(self.win32con.WHEEL, None, None, 120, None)
        return

    def _scrolldown(self):
        user32.mouse_event(self.win32con.WHEEL, None, None, -120, None)
        return

    def get_clipboard_data(self):
        """
    Retrieves text from the Windows clipboard
    as a String
    """
        CF_TEXT = 1
        user32.OpenClipboard(None)
        hglb = user32.GetClipboardData(CF_TEXT)
        text_ptr = c_char_p(kernel32.GlobalLock(hglb))
        kernel32.GlobalUnlock(hglb)
        return text_ptr.value

    def add_to_clipboard(self, string):
        """
    Copy text into clip board for later pasting.
    """
        GHND = 66
        hGlobalMemory = kernel32.GlobalAlloc(GHND, len(bytes(string)) + 1)
        lpGlobalMemory = kernel32.GlobalLock(hGlobalMemory)
        lpGlobalMemory = kernel32.lstrcpy(lpGlobalMemory, string)
        kernel32.GlobalUnlock(lpGlobalMemory)
        user32.OpenClipboard(None)
        user32.EmptyClipboard()
        hClipMemory = user32.SetClipboardData(1, hGlobalMemory)
        user32.CloseClipboard()
        return

    def clear_clipboard(self):
        """
    Clear everything out of the clipboard
    """
        user32.OpenClipboard(None)
        user32.EmptyClipboard()
        user32.CloseClipboard()
        return

    def _get_monitor_coordinates(self):
        raise NotImplementedError('.. still working on things :)')
        return

    def take_screenshot(self, bounds=None):
        """
    NOTE:
      REQUIRES: PYTHON IMAGE LIBRARY

    Takes a snapshot of desktop and loads it into memory as a PIL object.

    TODO:
      * Add multimonitor support

    """
        try:
            from PIL import Image
        except ImportError as e:
            print e
            print 'Need to have PIL installed! See: effbot.org for download'
            sys.exit()

        return self._make_image_from_buffer(self._get_screen_buffer(bounds))

    def _get_screen_buffer(self, bounds=None):
        SM_XVIRTUALSCREEN = 76
        SM_YVIRTUALSCREEN = 77
        SM_CXVIRTUALSCREEN = 78
        SM_CYVIRTUALSCREEN = 79
        hDesktopWnd = user32.GetDesktopWindow()
        left = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
        top = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
        width = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
        height = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
        if bounds:
            left, top, right, bottom = bounds
            width = right - left
            height = bottom - top
        hDesktopDC = user32.GetWindowDC(hDesktopWnd)
        if not hDesktopDC:
            print 'GetDC Failed'
            sys.exit()
        hCaptureDC = gdi.CreateCompatibleDC(hDesktopDC)
        if not hCaptureDC:
            print 'CreateCompatibleBitmap Failed'
            sys.exit()
        hCaptureBitmap = gdi.CreateCompatibleBitmap(hDesktopDC, width, height)
        if not hCaptureBitmap:
            print 'CreateCompatibleBitmap Failed'
            sys.exit()
        gdi.SelectObject(hCaptureDC, hCaptureBitmap)
        SRCCOPY = 13369376
        gdi.BitBlt(hCaptureDC, 0, 0, width, height, hDesktopDC, left, top, 13369376)
        return hCaptureBitmap

    def _make_image_from_buffer(self, hCaptureBitmap):
        from PIL import Image
        bmp_info = BITMAPINFO()
        bmp_header = BITMAPFILEHEADER()
        hdc = user32.GetDC(None)
        bmp_info.bmiHeader.biSize = sizeof(BITMAPINFOHEADER)
        DIB_RGB_COLORS = 0
        gdi.GetDIBits(hdc, hCaptureBitmap, 0, 0, None, byref(bmp_info), DIB_RGB_COLORS)
        bmp_info.bmiHeader.biSizeImage = int(bmp_info.bmiHeader.biWidth * abs(bmp_info.bmiHeader.biHeight) * (bmp_info.bmiHeader.biBitCount + 7) / 8)
        size = (bmp_info.bmiHeader.biWidth, bmp_info.bmiHeader.biHeight)
        pBuf = (c_char * bmp_info.bmiHeader.biSizeImage)()
        gdi.GetBitmapBits(hCaptureBitmap, bmp_info.bmiHeader.biSizeImage, pBuf)
        return Image.frombuffer('RGB', size, pBuf, 'raw', 'BGRX', 0, 1)

    def press_and_release(self, key):
        """
    Simulates pressing a key: One down event, one release event.
    """
        self.key_press(key)
        self.key_release(key)
        return

    def key_press(self, key):
        """ Presses a given key. """
        KEY_PRESS = 0
        if isinstance(key, str):
            vk_code = self._vk_from_char(key)
        else:
            vk_code = key
        self._key_control(key=vk_code, action=KEY_PRESS)
        return

    def key_release(self, key):
        """ Releases a given key. """
        KEY_RELEASE = 2
        if isinstance(key, str):
            vk_code = self._vk_from_char(key)
        else:
            vk_code = key
        self._key_control(key=vk_code, action=KEY_RELEASE)
        return

    def _key_control(self, key, action):
        ip = INPUT()
        INPUT_KEYBOARD = 1
        ip.type = INPUT_KEYBOARD
        ip.ki.wScan = 0
        ip.ki.time = 0
        a = user32.GetMessageExtraInfo()
        b = cast(a, POINTER(c_ulong))
        ip.ki.wVk = key
        ip.ki.dwFlags = action
        user32.SendInput(1, byref(ip), sizeof(INPUT))
        return

    def _vk_from_char(self, key_char):
        try:
            return KeyConsts.key_mapping[key_char.lower()]
        except ValueError as e:
            print e
            print '\n\nUsage Note: all keys are underscore delimited, e.g. "left_mouse_button", or "up_arrow."\nView KeyConsts class for list of key_names'
            sys.exit()

        return

    def _capitalize(self, letter):
        self.key_press('shift')
        self.key_press(letter)
        self.key_release('shift')
        self.key_release(letter)
        return

    def alt_press(self, letter):
        self.key_press('alt')
        self.key_press(letter)
        self.key_release('alt')
        self.key_release(letter)
        return

    def ctrl_press(self, letter):
        self.key_press('ctrl')
        self.key_press(letter)
        self.key_release('ctrl')
        self.key_release(letter)
        return

    def _get_unshifted_key(self, key):
        return KeyConsts.special_map[key]

    def type_string(self, input_string, delay=0.005):
        """
    Convenience function for typing out strings.
    Delay controls the time between each letter.

    For the most part, large tests should be pushed
    into the clipboard and pasted where needed. However,
    they typing serves the useful purpose of looking neat.
    """
        for letter in input_string:
            self._handle_input(letter)
            time.sleep(delay)

        return

    def _handle_input(self, key):
        if ord(key) in range(65, 91):
            self._capitalize(key)
        elif key in KeyConsts.special_map.keys():
            normalized_key = KeyConsts.special_map[key]
            self._capitalize(normalized_key)
        else:
            self.key_press(key)
            self.key_release(key)
        return

    def type_backwards(self, input_string, delay=0.05):
        """
    Types right to left. Because why not!
    """
        for letter in reversed(input_string):
            self._handle_input(letter)
            self.key_press('left_arrow')
            self.key_release('left_arrow')
            time.sleep(delay)

        return

    def start_program(self, full_path):
        """
    Starts a windows applications. Currently, you must pass in
    the full path to the exe, otherwise it will fail.

    TODO:
      * return Handle to started program.
      * Search on program name
    """

        class STARTUPINFO(ctypes.Structure):
            _fields_ = [
             (
              'cb', c_ulong),
             (
              'lpReserved', POINTER(c_char)),
             (
              'lpDesktop', POINTER(c_char)),
             (
              'lpTitle', POINTER(c_char)),
             (
              'dwX', c_ulong),
             (
              'dwY', c_ulong),
             (
              'dwXSize', c_ulong),
             (
              'dwYSize', c_ulong),
             (
              'dwXCountChars', c_ulong),
             (
              'dwYCountChars', c_ulong),
             (
              'dwFillAttribute', c_ulong),
             (
              'dwFlags', c_ulong),
             (
              'wShowWindow', c_ushort),
             (
              'cbReserved2', c_ushort),
             (
              'lpReserved2', POINTER(c_ubyte)),
             (
              'hStdInput', c_void_p),
             (
              'hStdOutput', c_void_p),
             (
              'hStdError', c_void_p)]

        class PROCESS_INFORMATION(ctypes.Structure):
            _fields_ = [
             (
              'hProcess', c_void_p),
             (
              'hThread', c_void_p),
             (
              'dwProcessId', c_ulong),
             (
              'dwThreadId', c_ulong)]

        NORMAL_PRIORITY_CLASS = 32
        startupinfo = STARTUPINFO()
        processInformation = PROCESS_INFORMATION()
        kernel32.CreateProcessA(full_path, None, None, None, True, 0, None, None, byref(startupinfo), byref(processInformation))
        return

    def copy(self):
        """
    convenience function for issuing Ctrl+C copy command
    """
        self.key_press('ctrl')
        self.key_press('c')
        self.key_release('c')
        self.key_release('ctrl')
        return

    def paste(self):
        """
    convenience function for pasting whatever is in the clipboard
    """
        self.key_press('ctrl')
        self.key_press('v')
        self.key_release('v')
        self.key_release('ctrl')
        return

    def sleep(self, duration):
        """
    Pauses the robot for `duration` number of seconds.
    """
        time.sleep(duration)
        return

    def _enumerate_windows(self, visible=True):
        """
    Loops through the titles of all the "windows."
    Spits out too much junk to to be of immediate use.
    Keeping it here to remind me how the ctypes
    callbacks work.
    """
        titles = []
        handlers = []

        def worker(hwnd, lParam):
            length = user32.GetWindowTextLengthW(hwnd) + 1
            b = ctypes.create_unicode_buffer(length)
            user32.GetWindowTextW(hwnd, b, length)
            if visible and user32.IsWindowVisible(hwnd):
                title = b.value
                if title:
                    titles.append(title)
                    handlers.append(hwnd)
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(BOOL, HWND, LPARAM)
        if not user32.EnumWindows(WNDENUMPROC(worker), True):
            raise ctypes.WinError()
        else:
            return (
             handlers, titles)
        return

    def get_window_hwnd(self, wname):
        hwnd, win = self._enumerate_windows()
        for w in win:
            if wname.lower() in w.lower():
                return hwnd[win.index(w)]

        return

    def get_window_bounds(self):
        rect = RECT()
        user32.GetWindowRect(self.hwnd, ctypes.byref(rect))
        bbox = (rect.left, rect.top, rect.right, rect.bottom)
        return bbox

    def get_window_pos(self):
        x, y, right, bottom = self.get_window_bounds()
        return (x, y)

    pos = property(get_window_pos)

    def wait_for_window(self, wname, timeout=0, interval=0.005):
        if timeout < 0:
            raise ValueError("'timeout' must be a positive number")
        start_time = time.time()
        while True:
            for window in self._enumerate_windows()[1]:
                if wname.lower() in window.lower():
                    return self.get_window_hwnd(window)

            if time.time() - start_time > timeout:
                return False
            time.sleep(interval)

        return

    def get_display_monitors(self):
        """
    Enumerates and returns a list of virtual screen
    coordinates for the attached display devices

    output = [
      (left, top, right, bottom), # Monitor 1
      (left, top, right, bottom)  # Monitor 2
      # etc...
    ]

    """
        display_coordinates = []

        def _monitorEnumProc(hMonitor, hdcMonitor, lprcMonitor, dwData):
            coordinates = (
             lprcMonitor.contents.left,
             lprcMonitor.contents.top,
             lprcMonitor.contents.right,
             lprcMonitor.contents.bottom)
            display_coordinates.append(coordinates)
            return True

        MonitorEnumProc = WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HMONITOR, ctypes.wintypes.HDC, ctypes.POINTER(RECT), ctypes.wintypes.LPARAM)
        enum_callback = MonitorEnumProc(_monitorEnumProc)
        user32.EnumDisplayMonitors(None, None, enum_callback, 0)
        return display_coordinates

    def draw_box(self, location, rgb_value):
        p1_x, p1_y, p2_x, p2_y = location
        width = p2_x - p1_x
        height = p2_y - p1_y
        for pix in range(width):
            self.draw_pixel((p1_x + pix, p1_y), rgb_value)
            self.draw_pixel((p1_x + pix, p2_y), rgb_value)
            self.draw_pixel((p1_x + pix, p1_y - 1), rgb_value)
            self.draw_pixel((p1_x + pix, p2_y + 1), rgb_value)

        for i in range(height):
            self.draw_pixel((p1_x, p1_y + i), rgb_value)
            self.draw_pixel((p2_x, p1_y + i), rgb_value)
            self.draw_pixel((p1_x - 1, p1_y + i), rgb_value)
            self.draw_pixel((p2_x + 1, p1_y + i), rgb_value)

        return

    def draw_pixel(self, coordinate, rgb_value):
        """
    Draw pixels on the screen.

    Eventual plan is to use this to draw bounding boxes for template matching.
    Idea is to have it seek out anything that looks vaguely like a text-box
    (or something). Who knows.

    """

        def _convert_rgb(r, g, b):
            r = r & 255
            g = g & 255
            b = b & 255
            return b << 16 | g << 8 | r

        rgb = _convert_rgb(*rgb_value)
        hdc = user32.GetDC(None)
        x, y = coordinate
        gdi.SetPixel(hdc, c_int(x), c_int(y), rgb)
        return


return

# okay decompiling AQTEServer.exe_extracted/PYZ-00.pyz_extracted/pyrobot.pyc
