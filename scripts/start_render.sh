#!/usr/bin/env bash
set -euo pipefail

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${PORT:-8502}"

export VENDYGOSCAN_API_URL="${VENDYGOSCAN_API_URL:-http://127.0.0.1:${BACKEND_PORT}/analyze}"
export VENDYGOSCAN_LOG_DIR="${VENDYGOSCAN_LOG_DIR:-logs}"

uvicorn app.main:app --host 0.0.0.0 --port "${BACKEND_PORT}" &
BACKEND_PID="$!"

cleanup() {
  kill "${BACKEND_PID}" 2>/dev/null || true
}
trap cleanup EXIT

streamlit run frontend/streamlit_app.py \
  --server.address 0.0.0.0 \
  --server.port "${FRONTEND_PORT}" \
  --server.headless true \
  --browser.gatherUsageStats false
