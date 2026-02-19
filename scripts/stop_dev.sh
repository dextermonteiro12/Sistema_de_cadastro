#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/_common.sh"

stop_one() {
  local name="$1" file="$2"
  if is_running "$file"; then
    pid="$(cat "$file")"
    msg "Parando $name (PID $pid)"
    kill "$pid" 2>/dev/null || true
    sleep 1
    kill -9 "$pid" 2>/dev/null || true
  fi
  rm -f "$file"
  msg "$name parado"
}

stop_one "FRONTEND" "$FRONTEND_PID_FILE"
stop_one "WORKER" "$WORKER_PID_FILE"
stop_one "API" "$API_PID_FILE"
