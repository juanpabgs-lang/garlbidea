#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="$HOME/.local/bin:$PATH"
export PYTHONPATH="$ROOT/backend/src"
export __VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS="*"

cleanup() {
  if [[ -n "${API_PID:-}" ]]; then kill "$API_PID" 2>/dev/null || true; fi
  if [[ -n "${WEB_PID:-}" ]]; then kill "$WEB_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT INT TERM

start_api() {
  cd "$ROOT/backend"
  uv run uvicorn garleb_desk.main:app --host 0.0.0.0 --port 8011 --reload &
  API_PID=$!
}

start_web() {
  cd "$ROOT/frontend"
  npm run dev -- --host 0.0.0.0 --port 5171 --strictPort &
  WEB_PID=$!
}

start_api
start_web
echo "GARLEB Desk API  http://127.0.0.1:8011"
echo "GARLEB Desk UI   http://127.0.0.1:5171"

# Keep both up for the life of the agent.
while true; do
  if ! kill -0 "${API_PID:-0}" 2>/dev/null; then
    echo "API died — restarting" >&2
    start_api
  fi
  if ! kill -0 "${WEB_PID:-0}" 2>/dev/null; then
    echo "UI died — restarting" >&2
    start_web
  fi
  sleep 4
done
