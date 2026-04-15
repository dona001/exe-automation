# EXE Automation — IBM 3270 Terminal Automation Suite

This project was born from reverse engineering a PyInstaller-bundled Windows EXE (`AQTEServer.exe`) that automated IBM 3270 mainframe terminals. The recovered Python source was then rewritten as a modern, Dockerized, cross-platform solution.

## Project Structure

```
├── docker-te-server/           # Dockerized TE Server + Mock Mainframe
│   ├── app.py                  # Flask REST API (rewritten from decompiled source)
│   ├── Dockerfile
│   ├── docker-compose.yml      # TE Server + Mock IBM Mainframe
│   ├── mock-tn3270/            # Mock TN3270 mainframe for local testing
│   │   ├── mock_server.py
│   │   └── Dockerfile
│   ├── sessions/               # Session config files (host=mainframe:port)
│   ├── client_example.py       # Python client examples
│   ├── requirements.txt
│   └── README.md               # API reference
│
├── playwright-te-tests/        # Playwright test integration
│   ├── lib/
│   │   ├── te-client.ts        # Typed TypeScript client for the TE API
│   │   └── te-fixture.ts       # Playwright fixture (auto Docker lifecycle)
│   ├── tests/
│   │   ├── ibm-login.spec.ts   # Login flow test cases
│   │   └── ibm-cics.spec.ts    # CICS transaction test cases
│   ├── playwright.config.ts
│   └── package.json
│
├── run-tests.sh                # Shell test runner (18 tests, 31 assertions)
└── README.md                   # This file
```

## Quick Start

```bash
# Run the full test suite (starts Docker, runs tests, tears down)
./run-tests.sh
```

That's it. No IBM mainframe needed — a mock TN3270 server runs locally in Docker.

---

## Reverse Engineering PyInstaller EXE to Python Source Code

This section documents how `AQTEServer.exe` (a PyInstaller-bundled Python 2.7 application) was decompiled back to readable Python source code.

> This process applies to recovering source from your own applications or
> applications you have legal authorization to analyze. Always respect
> software licenses and applicable laws.

### Step 1: Identify the EXE Type

First, determine what kind of executable you're dealing with:

```bash
file AQTEServer.exe
# Output: PE32 executable (console) Intel 80386, for MS Windows

strings AQTEServer.exe | grep -i "python\|pyinstaller\|Py_SetPythonHome"
# If you see references to Python, PyInstaller, or Py_SetPythonHome,
# it's a Python application bundled with PyInstaller.
```

Key indicators that an EXE is a PyInstaller bundle:
- References to `Py_SetPythonHome`, `pyiboot01_bootstrap`, `pyi_rth_` in strings output
- Large file size relative to what the app does (Python runtime is bundled in)
- References to `distutils`, `importlib`, or Python standard library modules

### Step 2: Extract the PyInstaller Archive

PyInstaller bundles Python bytecode (`.pyc` files) into the EXE. Extract them using `pyinstxtractor-ng`:

```bash
pip install pyinstxtractor-ng
pyinstxtractor-ng AQTEServer.exe
```

Output:
```
[+] Processing AQTEServer.exe
[+] Pyinstaller version: 2.1+
[+] Python version: 2.7
[+] Length of package: 36330830 bytes
[+] Found 964 files in CArchive
[+] Beginning extraction...please standby
[+] Possible entry point: AQTEServer.pyc      <-- main script
[+] Found 962 files in PYZ archive
[+] Successfully extracted pyinstaller archive: AQTEServer.exe
```

This creates a directory `AQTEServer.exe_extracted/` containing:
- `AQTEServer.pyc` — the main entry point bytecode
- `PYZ-00.pyz_extracted/` — all bundled Python modules as `.pyc` files
- Various runtime `.pyc` files (`pyiboot01_bootstrap.pyc`, etc.)

### Step 3: Identify the Application Modules

The extracted directory contains both your application code and standard library modules. Find the custom ones:

```bash
# The main entry point
ls AQTEServer.exe_extracted/*.pyc

# Custom modules inside the PYZ archive
ls AQTEServer.exe_extracted/PYZ-00.pyz_extracted/ | grep -v "^_"
```

In this case, the custom application modules were:
- `AQTEServer.pyc` — main Flask server
- `AQTEAPI.pyc` — terminal emulator API wrapper
- `X3270API.pyc` — x3270 protocol handler
- `pyrobot.pyc` — GUI automation (keyboard/mouse)

### Step 4: Decompile .pyc to .py

Use `uncompyle6` for Python 2.7 bytecode, or `decompyle3` / `pycdc` for Python 3.x:

```bash
# For Python 2.7 bytecode
pip install uncompyle6

# Decompile the main entry point
uncompyle6 AQTEServer.exe_extracted/AQTEServer.pyc > AQTEServer.py

# Decompile custom modules from the PYZ archive
uncompyle6 AQTEServer.exe_extracted/PYZ-00.pyz_extracted/AQTEAPI.pyc > AQTEAPI.py
uncompyle6 AQTEServer.exe_extracted/PYZ-00.pyz_extracted/X3270API.pyc > X3270API.py
uncompyle6 AQTEServer.exe_extracted/PYZ-00.pyz_extracted/pyrobot.pyc > pyrobot.py
```

For Python 3.9+ bytecode (where `uncompyle6` may not work):

```bash
# Option A: decompyle3 (fork of uncompyle6 with Python 3.8+ support)
pip install decompyle3
decompyle3 module.pyc > module.py

# Option B: pycdc (C++ based, supports latest Python versions)
# Build from source: https://github.com/zrax/pycdc
git clone https://github.com/zrax/pycdc.git
cd pycdc && cmake . && make
./pycdc module.pyc > module.py
```

### Step 5: Verify the Decompiled Code

The decompiled output includes a header showing the decompiler version and original Python version:

```python
# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.10.0
# Embedded file name: AQTEServer.py
from flask import *
from AQTEAPI import AQTEAPI
...
```

Check the code compiles and makes sense:

```bash
# Syntax check (won't catch runtime errors, but validates structure)
python3 -c "import ast; ast.parse(open('AQTEServer.py').read()); print('OK')"
```

### Tool Reference

| Tool | Python Version | Install | Use Case |
|------|---------------|---------|----------|
| `pyinstxtractor-ng` | Any | `pip install pyinstxtractor-ng` | Extract `.pyc` files from PyInstaller EXE |
| `uncompyle6` | 2.6 — 3.8 | `pip install uncompyle6` | Decompile `.pyc` → `.py` |
| `decompyle3` | 3.7 — 3.8 | `pip install decompyle3` | Fork of uncompyle6 for Python 3 |
| `pycdc` | 1.0 — 3.12+ | Build from source | C++ decompiler, broadest version support |
| `unpy2exe` | 2.x | `pip install unpy2exe` | Extract from `py2exe` bundles (not PyInstaller) |
| `pycdas` | Any | Comes with `pycdc` | Disassemble `.pyc` to bytecode (when decompile fails) |

### What About Non-Python EXEs?

Not all executables can be decompiled to readable source. Here's a quick guide:

| EXE Type | How to Identify | Can You Get Source? |
|----------|----------------|-------------------|
| PyInstaller (Python) | `strings exe \| grep Py_SetPythonHome` | Yes — full Python source recovery |
| py2exe (Python) | `strings exe \| grep py2exe` | Yes — similar process with `unpy2exe` |
| cx_Freeze (Python) | `strings exe \| grep cx_Freeze` | Yes — extract and decompile `.pyc` files |
| Nuitka (Python) | `strings exe \| grep nuitka` | Partial — compiles to C, harder to recover |
| .NET (C#/VB) | `strings exe \| grep mscoree.dll` | Yes — use `ILSpy`, `dnSpy`, or `dotPeek` |
| Java JAR | `file exe` shows Java archive | Yes — use `JD-GUI`, `CFR`, or `Procyon` |
| Electron (JS) | Large size, `strings exe \| grep electron` | Yes — extract `app.asar` with `asar extract` |
| Go | `strings exe \| grep "go.buildid"` | Partial — use `Ghidra` with Go plugin |
| Rust | `strings exe \| grep "rust"` | Partial — use `Ghidra` or `IDA Pro` |
| Native C/C++ | MinGW/MSVC/GCC signatures in strings | Assembly only — use `Ghidra`, `IDA Pro`, or `Binary Ninja` |

### Limitations

- Decompiled code may have minor formatting differences from the original
- Variable names in optimized bytecode may be lost (shown as generic names)
- Some complex constructs (decorators, generators) may not decompile perfectly
- Comments and docstrings from the original source are not preserved in `.pyc` files
- Obfuscated Python (using tools like PyArmor) may resist decompilation

---

## License

This project is for educational and authorized reverse engineering purposes only.
