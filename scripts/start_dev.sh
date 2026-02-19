#!/usr/bin/env bash
# scripts/start_dev.sh - Iniciar serviços do ambiente de desenvolvimento
set -euo pipefail
source "$(dirname "$0")/_common.sh"

# Função para ativar venv e iniciar processo
start_api() {
  if is_running "$API_PID_FILE"; then 
    msg "API já rodando (PID $(cat "$API_PID_FILE"))"
    return 0
  fi
  
  msg "Iniciando API Gateway..."
  cd "$API_DIR"
  
  # Verificar se venv existe
  if [[ ! -d ".venv" ]]; then
    error "venv não encontrado em $API_DIR. Execute: bash scripts/setup_env.sh"
    return 1
  fi
  
  # Iniciar em background - funciona no Windows e Unix
  if [[ -f ".venv/Scripts/python.exe" ]]; then
    # Windows
    nohup .venv/Scripts/python.exe main.py > "$API_LOG" 2>&1 &
    local pid=$!
    echo $pid > "$API_PID_FILE"
    msg "✓ API iniciada (PID $pid)"
  elif [[ -f ".venv/bin/python" ]]; then
    # Unix/Linux/Mac
    nohup .venv/bin/python main.py > "$API_LOG" 2>&1 &
    local pid=$!
    echo $pid > "$API_PID_FILE"
    msg "✓ API iniciada (PID $pid)"
  else
    error "Interpretador Python não encontrado no venv"
    return 1
  fi
  
  msg "Log: $API_LOG"
}

start_worker() {
  if is_running "$WORKER_PID_FILE"; then 
    msg "Worker já rodando (PID $(cat "$WORKER_PID_FILE"))"
    return 0
  fi
  
  msg "Iniciando gRPC Worker..."
  cd "$WORKER_DIR"
  
  # Verificar se venv existe
  if [[ ! -d ".venv" ]]; then
    error "venv não encontrado em $WORKER_DIR. Execute: bash scripts/setup_env.sh"
    return 1
  fi
  
  # Iniciar em background - funciona no Windows e Unix
  if [[ -f ".venv/Scripts/python.exe" ]]; then
    # Windows
    nohup .venv/Scripts/python.exe server.py > "$WORKER_LOG" 2>&1 &
    local pid=$!
    echo $pid > "$WORKER_PID_FILE"
    msg "✓ Worker iniciado (PID $pid)"
  elif [[ -f ".venv/bin/python" ]]; then
    # Unix/Linux/Mac
    nohup .venv/bin/python server.py > "$WORKER_LOG" 2>&1 &
    local pid=$!
    echo $pid > "$WORKER_PID_FILE"
    msg "✓ Worker iniciado (PID $pid)"
  else
    error "Interpretador Python não encontrado no venv"
    return 1
  fi
  
  msg "Log: $WORKER_LOG"
}

start_frontend() {
  [[ "$START_FRONTEND" == "1" ]] || { 
    msg "Frontend desabilitado (defina START_FRONTEND=1 para habilitar)"
    return 0
  }
  
  if is_running "$FRONTEND_PID_FILE"; then 
    msg "Frontend já rodando (PID $(cat "$FRONTEND_PID_FILE"))"
    return 0
  fi
  
  msg "Iniciando Frontend React..."
  cd "$FRONTEND_DIR"
  
  # Verificar se node_modules existe
  if [[ ! -d "node_modules" ]]; then
    error "node_modules não encontrado. Execute: bash scripts/setup_env.sh"
    return 1
  fi
  
  # npm start em background
  nohup npm start > "$FRONTEND_LOG" 2>&1 &
  local pid=$!
  echo $pid > "$FRONTEND_PID_FILE"
  msg "✓ Frontend iniciado (PID $pid)"
  msg "Log: $FRONTEND_LOG"
}

# Função para aguardar API estar saudável
wait_api_health() {
  msg "Aguardando API responder /health..."
  
  local max_attempts=40
  local attempt=0
  
  while [[ $attempt -lt $max_attempts ]]; do
    if command -v curl &> /dev/null; then
      if curl -fsS "$API_URL/health" >/dev/null 2>&1; then
        msg "✓ API saudável em $API_URL/health"
        return 0
      fi
    else
      # Fallback se curl não existir
      if [[ -f "$API_LOG" ]] && grep -q "Uvicorn running" "$API_LOG"; then
        msg "✓ API iniciada (detectado no log)"
        return 0
      fi
    fi
    
    attempt=$((attempt + 1))
    sleep 1
  done
  
  echo "⚠ API não respondeu /health após ${max_attempts}s" >&2
  echo "Verifique o log: $API_LOG" >&2
  return 1
}

# Processar argumentos
SERVICES_TO_START="${1:-all}"

case "$SERVICES_TO_START" in
  api)
    start_api || { msg "Falha ao iniciar API"; exit 1; }
    wait_api_health || true
    ;;
  worker)
    start_worker || { msg "Falha ao iniciar Worker"; exit 1; }
    msg "✓ Worker iniciado com sucesso"
    ;;
  frontend)
    start_frontend || { msg "Falha ao iniciar Frontend"; exit 1; }
    msg "✓ Frontend iniciado com sucesso"
    ;;
  backend)
    start_api || { msg "Falha ao iniciar API"; exit 1; }
    start_worker || { msg "Falha ao iniciar Worker"; exit 1; }
    wait_api_health || true
    msg "✓ Backend completo iniciado"
    ;;
  all)
    start_api || { msg "Falha ao iniciar API"; exit 1; }
    start_worker || { msg "Falha ao iniciar Worker"; exit 1; }
    start_frontend || true  # Frontend é opcional
    wait_api_health || true
    msg "✓ Todos os serviços iniciados"
    ;;
  *)
    echo "❌ Opção inválida: $SERVICES_TO_START" >&2
    echo "Uso: bash scripts/start_dev.sh {api|worker|frontend|backend|all}" >&2
    exit 1
    ;;
esac

msg "Para verificar status: bash scripts/status_dev.sh"
msg "Para parar: bash scripts/stop_dev.sh $SERVICES_TO_START"