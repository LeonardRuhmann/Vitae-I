#!/bin/bash
# ============================================================
#  Vitae-I — Project Runner
#  Usage:
#    ./run.sh docker   → Start full stack via Docker (RECOMMENDED for production/demo)
#    ./run.sh          → Start API + Frontend locally (development)
#    ./run.sh api      → Start API only locally
#    ./run.sh app      → Start Frontend only locally
#    ./run.sh test     → Run the test suite locally
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

    MARKER="$VENV_DIR/.req_hash"
    CURRENT_HASH=$(md5sum "$SCRIPT_DIR/requirements.txt" | cut -d ' ' -f 1)

    if [ ! -f "$MARKER" ] || [ "$(cat "$MARKER")" != "$CURRENT_HASH" ]; then
        info "Changes detected in requirements.txt. Installing dependencies..."
        "$VENV_PIP" install -r "$SCRIPT_DIR/requirements.txt" --quiet
        echo "$CURRENT_HASH" > "$MARKER"
        success "Dependencies are installed and up to date."
    else
        info "Dependencies are already installed and up to date. Skipping."
    fi
}

ensure_node() {
    if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
        warn "Node modules not found. Installing frontend dependencies..."
        (cd "$SCRIPT_DIR/frontend" && npm install --silent)
        success "Node modules installed."
    fi
}

# ── Commands ─────────────────────────────────────────────────
start_api() {
    info "Starting FastAPI backend on http://localhost:8000 ..."
    "$VENV_PYTHON" -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload
}

start_app() {
    info "Starting React (Vite) frontend on http://localhost:5173 ..."
    cd "$SCRIPT_DIR/frontend" && npm run dev
}

run_tests() {
    info "Running test suite with pytest..."
    "$VENV_PYTHON" -m pytest "$SCRIPT_DIR/tests/" -v
}

start_all() {
    info "Starting full stack (API + Frontend)..."
    echo ""

    # Start the API in the background
    "$VENV_PYTHON" -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload &
    API_PID=$!
    success "API started (PID: $API_PID) → http://localhost:8000"

    # Give the API a moment to boot before the frontend tries to connect
    sleep 2

    # Start the frontend in the background
    (cd "$SCRIPT_DIR/frontend" && npm run dev) &
    APP_PID=$!
    success "Frontend started (PID: $APP_PID) → http://localhost:5173"

    echo ""
    info "Both services are running. Press Ctrl+C to stop."

    # Wait and handle graceful shutdown
    trap "echo ''; warn 'Shutting down...'; kill $API_PID $APP_PID 2>/dev/null; success 'All services stopped.'" INT TERM
    wait
}

start_docker() {
    info "Starting full stack via Docker Compose (PostgreSQL + API + Frontend)..."
    # Check if docker-compose exists, fallback to docker compose
    if command -v docker-compose &> /dev/null; then
        docker-compose up --build
    else
        docker compose up --build
    fi
}

# ── Entry Point ──────────────────────────────────────────────
cd "$SCRIPT_DIR"
ensure_venv
ensure_node

case "${1:-all}" in
    api)    start_api ;;
    app)    start_app ;;
    test)   run_tests ;;
    docker) start_docker ;;
    all)    start_all ;;
    *)
        echo "Usage: $0 [docker|api|app|test|all]"
        exit 1
        ;;
esac
