#!/usr/bin/env bash
# scripts/clean_restart.sh - Limpar processos órfãos e reiniciar

source "$(dirname "$0")/_common.sh"

msg "Parando processos órfãos..."

# Matar processos específicos das portas do sistema
for port in 5000 50051 3000; do
  pid=$(netstat.exe -ano 2>/dev/null | grep ":$port " | grep "LISTENING" | awk '{print $5}' | head -1)
  if [[ -n "$pid" && "$pid" != "0" ]]; then
    msg "Matando processo na porta $port (PID $pid)..."
    taskkill.exe //F //PID "$pid" 2>/dev/null || true
  fi
done

# Limpar arquivos PID antigos
rm -f "$API_PID_FILE" "$WORKER_PID_FILE" "$FRONTEND_PID_FILE"

msg "Aguardando portas liberarem..."
sleep 2

msg "Iniciando serviços sob controle dos scripts..."
bash "$(dirname "$0")/start_dev.sh" "$@"