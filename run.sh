#!/bin/bash
# ============================================================
#  Vitae-I — Project Runner
#  Usage:
#    ./run.sh          → Start API + Frontend (full stack)
#    ./run.sh api      → Start API only
#    ./run.sh app      → Start Frontend only
#    ./run.sh test     → Run the test suite
# ============================================================

set -e

# ── Colours ──────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Colour

# ── Paths ────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

# ── Helpers ──────────────────────────────────────────────────
info()    { echo -e "${CYAN}[vitae-i]${NC} $1"; }
success() { echo -e "${GREEN}[vitae-i]${NC} $1"; }
warn()    { echo -e "${YELLOW}[vitae-i]${NC} $1"; }
error()   { echo -e "${RED}[vitae-i]${NC} $1"; exit 1; }

ensure_venv() {
    if [ ! -f "$VENV_PYTHON" ]; then
        warn "Virtual environment not found. Creating one..."
        python3 -m venv "$VENV_DIR"
        success "Virtual environment created at $VENV_DIR"
    fi

    info "Checking dependencies..."
    "$VENV_PIP" install -r "$SCRIPT_DIR/requirements.txt" --quiet
    success "Dependencies are up to date."
}

# ── Commands ─────────────────────────────────────────────────
start_api() {
    info "Starting FastAPI backend on http://localhost:8000 ..."
    "$VENV_PYTHON" -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload
}

start_app() {
    info "Starting Streamlit frontend on http://localhost:8501 ..."
    "$VENV_PYTHON" -m streamlit run "$SCRIPT_DIR/app.py"
}

run_tests() {
    info "Running test suite with pytest..."
    "$VENV_PYTHON" -m pytest "$SCRIPT_DIR/tests/" -v
}

start_all() {
    info "Starting full stack (API + Frontend)..."
    echo ""

    # Start the API in the background
    "$VENV_PYTHON" -m uvicorn api:app --host 127.0.0.1 --port 8000 &
    API_PID=$!
    success "API started (PID: $API_PID) → http://localhost:8000"

    # Give the API a moment to boot before the frontend tries to connect
    sleep 2

    # Start the frontend in the background
    "$VENV_PYTHON" -m streamlit run "$SCRIPT_DIR/app.py" &
    APP_PID=$!
    success "Frontend started (PID: $APP_PID) → http://localhost:8501"

    echo ""
    info "Both services are running. Press Ctrl+C to stop."

    # Wait and handle graceful shutdown
    trap "echo ''; warn 'Shutting down...'; kill $API_PID $APP_PID 2>/dev/null; success 'All services stopped.'" INT TERM
    wait
}

# ── Entry Point ──────────────────────────────────────────────
cd "$SCRIPT_DIR"
ensure_venv

case "${1:-all}" in
    api)   start_api ;;
    app)   start_app ;;
    test)  run_tests ;;
    all)   start_all ;;
    *)
        echo "Usage: $0 [api|app|test|all]"
        exit 1
        ;;
esac
