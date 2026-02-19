#!/usr/bin/env bash
# scripts/adopt_orphan_processes.sh - Adotar processos órfãos do sistema

source "$(dirname "$0")/_common.sh"

msg "Procurando processos órfãos do sistema..."

# Função para encontrar PID por porta
find_pid_by_port() {
  local port="$1"
  netstat.exe -ano 2>/dev/null | grep ":$port " | grep "LISTENING" | awk '{print $5}' | head -1
}

# Procurar API na porta 5000
api_pid=$(find_pid_by_port 5000)
if [[ -n "$api_pid" ]]; then
  echo "$api_pid" > "$API_PID_FILE"
  msg "✓ API encontrada (PID $api_pid) - agora sob controle dos scripts"
else
  msg "API não encontrada rodando"
fi

# Procurar Worker na porta 50051
worker_pid=$(find_pid_by_port 50051)
if [[ -n "$worker_pid" ]]; then
  echo "$worker_pid" > "$WORKER_PID_FILE"
  msg "✓ Worker encontrado (PID $worker_pid) - agora sob controle dos scripts"
else
  msg "Worker não encontrado rodando"
fi

# Procurar Frontend na porta 3000
frontend_pid=$(find_pid_by_port 3000)
if [[ -n "$frontend_pid" ]]; then
  echo "$frontend_pid" > "$FRONTEND_PID_FILE"
  msg "✓ Frontend encontrado (PID $frontend_pid) - agora sob controle dos scripts"
else
  msg "Frontend não encontrado rodando"
fi

msg "Verificando status..."
bash "$(dirname "$0")/status_dev.sh"