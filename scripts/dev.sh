#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="$HOME/.local/bin:$PATH"
export PYTHONPATH="$ROOT/backend/src"

cleanup() {
  if [[ -n "${API_PID:-}" ]]; then kill "$API_PID" 2>/dev/null || true; fi
  if [[ -n "${WEB_PID:-}" ]]; then kill "$WEB_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT INT TERM

cd "$ROOT/backend"
uv run uvicorn garleb_desk.main:app --host 0.0.0.0 --port 8011 --reload &
API_PID=$!

cd "$ROOT/frontend"
npm run dev -- --host 0.0.0.0 --port 5171 &
WEB_PID=$!

echo "GARLEB Desk API  http://127.0.0.1:8011"
echo "GARLEB Desk UI   http://127.0.0.1:5171"
wait
