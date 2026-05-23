#!/usr/bin/env bash
set -euo pipefail

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${PORT:-8502}"

export VENDYGOSCAN_API_URL="${VENDYGOSCAN_API_URL:-http://127.0.0.1:${BACKEND_PORT}/analyze}"
export VENDYGOSCAN_LOG_DIR="${VENDYGOSCAN_LOG_DIR:-logs}"

echo "Starting FastAPI backend on port ${BACKEND_PORT}"
uvicorn app.main:app --host 0.0.0.0 --port "${BACKEND_PORT}" &
BACKEND_PID="$!"

cleanup() {
  kill "${BACKEND_PID}" 2>/dev/null || true
}
trap cleanup EXIT

echo "Waiting for FastAPI backend health check..."
for attempt in $(seq 1 30); do
  if python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${BACKEND_PORT}/health', timeout=2)" >/dev/null 2>&1; then
    echo "FastAPI backend is ready."
    break
  fi

  if ! kill -0 "${BACKEND_PID}" 2>/dev/null; then
    echo "FastAPI backend stopped before becoming ready."
    exit 1
  fi

  if [ "${attempt}" -eq 30 ]; then
    echo "FastAPI backend did not become ready in time."
    exit 1
  fi

  sleep 1
done

echo "Starting Streamlit frontend on port ${FRONTEND_PORT}"
echo "Streamlit will call API at ${VENDYGOSCAN_API_URL}"
streamlit run frontend/streamlit_app.py \
  --server.address 0.0.0.0 \
  --server.port "${FRONTEND_PORT}" \
  --server.headless true \
  --browser.gatherUsageStats false
