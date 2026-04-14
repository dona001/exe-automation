# 3270 Terminal Automation Server (Docker)

REST API server for automating IBM 3270 mainframe terminals. Runs in Docker — no Windows, no GUI, no emulator installation needed on the client side.

## Quick Start

### 1. Configure your mainframe connection

```bash
# Edit the session file with your mainframe host
echo "host=your-mainframe-host:23" > sessions/default.txt
```

### 2. Start the server

```bash
docker compose up --build -d
```

The server starts on port `9995` and auto-connects to all hosts defined in `sessions/*.txt`.

### 3. Verify it's running

```bash
curl http://localhost:9995/te/ping
curl http://localhost:9995/te/status
```

### 4. Start automating

```bash
# Read the screen
curl -X POST http://localhost:9995/te/screentext \
  -H "Content-Type: application/json" -d '{}'

# Type something + Enter
curl -X POST http://localhost:9995/te/sendkeys \
  -H "Content-Type: application/json" -d '{"text": "LOGON MYUSER"}'
```

## API Reference

All POST endpoints accept JSON body. Common fields:
- `sname` — session name (defaults to `"default"`)

### Session Management

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| GET | `/te/ping` | — | Health check |
| GET | `/te/status` | — | List all sessions and their status |
| POST | `/te/init` | `{}` | Initialize (no-op, for compatibility) |
| POST | `/te/startsession` | `{"path":"sessions/x.txt","sname":"default"}` | Start a new session |
| POST | `/te/disconnect` | `{"sname":"default"}` | Disconnect a session |

### Screen Reading

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| POST | `/te/screentext` | `{}` | Get full screen (24 rows × 80 cols) |
| POST | `/te/fieldtext_by_row_col` | `{"row":5,"col":10,"length":20}` | Read text at position |
| POST | `/te/search` | `{"text":"READY"}` | Find text on screen (returns row/col) |

### Input

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| POST | `/te/sendkeys` | `{"text":"CMD"}` | Type text + press Enter |
| POST | `/te/sendkeysnoreturn` | `{"text":"CMD"}` | Type text without Enter |
| POST | `/te/entertext_by_row_col` | `{"text":"VAL","row":10,"col":20}` | Type into field at position |
| POST | `/te/clear_text_by_row_col` | `{"row":10,"col":20}` | Clear field at position |

### Special Keys

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| POST | `/te/send_special_key` | `{"key":"enter"}` | Send special key |
| POST | `/te/clearscreen` | `{}` | Send Clear key |

Supported keys: `enter`, `tab`, `clear`, `f1`–`f24`, `pa1`–`pa12`, `backspace`, `delete`, `home`, `insert`, `newline`, `reset`, `erase-line`

### Navigation

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| POST | `/te/moveto` | `{"row":5,"col":10}` | Move cursor |
| POST | `/te/pause` | `{"time":2}` | Wait N seconds |
| POST | `/te/exec` | `{"cmd":"PF(3)"}` | Execute raw s3270 command |

## Multiple Sessions

You can run multiple sessions simultaneously:

```bash
echo "host=mainframe-a:23" > sessions/prod.txt
echo "host=mainframe-b:23" > sessions/dev.txt
```

Then target them by name:

```bash
curl -X POST http://localhost:9995/te/screentext \
  -H "Content-Type: application/json" -d '{"sname": "prod"}'
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TE_PORT` | `9995` | Server port |
| `AUTO_CONNECT_DIR` | — | Directory of `.txt` session files to auto-connect on startup |

## Client Examples

See `client_example.py` for Python examples covering login, navigation, search, and batch automation.

```bash
pip install requests
python client_example.py
```
