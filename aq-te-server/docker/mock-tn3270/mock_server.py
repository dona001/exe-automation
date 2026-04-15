"""
Mock TN3270 Server for local testing.

Uses proper telnet negotiation that s3270 expects.
Simulates a basic IBM mainframe with login screen and menus.
"""
import socket
import threading
import time
import sys
import struct

# ============================================================================
# TN3270 Protocol Constants
# ============================================================================

# Telnet commands
IAC  = 0xFF
DONT = 0xFE
DO   = 0xFD
WONT = 0xFC
WILL = 0xFB
SB   = 0xFA
SE   = 0xF0
EOR  = 0xEF

# Telnet options
OPT_BINARY  = 0x00
OPT_EOR     = 0x19
OPT_TTYPE   = 0x18
OPT_TN3270E = 0x28

# 3270 commands
CMD_ERASE_WRITE       = 0xF5
CMD_ERASE_WRITE_ALT   = 0x7E
CMD_WRITE             = 0xF1

# 3270 orders
ORDER_SBA = 0x11  # Set Buffer Address
ORDER_SF  = 0x1D  # Start Field
ORDER_SA  = 0x28  # Set Attribute
ORDER_IC  = 0x13  # Insert Cursor

# WCC (Write Control Character)
WCC_RESET_MDT = 0x40
WCC_KEYBOARD_RESTORE = 0x02
WCC_RESET_MODIFIED = 0x01

# AID bytes
AID_ENTER = 0x7D
AID_PF1   = 0xF1
AID_PF2   = 0xF2
AID_PF3   = 0xF3
AID_PF4   = 0xF4
AID_PF5   = 0xF5
AID_PF6   = 0xF6
AID_PF7   = 0xF7
AID_PF8   = 0xF8
AID_PF9   = 0xF9
AID_PF10  = 0x7A
AID_PF11  = 0x7B
AID_PF12  = 0x7C
AID_CLEAR = 0x6D

# Field attributes
FA_PROTECT          = 0x20
FA_NUMERIC          = 0x10
FA_DISPLAY_NOT_SEL  = 0x00
FA_DISPLAY_NOT_PEN  = 0x04
FA_INTENSIFIED      = 0x08
FA_HIDDEN           = 0x0C
FA_MDT              = 0x01

ROWS = 24
COLS = 80


# ============================================================================
# EBCDIC / Address encoding
# ============================================================================

_a2e_table = [0] * 256
_e2a_table = [0] * 256

def _init_tables():
    pairs = [
        (0x20, 0x40),  # space
        (0x2E, 0x4B), (0x3C, 0x4C), (0x28, 0x4D), (0x2B, 0x4E),
        (0x26, 0x50), (0x21, 0x5A), (0x24, 0x5B), (0x2A, 0x5C),
        (0x29, 0x5D), (0x3B, 0x5E), (0x2D, 0x60), (0x2F, 0x61),
        (0x2C, 0x6B), (0x25, 0x6C), (0x5F, 0x6D), (0x3E, 0x6E),
        (0x3F, 0x6F), (0x3A, 0x7A), (0x23, 0x7B), (0x40, 0x7C),
        (0x27, 0x7D), (0x3D, 0x7E), (0x22, 0x7F),
    ]
    for i in range(10):
        pairs.append((0x30 + i, 0xF0 + i))
    for i in range(9):
        pairs.append((0x41 + i, 0xC1 + i))  # A-I
        pairs.append((0x61 + i, 0xC1 + i))  # a-i
    for i in range(9):
        pairs.append((0x4A + i, 0xD1 + i))  # J-R
        pairs.append((0x6A + i, 0xD1 + i))  # j-r
    for i in range(8):
        pairs.append((0x53 + i, 0xE2 + i))  # S-Z
        pairs.append((0x73 + i, 0xE2 + i))  # s-z

    for a, e in pairs:
        _a2e_table[a] = e
        _e2a_table[e] = a

_init_tables()


def to_ebcdic(text):
    return bytes([_a2e_table[ord(c)] if ord(c) < 256 else 0x40 for c in text])


def from_ebcdic(data):
    return ''.join(chr(_e2a_table[b]) if _e2a_table[b] else ' ' for b in data)


def encode_ba(pos):
    """Encode buffer address in 14-bit format (for model 2: 24x80 = 1920 < 4096)."""
    # Use 14-bit encoding
    return bytes([(pos >> 8) & 0x3F, pos & 0xFF])


def decode_ba(b1, b2):
    """Decode a 14-bit or 12-bit buffer address."""
    # Check if 12-bit (high bits of both bytes are in the 6-bit coded range)
    _6bit = [
        0x40, 0xC1, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7,
        0xC8, 0xC9, 0x4A, 0x4B, 0x4C, 0x4D, 0x4E, 0x4F,
        0x50, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7,
        0xD8, 0xD9, 0x5A, 0x5B, 0x5C, 0x5D, 0x5E, 0x5F,
        0x60, 0x61, 0xE2, 0xE3, 0xE4, 0xE5, 0xE6, 0xE7,
        0xE8, 0xE9, 0x6A, 0x6B, 0x6C, 0x6D, 0x6E, 0x6F,
        0xF0, 0xF1, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF7,
        0xF8, 0xF9, 0x7A, 0x7B, 0x7C, 0x7D, 0x7E, 0x7F,
    ]
    if b1 in _6bit and b2 in _6bit:
        return (_6bit.index(b1) << 6) | _6bit.index(b2)
    # 14-bit
    return ((b1 & 0x3F) << 8) | b2


# ============================================================================
# Screen Builder
# ============================================================================

class ScreenBuilder:
    """Build a 3270 data stream."""

    def __init__(self):
        self.buf = bytearray()

    def text_at(self, row, col, text, protected=True, intensified=False, hidden=False):
        """Place text at row,col with a field attribute before it."""
        pos = (row - 1) * COLS + (col - 1)
        # Position before the field attribute
        if pos > 0:
            attr_pos = pos - 1
        else:
            attr_pos = 0
        self.buf += bytes([ORDER_SBA]) + encode_ba(attr_pos)

        # Field attribute
        fa = 0
        if protected:
            fa |= FA_PROTECT
        if intensified:
            fa |= FA_INTENSIFIED
        if hidden:
            fa |= FA_HIDDEN
        # Encode FA: 0xC0 base + attribute bits
        fa_byte = 0xC0 | (fa & 0x3F)
        self.buf += bytes([ORDER_SF, fa_byte])

        # Text content
        self.buf += to_ebcdic(text)
        return self

    def input_at(self, row, col, length, hidden=False):
        """Place an unprotected input field at row,col."""
        pos = (row - 1) * COLS + (col - 1)
        attr_pos = pos - 1 if pos > 0 else 0
        self.buf += bytes([ORDER_SBA]) + encode_ba(attr_pos)

        fa = 0  # unprotected
        if hidden:
            fa |= FA_HIDDEN
        fa_byte = 0xC0 | (fa & 0x3F)
        self.buf += bytes([ORDER_SF, fa_byte])

        # Null fill the field
        self.buf += bytes([0x00] * length)

        # End with a protected field attribute
        end_pos = (row - 1) * COLS + (col - 1) + length
        if end_pos < ROWS * COLS:
            self.buf += bytes([ORDER_SF, 0xE0])  # protected
        return self

    def cursor_at(self, row, col):
        """Set cursor position."""
        pos = (row - 1) * COLS + (col - 1)
        self.buf += bytes([ORDER_SBA]) + encode_ba(pos)
        self.buf += bytes([ORDER_IC])
        return self

    def build(self):
        """Return complete erase/write data stream."""
        wcc = WCC_KEYBOARD_RESTORE | WCC_RESET_MODIFIED
        return bytes([CMD_ERASE_WRITE, 0xC0 | wcc]) + bytes(self.buf)


# ============================================================================
# Screen Definitions
# ============================================================================

def login_screen():
    s = ScreenBuilder()
    s.text_at(1, 25, "IBM MOCK MAINFRAME SYSTEM")
    s.text_at(2, 25, "========================")
    s.text_at(4, 10, "APPLICATION: MOCK3270 V1.0")
    s.text_at(6, 10, "WELCOME TO THE MOCK TN3270 SERVER")
    s.text_at(7, 10, "THIS IS A TEST ENVIRONMENT FOR AUTOMATION")
    s.text_at(9, 10, "LOGON ===>")
    s.text_at(11, 10, "USERID  ===>")
    s.input_at(11, 23, 8)
    s.text_at(12, 10, "PASSWORD ===>")
    s.input_at(12, 24, 8, hidden=True)
    s.text_at(14, 10, "ENTER USERID AND PASSWORD, THEN PRESS ENTER")
    s.text_at(20, 10, "*** FOR TESTING PURPOSES ONLY ***")
    s.text_at(24, 2, "MOCK3270")
    s.cursor_at(11, 23)
    return s.build()


def main_menu():
    s = ScreenBuilder()
    s.text_at(1, 25, "MOCK MAINFRAME - MAIN MENU")
    s.text_at(2, 25, "==========================")
    s.text_at(4, 10, "SELECT OPTION:")
    s.text_at(6, 14, "1  ISPF      - INTERACTIVE SYSTEM PRODUCTIVITY FACILITY")
    s.text_at(7, 14, "2  TSO       - TIME SHARING OPTION")
    s.text_at(8, 14, "3  CICS      - CUSTOMER INFORMATION CONTROL SYSTEM")
    s.text_at(9, 14, "4  STATUS    - SYSTEM STATUS")
    s.text_at(10, 14, "5  LOGOFF    - DISCONNECT")
    s.text_at(12, 10, "OPTION ===>")
    s.input_at(12, 22, 10)
    s.text_at(14, 10, "USERID: TESTUSER    SYSTEM: MOCK3270")
    s.text_at(24, 2, "READY")
    s.cursor_at(12, 22)
    return s.build()


def ispf_screen():
    s = ScreenBuilder()
    s.text_at(1, 10, "ISPF Primary Option Menu")
    s.text_at(2, 10, "========================")
    s.text_at(4, 14, "0  SETTINGS  - TERMINAL AND USER PARAMETERS")
    s.text_at(5, 14, "1  VIEW      - DISPLAY SOURCE DATA")
    s.text_at(6, 14, "2  EDIT      - CREATE OR CHANGE SOURCE DATA")
    s.text_at(7, 14, "3  UTILITIES - PERFORM UTILITY FUNCTIONS")
    s.text_at(9, 10, "OPTION ===>")
    s.input_at(9, 22, 10)
    s.text_at(24, 2, "F3=EXIT")
    s.cursor_at(9, 22)
    return s.build()


def tso_screen():
    s = ScreenBuilder()
    s.text_at(1, 10, "TSO COMMAND PROCESSOR")
    s.text_at(2, 10, "====================")
    s.text_at(4, 10, "READY")
    s.text_at(6, 10, "ENTER TSO COMMAND:")
    s.text_at(8, 10, "===>")
    s.input_at(8, 15, 60)
    s.text_at(24, 2, "F3=EXIT")
    s.cursor_at(8, 15)
    return s.build()


def status_screen():
    s = ScreenBuilder()
    s.text_at(1, 10, "SYSTEM STATUS")
    s.text_at(2, 10, "=============")
    s.text_at(4, 10, "SYSTEM:    MOCK3270")
    s.text_at(5, 10, "STATUS:    ACTIVE")
    s.text_at(6, 10, "USERS:     1")
    s.text_at(7, 10, "CPU:       12 PERCENT")
    s.text_at(8, 10, "MEMORY:    45 PERCENT")
    s.text_at(9, 10, "UPTIME:    3 DAYS 12:45:00")
    s.text_at(11, 10, "READY")
    s.text_at(24, 2, "F3=EXIT")
    return s.build()


def logoff_screen():
    s = ScreenBuilder()
    s.text_at(1, 25, "IBM MOCK MAINFRAME SYSTEM")
    s.text_at(4, 10, "SESSION ENDED")
    s.text_at(6, 10, "THANK YOU FOR USING MOCK3270")
    s.text_at(8, 10, "LOGON ===>")
    s.input_at(8, 21, 20)
    s.cursor_at(8, 21)
    return s.build()


# ============================================================================
# TN3270 Connection Handler
# ============================================================================

class TN3270Handler:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.screen = "login"

    def handle(self):
        print(f"[MOCK] New connection from {self.addr}", flush=True)
        try:
            self._negotiate()
            time.sleep(0.3)
            self._send_3270(login_screen())
            self._main_loop()
        except (ConnectionResetError, BrokenPipeError, OSError) as e:
            print(f"[MOCK] Connection error: {e}", flush=True)
        finally:
            print(f"[MOCK] Closed {self.addr}", flush=True)
            try:
                self.conn.close()
            except:
                pass

    def _negotiate(self):
        """Perform TN3270 telnet option negotiation."""
        # We need to negotiate: BINARY, EOR, TERMINAL-TYPE
        # s3270 expects: server WILL BINARY, DO BINARY, WILL EOR, DO EOR

        # Send our WILL/DO offers
        offers = bytearray()
        offers += bytes([IAC, DO, OPT_BINARY])
        offers += bytes([IAC, WILL, OPT_BINARY])
        offers += bytes([IAC, DO, OPT_EOR])
        offers += bytes([IAC, WILL, OPT_EOR])
        offers += bytes([IAC, DO, OPT_TTYPE])
        self.conn.sendall(offers)

        # Read client responses (with timeout)
        self.conn.settimeout(5.0)
        buf = bytearray()
        deadline = time.time() + 3.0
        while time.time() < deadline:
            try:
                chunk = self.conn.recv(4096)
                if not chunk:
                    break
                buf.extend(chunk)
                # Check if we've received enough negotiation
                # We need at least WILL BINARY, DO BINARY, WILL EOR, DO EOR from client
                will_count = sum(1 for i in range(len(buf)-2)
                                if buf[i] == IAC and buf[i+1] in (WILL, DO))
                if will_count >= 4:
                    break
            except socket.timeout:
                break

        # Handle terminal type subnegotiation if client sent WILL TTYPE
        if bytes([IAC, WILL, OPT_TTYPE]) in buf:
            # Request terminal type
            self.conn.sendall(bytes([IAC, SB, OPT_TTYPE, 0x01, IAC, SE]))
            try:
                self.conn.settimeout(2.0)
                ttype_resp = self.conn.recv(4096)
                # We don't really care what type they send
            except socket.timeout:
                pass

        self.conn.settimeout(30.0)
        print(f"[MOCK] Negotiation complete for {self.addr}", flush=True)

    def _send_3270(self, data):
        """Send 3270 data stream with IAC EOR terminator."""
        # Escape any 0xFF in the data
        escaped = bytearray()
        for b in data:
            escaped.append(b)
            if b == 0xFF:
                escaped.append(0xFF)
        escaped += bytes([IAC, EOR])
        self.conn.sendall(escaped)

    def _recv_3270(self):
        """Receive 3270 data stream (until IAC EOR)."""
        buf = bytearray()
        self.conn.settimeout(60.0)
        while True:
            try:
                chunk = self.conn.recv(4096)
                if not chunk:
                    return None
                buf.extend(chunk)

                # Look for IAC EOR
                idx = 0
                while idx < len(buf) - 1:
                    if buf[idx] == IAC:
                        if buf[idx + 1] == EOR:
                            # Found end of record
                            data = bytes(buf[:idx])
                            return data
                        elif buf[idx + 1] == IAC:
                            # Escaped 0xFF, remove one
                            del buf[idx]
                            idx += 1
                        elif buf[idx + 1] in (DO, DONT, WILL, WONT):
                            # Telnet negotiation in-band, skip 3 bytes
                            if idx + 2 < len(buf):
                                del buf[idx:idx+3]
                            else:
                                break
                        else:
                            idx += 1
                    else:
                        idx += 1
            except socket.timeout:
                return None

    def _parse_input(self, data):
        """Parse 3270 input data stream. Returns (aid, cursor_pos, fields)."""
        if not data or len(data) < 3:
            return ("NONE", 0, {})

        aid = data[0]
        cursor_pos = decode_ba(data[1], data[2])

        # Parse SBA + field data pairs
        fields = {}
        i = 3
        current_pos = None
        field_data = bytearray()

        while i < len(data):
            if data[i] == ORDER_SBA and i + 2 < len(data):
                # Save previous field
                if current_pos is not None:
                    fields[current_pos] = from_ebcdic(field_data).strip()
                current_pos = decode_ba(data[i+1], data[i+2])
                field_data = bytearray()
                i += 3
            else:
                if current_pos is not None:
                    field_data.append(data[i])
                i += 1

        # Save last field
        if current_pos is not None:
            fields[current_pos] = from_ebcdic(field_data).strip()

        aid_names = {
            AID_ENTER: "ENTER", AID_CLEAR: "CLEAR",
            AID_PF1: "PF1", AID_PF2: "PF2", AID_PF3: "PF3",
            AID_PF4: "PF4", AID_PF5: "PF5", AID_PF6: "PF6",
            AID_PF7: "PF7", AID_PF8: "PF8", AID_PF9: "PF9",
            AID_PF10: "PF10", AID_PF11: "PF11", AID_PF12: "PF12",
        }
        aid_name = aid_names.get(aid, f"0x{aid:02X}")
        return (aid_name, cursor_pos, fields)

    def _main_loop(self):
        """Main interaction loop."""
        while True:
            data = self._recv_3270()
            if data is None:
                break

            aid, cursor, fields = self._parse_input(data)
            # Collect all field text
            all_text = " ".join(fields.values()).upper()
            print(f"[MOCK] screen={self.screen} aid={aid} text='{all_text}' fields={fields}", flush=True)

            # Route based on current screen + input
            next_screen = self._route(aid, all_text)
            self._send_3270(next_screen)

    def _route(self, aid, text):
        """Determine next screen based on current state and input."""
        # PF3 = back/exit from any screen
        if aid == "PF3":
            if self.screen in ("ispf", "tso", "status", "cics"):
                self.screen = "main"
                return main_menu()
            elif self.screen == "main":
                self.screen = "logoff"
                return logoff_screen()

        # CLEAR = refresh current screen
        if aid == "CLEAR":
            return self._current()

        # Screen-specific routing
        if self.screen == "login" or self.screen == "logoff":
            if aid == "ENTER":
                self.screen = "main"
                return main_menu()

        elif self.screen == "main":
            if aid == "ENTER":
                if "1" in text or "ISPF" in text:
                    self.screen = "ispf"
                    return ispf_screen()
                elif "2" in text or "TSO" in text:
                    self.screen = "tso"
                    return tso_screen()
                elif "4" in text or "STATUS" in text:
                    self.screen = "status"
                    return status_screen()
                elif "5" in text or "LOGOFF" in text:
                    self.screen = "logoff"
                    return logoff_screen()
                return main_menu()

        elif self.screen in ("ispf", "tso", "status"):
            return self._current()

        return self._current()

    def _current(self):
        screens = {
            "login": login_screen,
            "main": main_menu,
            "ispf": ispf_screen,
            "tso": tso_screen,
            "status": status_screen,
            "logoff": logoff_screen,
        }
        return screens.get(self.screen, login_screen)()


# ============================================================================
# Server
# ============================================================================

def start_server(host="0.0.0.0", port=3270):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)
    print(f"[MOCK] TN3270 server listening on {host}:{port}", flush=True)

    try:
        while True:
            conn, addr = server.accept()
            t = threading.Thread(target=TN3270Handler(conn, addr).handle, daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("[MOCK] Shutting down", flush=True)
    finally:
        server.close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3270
    start_server(port=port)
