#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/_common.sh"

echo "== /health =="
curl -fsS "$API_URL/health"; echo

if [[ -n "${CONFIG_KEY:-}" ]]; then
  echo "== GraphQL =="
  curl -fsS -X POST "$API_URL/graphql" \
    -H "Content-Type: application/json" \
    -H "X-Config-Key: $CONFIG_KEY" \
    -d '{"query":"{ monitoramentoStatus { statusGeral filaPendente } }"}'
  echo
else
  echo "CONFIG_KEY não informado. Pulando GraphQL."
fi
