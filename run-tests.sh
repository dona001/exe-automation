#!/bin/bash
# =============================================================================
#
#  IBM 3270 Terminal Automation — End-to-End Test Suite
#
#  This script:
#    1. Builds & starts a Mock IBM Mainframe (TN3270) + TE REST API in Docker
#    2. Runs 18 test cases covering the full automation API surface
#    3. Tears everything down and writes a timestamped log file
#
#  Usage:
#    ./run-tests.sh              # run with console + log output
#    ./run-tests.sh --quiet      # log file only, minimal console
#
#  Requirements: docker, curl, python3
#
# =============================================================================

set -e

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL="http://localhost:9995"
DOCKER_DIR="docker-te-server"
SESSION="autotest"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_DIR="test-logs"
LOG_FILE="$LOG_DIR/test-run-${TIMESTAMP}.log"
QUIET=false

PASS=0
FAIL=0
TOTAL=0
START_TIME=$(python3 -c "import time; print(time.time())")

# Colors (console only)
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
DIM="\033[2m"
BOLD="\033[1m"
NC="\033[0m"

# Parse args
if [ "$1" = "--quiet" ]; then
  QUIET=true
fi

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

mkdir -p "$LOG_DIR"

# Strip ANSI codes for log file
strip_ansi() {
  sed 's/\x1b\[[0-9;]*m//g'
}

# Write to both console and log
out() {
  if [ "$QUIET" = false ]; then
    echo -e "$1"
  fi
  echo -e "$1" | strip_ansi >> "$LOG_FILE"
}

# Write to log only
log_only() {
  echo -e "$1" | strip_ansi >> "$LOG_FILE"
}

# Section header
section() {
  out ""
  out "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  out "${CYAN}  $1${NC}"
  out "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Info log
log_info() {
  local ts
  ts=$(date +"%H:%M:%S")
  out "  ${DIM}[$ts]${NC} ${CYAN}INFO${NC}  $1"
}

# Test case header
tc_header() {
  out ""
  out "  ${YELLOW}${BOLD}$1${NC}"
}

# Pass assertion
pass() {
  local ts
  ts=$(date +"%H:%M:%S")
  out "    ${GREEN}✓${NC} $1"
  log_only "    [$ts] PASS: $1"
  PASS=$((PASS+1))
  TOTAL=$((TOTAL+1))
}

# Fail assertion
fail() {
  local ts
  ts=$(date +"%H:%M:%S")
  out "    ${RED}✗${NC} $1"
  if [ -n "$2" ]; then
    out "      ${DIM}→ $2${NC}"
    log_only "    [$ts] FAIL: $1 | Detail: $2"
  else
    log_only "    [$ts] FAIL: $1"
  fi
  FAIL=$((FAIL+1))
  TOTAL=$((TOTAL+1))
}

# Log raw API response
log_api() {
  local endpoint="$1"
  local resp="$2"
  log_only "    [API] $endpoint → $resp"
}

# Log screen content
log_screen() {
  local label="$1"
  local screen="$2"
  log_only ""
  log_only "    ┌── $label ──"
  echo "$screen" | while IFS= read -r line; do
    log_only "    │ $line"
  done
  log_only "    └──"
  log_only ""
}

# ---------------------------------------------------------------------------
# API Helpers
# ---------------------------------------------------------------------------

api_post() {
  local endpoint="$1"
  local body="$2"
  local resp
  resp=$(curl -s -X POST "$BASE_URL/te/$endpoint" \
    -H "Content-Type: application/json" \
    -d "$body" 2>/dev/null)
  log_api "POST /te/$endpoint" "$resp"
  echo "$resp"
}

api_get() {
  local endpoint="$1"
  local resp
  resp=$(curl -s "$BASE_URL/te/$endpoint" 2>/dev/null)
  log_api "GET /te/$endpoint" "$resp"
  echo "$resp"
}

check_status() {
  echo "$1" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])" 2>/dev/null
}

get_error() {
  echo "$1" | python3 -c "import sys,json; print(json.load(sys.stdin).get('error',''))" 2>/dev/null
}

get_screen() {
  local resp
  resp=$(api_post "screentext" "{\"sname\":\"$1\"}")
  echo "$resp" | python3 -c "
import sys, json
data = json.load(sys.stdin)['data']['text']
for i in range(1, 25):
    print(data.get(str(i), ' ' * 80))
" 2>/dev/null
}

screen_contains() {
  echo "$1" | grep -qi "$2"
}

print_screen_rows() {
  local screen="$1"
  local label="$2"
  log_screen "$label" "$screen"
  # Also show non-empty rows on console
  echo "$screen" | awk -v y="${YELLOW}" -v d="${DIM}" -v nc="${NC}" '
    NF && $0 !~ /^[[:space:]]*$/ {
      printf "      %s%2d│%s %s%s\n", d, NR, nc, $0, nc
    }
  '
}

# =============================================================================
# PHASE 1: ENVIRONMENT SETUP
# =============================================================================

section "IBM 3270 Terminal Automation — Test Suite"
out ""
out "  ${DIM}Timestamp : ${TIMESTAMP}${NC}"
out "  ${DIM}Log file  : ${LOG_FILE}${NC}"
out "  ${DIM}API URL   : ${BASE_URL}${NC}"
out "  ${DIM}Session   : ${SESSION}${NC}"

log_only "============================================================"
log_only "Test Run: $TIMESTAMP"
log_only "Host: $(hostname)"
log_only "Docker Dir: $DOCKER_DIR"
log_only "API URL: $BASE_URL"
log_only "============================================================"

# ---------------------------------------------------------------------------
# Build & Start Docker
# ---------------------------------------------------------------------------

section "Phase 1: Environment Setup"

log_info "Building Docker images..."
log_only "[DOCKER BUILD OUTPUT]"
docker compose -f "$DOCKER_DIR/docker-compose.yml" build 2>&1 | while IFS= read -r line; do
  log_only "  $line"
done
log_info "Docker images built"

log_info "Starting containers..."
log_only "[DOCKER UP OUTPUT]"
docker compose -f "$DOCKER_DIR/docker-compose.yml" up -d 2>&1 | while IFS= read -r line; do
  log_only "  $line"
done

# Wait for mock mainframe health check
log_info "Waiting for Mock IBM Mainframe (TN3270 on port 3270)..."
MOCK_READY=false
for i in $(seq 1 30); do
  if docker compose -f "$DOCKER_DIR/docker-compose.yml" ps 2>/dev/null | grep -q "healthy"; then
    MOCK_READY=true
    break
  fi
  sleep 1
done

if [ "$MOCK_READY" = true ]; then
  log_info "Mock IBM Mainframe is healthy"
else
  out "  ${RED}ERROR: Mock mainframe did not become healthy in 30s${NC}"
  log_only "FATAL: Mock mainframe health check timeout"
  docker compose -f "$DOCKER_DIR/docker-compose.yml" logs 2>&1 | while IFS= read -r line; do
    log_only "  [DOCKER LOG] $line"
  done
  docker compose -f "$DOCKER_DIR/docker-compose.yml" down 2>/dev/null
  exit 1
fi

# Wait for TE Server
log_info "Waiting for TE REST API server (port 9995)..."
TE_READY=false
for i in $(seq 1 30); do
  resp=$(curl -s "$BASE_URL/te/ping" 2>/dev/null || true)
  if echo "$resp" | grep -q "pingstatus" 2>/dev/null; then
    TE_READY=true
    break
  fi
  sleep 1
done

if [ "$TE_READY" = true ]; then
  log_info "TE REST API server is ready"
else
  out "  ${RED}ERROR: TE server did not start in 30s${NC}"
  log_only "FATAL: TE server startup timeout"
  docker compose -f "$DOCKER_DIR/docker-compose.yml" logs 2>&1 | while IFS= read -r line; do
    log_only "  [DOCKER LOG] $line"
  done
  docker compose -f "$DOCKER_DIR/docker-compose.yml" down 2>/dev/null
  exit 1
fi

# Log container status
log_only ""
log_only "[CONTAINER STATUS]"
docker compose -f "$DOCKER_DIR/docker-compose.yml" ps 2>&1 | while IFS= read -r line; do
  log_only "  $line"
done

out ""
out "  ${GREEN}Environment ready${NC} — Mock IBM Mainframe + TE API running"
out ""

# =============================================================================
# PHASE 2: MOCK IBM MAINFRAME VERIFICATION
# =============================================================================

section "Phase 2: Mock IBM Mainframe Verification"

# ---------------------------------------------------------------------------
# TC-01: Ping / Health Check
# ---------------------------------------------------------------------------
tc_header "TC-01: API Health Check"
resp=$(api_get "ping")
status=$(check_status "$resp")
if [ "$status" = "200" ]; then
  pass "TE Server responded — pingstatus=ok"
else
  fail "TE Server ping failed" "$(get_error "$resp")"
fi

# ---------------------------------------------------------------------------
# TC-02: Connect to Mock IBM Mainframe
# ---------------------------------------------------------------------------
tc_header "TC-02: Connect to Mock IBM Mainframe"
log_info "Connecting session '$SESSION' → mock-mainframe:3270"
resp=$(api_post "startsession" "{\"path\":\"sessions/default.txt\",\"sname\":\"$SESSION\"}")
status=$(check_status "$resp")
if [ "$status" = "200" ]; then
  pass "TN3270 session '$SESSION' established"
else
  fail "Could not connect to Mock IBM Mainframe" "$(get_error "$resp")"
fi

# ---------------------------------------------------------------------------
# TC-03: Verify IBM Login Screen (VTAM)
# ---------------------------------------------------------------------------
tc_header "TC-03: Verify IBM Login Screen (VTAM)"
screen=$(get_screen "$SESSION")
log_info "Reading initial 3270 screen..."
print_screen_rows "$screen" "LOGIN SCREEN"

if screen_contains "$screen" "IBM MOCK MAINFRAME"; then
  pass "IBM banner displayed: 'IBM MOCK MAINFRAME SYSTEM'"
else
  fail "IBM banner not found on login screen" ""
fi

if screen_contains "$screen" "USERID"; then
  pass "USERID input field present"
else
  fail "USERID field missing" ""
fi

if screen_contains "$screen" "PASSWORD"; then
  pass "PASSWORD input field present"
else
  fail "PASSWORD field missing" ""
fi

if screen_contains "$screen" "MOCK3270"; then
  pass "Terminal ID 'MOCK3270' shown in status line"
else
  fail "Terminal ID not found" ""
fi

# =============================================================================
# PHASE 3: AUTHENTICATION
# =============================================================================

section "Phase 3: Authentication"

# ---------------------------------------------------------------------------
# TC-04: Fill Username Field
# ---------------------------------------------------------------------------
tc_header "TC-04: Enter Username"
log_info "Typing 'TESTUSER' at row=11, col=23"
resp=$(api_post "entertext_by_row_col" "{\"sname\":\"$SESSION\",\"row\":11,\"col\":23,\"text\":\"TESTUSER\"}")
status=$(check_status "$resp")
if [ "$status" = "200" ]; then
  pass "Username 'TESTUSER' entered at field (11,23)"
else
  fail "Could not enter username" "$(get_error "$resp")"
fi

# ---------------------------------------------------------------------------
# TC-05: Submit Login (Press Enter)
# ---------------------------------------------------------------------------
tc_header "TC-05: Submit Login"
log_info "Pressing ENTER to authenticate..."
resp=$(api_post "send_special_key" "{\"sname\":\"$SESSION\",\"key\":\"enter\"}")
status=$(check_status "$resp")
if [ "$status" = "200" ]; then
  pass "ENTER key transmitted"
else
  fail "ENTER key failed" "$(get_error "$resp")"
fi

# ---------------------------------------------------------------------------
# TC-06: Verify Main Menu After Login
# ---------------------------------------------------------------------------
tc_header "TC-06: Verify Main Menu (Post-Login)"
screen=$(get_screen "$SESSION")
log_info "Reading post-login screen..."
print_screen_rows "$screen" "MAIN MENU"

if screen_contains "$screen" "MAIN MENU"; then
  pass "Main menu loaded after login"
else
  fail "Main menu not displayed after login" ""
fi

if screen_contains "$screen" "READY"; then
  pass "System READY indicator present"
else
  fail "READY indicator missing" ""
fi

if screen_contains "$screen" "ISPF"; then
  pass "Option 1 (ISPF) visible"
else
  fail "ISPF option not found" ""
fi

if screen_contains "$screen" "TSO"; then
  pass "Option 2 (TSO) visible"
else
  fail "TSO option not found" ""
fi

if screen_contains "$screen" "CICS"; then
  pass "Option 3 (CICS) visible"
else
  fail "CICS option not found" ""
fi

# =============================================================================
# PHASE 4: SCREEN INTERACTION
# =============================================================================

section "Phase 4: Screen Interaction"

# ---------------------------------------------------------------------------
# TC-07: Search for Text on Screen
# ---------------------------------------------------------------------------
tc_header "TC-07: Search for Text on Screen"
log_info "Searching for 'READY' on current screen..."
resp=$(api_post "search" "{\"sname\":\"$SESSION\",\"text\":\"READY\"}")
top=$(echo "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['top'])" 2>/dev/null)
left=$(echo "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['left'])" 2>/dev/null)
if [ "$top" != "-1" ] && [ -n "$top" ]; then
  pass "Found 'READY' at position row=$top, col=$left"
else
  fail "Text 'READY' not found on screen" ""
fi

# ---------------------------------------------------------------------------
# TC-08: Read Field Text by Row/Col
# ---------------------------------------------------------------------------
tc_header "TC-08: Read Field Text by Row/Col"
log_info "Reading 30 chars from row=1, col=25..."
resp=$(api_post "fieldtext_by_row_col" "{\"sname\":\"$SESSION\",\"row\":1,\"col\":25,\"length\":30}")
text=$(echo "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['text'])" 2>/dev/null)
if echo "$text" | grep -qi "MOCK MAINFRAME"; then
  pass "Field text read: '$(echo "$text" | xargs)'"
else
  fail "Unexpected field text" "got: '$text'"
fi

# ---------------------------------------------------------------------------
# TC-09: Move Cursor
# ---------------------------------------------------------------------------
tc_header "TC-09: Move Cursor"
log_info "Moving cursor to row=12, col=22..."
resp=$(api_post "moveto" "{\"sname\":\"$SESSION\",\"row\":12,\"col\":22}")
status=$(check_status "$resp")
if [ "$status" = "200" ]; then
  pass "Cursor repositioned to (12,22)"
else
  fail "Cursor move failed" "$(get_error "$resp")"
fi

# ---------------------------------------------------------------------------
# TC-10: Send Keys Without Enter
# ---------------------------------------------------------------------------
tc_header "TC-10: Type Text Without Submitting"
log_info "Typing 'HELLO' without pressing Enter..."
resp=$(api_post "sendkeysnoreturn" "{\"sname\":\"$SESSION\",\"text\":\"HELLO\"}")
status=$(check_status "$resp")
if [ "$status" = "200" ]; then
  pass "Text 'HELLO' typed (no Enter)"
else
  fail "sendkeysnoreturn failed" "$(get_error "$resp")"
fi

# =============================================================================
# PHASE 5: NAVIGATION (ISPF / TSO / STATUS)
# =============================================================================

section "Phase 5: Application Navigation"

# ---------------------------------------------------------------------------
# TC-11: Navigate to ISPF
# ---------------------------------------------------------------------------
tc_header "TC-11: Navigate to ISPF (Option 1)"
log_info "Sending '1' + Enter to open ISPF..."
resp=$(api_post "sendkeys" "{\"sname\":\"$SESSION\",\"text\":\"1\"}")
status=$(check_status "$resp")
if [ "$status" = "200" ]; then
  pass "Command '1' sent with Enter"
else
  fail "sendkeys failed" "$(get_error "$resp")"
fi

screen=$(get_screen "$SESSION")
print_screen_rows "$screen" "ISPF SCREEN"

if screen_contains "$screen" "ISPF Primary Option Menu"; then
  pass "ISPF Primary Option Menu displayed"
else
  fail "ISPF screen not loaded" ""
fi

if screen_contains "$screen" "F3=EXIT"; then
  pass "F3=EXIT hint visible"
else
  fail "F3=EXIT hint missing" ""
fi

# ---------------------------------------------------------------------------
# TC-12: F3 Exit from ISPF → Main Menu
# ---------------------------------------------------------------------------
tc_header "TC-12: Exit ISPF with F3"
log_info "Pressing F3 to return to main menu..."
resp=$(api_post "send_special_key" "{\"sname\":\"$SESSION\",\"key\":\"F3\"}")
status=$(check_status "$resp")
if [ "$status" = "200" ]; then
  pass "F3 key transmitted"
else
  fail "F3 key failed" "$(get_error "$resp")"
fi

screen=$(get_screen "$SESSION")
print_screen_rows "$screen" "MAIN MENU (after ISPF exit)"

if screen_contains "$screen" "MAIN MENU"; then
  pass "Returned to Main Menu from ISPF"
else
  fail "Did not return to main menu" ""
fi

# ---------------------------------------------------------------------------
# TC-13: Navigate to TSO
# ---------------------------------------------------------------------------
tc_header "TC-13: Navigate to TSO (Option 2)"
log_info "Sending '2' + Enter to open TSO..."
resp=$(api_post "sendkeys" "{\"sname\":\"$SESSION\",\"text\":\"2\"}")
screen=$(get_screen "$SESSION")
print_screen_rows "$screen" "TSO SCREEN"

if screen_contains "$screen" "TSO COMMAND PROCESSOR"; then
  pass "TSO Command Processor displayed"
else
  fail "TSO screen not loaded" ""
fi

log_info "Pressing F3 to return..."
api_post "send_special_key" "{\"sname\":\"$SESSION\",\"key\":\"F3\"}" > /dev/null

# ---------------------------------------------------------------------------
# TC-14: Navigate to System Status
# ---------------------------------------------------------------------------
tc_header "TC-14: Navigate to System Status (Option 4)"
log_info "Pressing Enter to refresh, then sending '4'..."
api_post "send_special_key" "{\"sname\":\"$SESSION\",\"key\":\"enter\"}" > /dev/null
resp=$(api_post "sendkeys" "{\"sname\":\"$SESSION\",\"text\":\"4\"}")
screen=$(get_screen "$SESSION")
print_screen_rows "$screen" "STATUS SCREEN"

if screen_contains "$screen" "SYSTEM STATUS"; then
  pass "System Status screen displayed"
else
  fail "Status screen not loaded" ""
fi

if screen_contains "$screen" "ACTIVE"; then
  pass "System status: ACTIVE"
else
  fail "ACTIVE status not found" ""
fi

if screen_contains "$screen" "MOCK3270"; then
  pass "System name: MOCK3270"
else
  fail "System name not found" ""
fi

log_info "Pressing F3 to return..."
api_post "send_special_key" "{\"sname\":\"$SESSION\",\"key\":\"F3\"}" > /dev/null

# =============================================================================
# PHASE 6: UTILITY OPERATIONS
# =============================================================================

section "Phase 6: Utility Operations"

# ---------------------------------------------------------------------------
# TC-15: Clear Screen
# ---------------------------------------------------------------------------
tc_header "TC-15: Clear Screen"
log_info "Sending CLEAR command..."
resp=$(api_post "clearscreen" "{\"sname\":\"$SESSION\"}")
status=$(check_status "$resp")
if [ "$status" = "200" ]; then
  pass "Screen cleared successfully"
else
  fail "Clear screen failed" "$(get_error "$resp")"
fi

# ---------------------------------------------------------------------------
# TC-16: Pause / Wait
# ---------------------------------------------------------------------------
tc_header "TC-16: Pause (1 second)"
log_info "Requesting 1-second pause..."
t_start=$(python3 -c "import time; print(time.time())")
resp=$(api_post "pause" "{\"sname\":\"$SESSION\",\"time\":1}")
t_end=$(python3 -c "import time; print(time.time())")
elapsed=$(python3 -c "print(round($t_end - $t_start, 1))")
status=$(check_status "$resp")
if [ "$status" = "200" ]; then
  pass "Paused for ${elapsed}s (requested 1.0s)"
else
  fail "Pause failed" "$(get_error "$resp")"
fi

# ---------------------------------------------------------------------------
# TC-17: Session Status API
# ---------------------------------------------------------------------------
tc_header "TC-17: Session Status API"
log_info "Querying /te/status..."
resp=$(api_get "status")
if echo "$resp" | grep -q "$SESSION"; then
  sessions_json=$(echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']['sessions']; [print(f'  {k}: {v}') for k,v in d.items()]" 2>/dev/null)
  pass "Session '$SESSION' found in active sessions"
  out "      ${DIM}Active sessions:${NC}"
  echo "$sessions_json" | while IFS= read -r line; do
    out "        ${DIM}$line${NC}"
  done
else
  fail "Session '$SESSION' not in status response" ""
fi

# =============================================================================
# PHASE 7: DISCONNECT & CLEANUP
# =============================================================================

section "Phase 7: Disconnect & Cleanup"

# ---------------------------------------------------------------------------
# TC-18: Disconnect Session
# ---------------------------------------------------------------------------
tc_header "TC-18: Disconnect Session"
log_info "Disconnecting session '$SESSION'..."
resp=$(api_post "disconnect" "{\"sname\":\"$SESSION\"}")
status=$(check_status "$resp")
if [ "$status" = "200" ]; then
  pass "Session '$SESSION' disconnected"
else
  fail "Disconnect failed" "$(get_error "$resp")"
fi

log_info "Verifying session cleanup..."
resp=$(api_get "status")
if echo "$resp" | python3 -c "import sys,json; sessions=json.load(sys.stdin)['data']['sessions']; sys.exit(1 if '$SESSION' in sessions else 0)" 2>/dev/null; then
  pass "Session '$SESSION' removed from active sessions"
else
  fail "Session '$SESSION' still present after disconnect" ""
fi

# =============================================================================
# PHASE 8: TEARDOWN
# =============================================================================

section "Phase 8: Teardown"

log_info "Capturing Docker logs..."
log_only ""
log_only "[MOCK MAINFRAME LOGS]"
docker compose -f "$DOCKER_DIR/docker-compose.yml" logs mock-mainframe 2>&1 | tail -30 | while IFS= read -r line; do
  log_only "  $line"
done
log_only ""
log_only "[TE SERVER LOGS]"
docker compose -f "$DOCKER_DIR/docker-compose.yml" logs te-server 2>&1 | tail -30 | while IFS= read -r line; do
  log_only "  $line"
done

log_info "Stopping Docker containers..."
docker compose -f "$DOCKER_DIR/docker-compose.yml" down 2>&1 | while IFS= read -r line; do
  log_only "  $line"
done
log_info "Containers stopped and removed"

# =============================================================================
# RESULTS
# =============================================================================

END_TIME=$(python3 -c "import time; print(time.time())")
DURATION=$(python3 -c "print(f'{($END_TIME - $START_TIME):.1f}')")

section "Test Results"
out ""
out "  ${BOLD}Total assertions : $TOTAL${NC}"
out "  ${GREEN}Passed           : $PASS${NC}"
if [ "$FAIL" -gt 0 ]; then
  out "  ${RED}Failed           : $FAIL${NC}"
else
  out "  ${DIM}Failed           : 0${NC}"
fi
out "  ${DIM}Duration         : ${DURATION}s${NC}"
out "  ${DIM}Log file         : ${LOG_FILE}${NC}"
out ""

if [ "$FAIL" -gt 0 ]; then
  out "  ${RED}${BOLD}RESULT: FAILED${NC}"
  out ""
  log_only ""
  log_only "RESULT: FAILED ($PASS/$TOTAL passed, $FAIL failed) in ${DURATION}s"
  exit 1
else
  out "  ${GREEN}${BOLD}RESULT: ALL PASSED${NC}"
  out ""
  log_only ""
  log_only "RESULT: ALL PASSED ($PASS/$TOTAL) in ${DURATION}s"
  exit 0
fi
