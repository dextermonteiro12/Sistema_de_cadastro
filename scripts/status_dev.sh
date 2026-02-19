#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/_common.sh"

show() {
  local name="$1" file="$2"
  if is_running "$file"; then
    echo "$name: RUNNING (PID $(cat "$file"))"
  else
    echo "$name: STOPPED"
  fi
}

show "API" "$API_PID_FILE"
show "WORKER" "$WORKER_PID_FILE"
show "FRONTEND" "$FRONTEND_PID_FILE"
