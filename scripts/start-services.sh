#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_PORT="${PORT:-8000}"
BFF_PORT="${BFF_PORT:-4000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

PY_PID=""
BFF_PID=""
FRONT_PID=""

cleanup() {
  for pid in "$PY_PID" "$BFF_PID" "$FRONT_PID"; do
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done
  wait || true
}

trap cleanup EXIT INT TERM

cd "$ROOT_DIR/server"
/venv/bin/python3 -m uvicorn server:app --host 0.0.0.0 --port "$PYTHON_PORT" &
PY_PID="$!"

cd "$ROOT_DIR/client"
BFF_PORT="$BFF_PORT" npm run bff &
BFF_PID="$!"

# Run frontend in dev or production mode based on NODE_ENV
if [[ "${NODE_ENV:-development}" == "production" ]]; then
  echo "Starting frontend in production mode..."
  npm run preview -- --host 0.0.0.0 --port "$FRONTEND_PORT" --strictPort &
  FRONT_PID="$!"
else
  echo "Starting frontend in development mode..."
  npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT" --strictPort &
  FRONT_PID="$!"
fi

wait -n
