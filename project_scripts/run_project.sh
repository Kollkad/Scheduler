#!/bin/bash

# Absolute path to the script directory (project_scripts)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# Project root is the parent directory of SCRIPT_DIR
ROOT="$(dirname "$SCRIPT_DIR")"

echo "ROOT: $ROOT"

# --- Frontend ---
if [ -d "$ROOT/frontend" ]; then
    echo "[OK] Frontend folder found: $ROOT/frontend"
    gnome-terminal -- bash -c "cd '$ROOT/frontend' && npm run dev; exec bash"
else
    echo "[ERROR] Frontend folder NOT found: $ROOT/frontend"
fi

# --- Backend ---
if [ -d "$ROOT/backend/app" ]; then
    echo "[OK] Backend folder found: $ROOT/backend/app"
    gnome-terminal -- bash -c "cd '$ROOT' && python3 -m backend.app.main; exec bash"
else
    echo "[ERROR] Backend folder NOT found: $ROOT/backend/app"
fi

echo "Check complete."