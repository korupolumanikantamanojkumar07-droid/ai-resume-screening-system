#!/usr/bin/env bash
set -e
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PATH="$HOME/.local/bin:$PATH"

echo "Starting FastAPI backend on http://127.0.0.1:8000 ..."
(
  cd "$ROOT_DIR/backend"
  PYTHONPATH=. "$ROOT_DIR/backend/venv/bin/uvicorn" app.main:app --host 127.0.0.1 --port 8000
) &
BACKEND_PID=$!

echo "Starting Vite React frontend on http://127.0.0.1:5173 ..."
(
  cd "$ROOT_DIR/frontend"
  npm run dev -- --host 127.0.0.1 --port 5173
) &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true" EXIT
wait
