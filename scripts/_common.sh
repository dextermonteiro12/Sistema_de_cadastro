#!/usr/bin/env bash
# scripts/_common.sh - Funções comuns para scripts de desenvolvimento

# Configurar modo strict DEPOIS de definir variáveis críticas
set -eo pipefail

# Determinar ROOT_DIR de forma mais robusta
if [[ -n "${BASH_SOURCE[0]:-}" ]]; then
  ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
else
  ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
fi

# Agora sim, ativar modo strict completo
set -u

API_DIR="$ROOT_DIR/api-gateway"
WORKER_DIR="$ROOT_DIR/microservice-worker"
FRONTEND_DIR="$ROOT_DIR/frontend-app"

RUN_DIR="$ROOT_DIR/.run"
LOG_DIR="$RUN_DIR/logs"
PID_DIR="$RUN_DIR/pids"

API_PID_FILE="$PID_DIR/api.pid"
WORKER_PID_FILE="$PID_DIR/worker.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"

API_LOG="$LOG_DIR/api.log"
WORKER_LOG="$LOG_DIR/worker.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

API_URL="${API_URL:-http://localhost:5000}"
START_FRONTEND="${START_FRONTEND:-1}"

mkdir -p "$LOG_DIR" "$PID_DIR"

msg() { echo "[$(date +'%H:%M:%S')] $*"; }

# Função de erro que NÃO fecha o terminal
error() {
  echo "❌ ERRO: $*" >&2
  return 1
}

pick_python() {
  if command -v python3 >/dev/null 2>&1; then echo "python3"; return; fi
  if command -v python >/dev/null 2>&1; then echo "python"; return; fi
  error "Python não encontrado no PATH"
}

activate_venv() {
  if [[ -f ".venv/bin/activate" ]]; then
    source .venv/bin/activate
  elif [[ -f ".venv/Scripts/activate" ]]; then
    source .venv/Scripts/activate
  else
    error "Arquivo de ativação não encontrado em .venv"
  fi
}

# Verificar se processo está rodando (compatível com Windows)
is_running() {
  local f="$1"
  [[ -f "$f" ]] || return 1
  local pid; pid="$(cat "$f" 2>/dev/null || true)"
  [[ -n "$pid" ]] || return 1
  
  # Tentar kill -0 primeiro (funciona em Unix)
  if kill -0 "$pid" 2>/dev/null; then
    return 0
  fi
  
  # Fallback para Windows: verificar se PID existe em ps ou tasklist
  if command -v ps &> /dev/null; then
    ps -p "$pid" &> /dev/null && return 0
  fi
  
  # Último recurso no Windows: tasklist
  if command -v tasklist.exe &> /dev/null; then
    tasklist.exe //FI "PID eq $pid" 2>/dev/null | grep -q "^python" && return 0
    tasklist.exe //FI "PID eq $pid" 2>/dev/null | grep -q "^node" && return 0
  fi
  
  return 1
}

ensure_grpc_req() {
  local req="$API_DIR/requirements.txt"
  [[ -f "$req" ]] || return 0
  sed -i.bak -E 's/^grpcio>=.*/grpcio>=1.78.0/' "$req"
  sed -i.bak -E 's/^grpcio-tools>=.*/grpcio-tools>=1.78.0/' "$req"
}