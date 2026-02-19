#!/usr/bin/env bash
# scripts/doctor.sh - Diagnóstico completo do ambiente de desenvolvimento

source "$(dirname "$0")/_common.sh"

ERRORS=0
WARNINGS=0

check() {
  local status="$1"
  local message="$2"
  if [[ "$status" == "OK" ]]; then
    echo "✓ $message"
  elif [[ "$status" == "WARN" ]]; then
    echo "⚠ $message"
    ((WARNINGS++))
  else
    echo "✗ $message"
    ((ERRORS++))
  fi
}

separator() {
  echo ""
  echo "=========================================="
  echo "$1"
  echo "=========================================="
}

separator "1. ESTRUTURA DE DIRETÓRIOS"

[[ -d "$API_DIR" ]] && check "OK" "api-gateway/ existe" || check "ERROR" "api-gateway/ NÃO existe"
[[ -d "$WORKER_DIR" ]] && check "OK" "microservice-worker/ existe" || check "ERROR" "microservice-worker/ NÃO existe"
[[ -d "$FRONTEND_DIR" ]] && check "OK" "frontend-app/ existe" || check "ERROR" "frontend-app/ NÃO existe"
[[ -d "$RUN_DIR" ]] && check "OK" ".run/ existe" || check "WARN" ".run/ não existe (será criado)"

separator "2. AMBIENTES VIRTUAIS"

if [[ -d "$API_DIR/.venv" ]]; then
  check "OK" "api-gateway/.venv/ existe"
  if [[ -f "$API_DIR/.venv/Scripts/python.exe" ]] || [[ -f "$API_DIR/.venv/bin/python" ]]; then
    check "OK" "api-gateway/.venv/ tem Python"
  else
    check "ERROR" "api-gateway/.venv/ corrompido (sem Python)"
  fi
else
  check "ERROR" "api-gateway/.venv/ NÃO existe - execute: bash scripts/setup_env.sh"
fi

if [[ -d "$WORKER_DIR/.venv" ]]; then
  check "OK" "microservice-worker/.venv/ existe"
  if [[ -f "$WORKER_DIR/.venv/Scripts/python.exe" ]] || [[ -f "$WORKER_DIR/.venv/bin/python" ]]; then
    check "OK" "microservice-worker/.venv/ tem Python"
  else
    check "ERROR" "microservice-worker/.venv/ corrompido (sem Python)"
  fi
else
  check "ERROR" "microservice-worker/.venv/ NÃO existe - execute: bash scripts/setup_env.sh"
fi

if [[ -d "$FRONTEND_DIR/node_modules" ]]; then
  check "OK" "frontend-app/node_modules/ existe"
else
  check "ERROR" "frontend-app/node_modules/ NÃO existe - execute: bash scripts/setup_env.sh"
fi

# Venvs legados na raiz
if [[ -d "$ROOT_DIR/venv312" ]]; then
  check "WARN" "venv312/ na raiz detectado (LEGADO - não é mais usado)"
fi

separator "3. ARQUIVOS DE CONFIGURAÇÃO"

[[ -f "$API_DIR/main.py" ]] && check "OK" "api-gateway/main.py existe" || check "ERROR" "api-gateway/main.py NÃO existe"
[[ -f "$API_DIR/requirements.txt" ]] && check "OK" "api-gateway/requirements.txt existe" || check "ERROR" "api-gateway/requirements.txt NÃO existe"
[[ -f "$WORKER_DIR/server.py" ]] && check "OK" "microservice-worker/server.py existe" || check "ERROR" "microservice-worker/server.py NÃO existe"
[[ -f "$WORKER_DIR/requirements.txt" ]] && check "OK" "microservice-worker/requirements.txt existe" || check "ERROR" "microservice-worker/requirements.txt NÃO existe"
[[ -f "$FRONTEND_DIR/package.json" ]] && check "OK" "frontend-app/package.json existe" || check "ERROR" "frontend-app/package.json NÃO existe"

separator "4. PROCESSOS EM EXECUÇÃO"

# Verificar processos gerenciados
if is_running "$API_PID_FILE"; then
  api_pid=$(cat "$API_PID_FILE")
  check "OK" "API rodando (PID $api_pid) - gerenciado pelos scripts"
else
  check "WARN" "API não está rodando (pelos scripts)"
fi

if is_running "$WORKER_PID_FILE"; then
  worker_pid=$(cat "$WORKER_PID_FILE")
  check "OK" "Worker rodando (PID $worker_pid) - gerenciado pelos scripts"
else
  check "WARN" "Worker não está rodando (pelos scripts)"
fi

if is_running "$FRONTEND_PID_FILE"; then
  frontend_pid=$(cat "$FRONTEND_PID_FILE")
  check "OK" "Frontend rodando (PID $frontend_pid) - gerenciado pelos scripts"
else
  check "WARN" "Frontend não está rodando (pelos scripts)"
fi

separator "5. PROCESSOS ÓRFÃOS (não gerenciados)"

# Procurar processos Python órfãos
if command -v tasklist.exe &> /dev/null; then
  orphan_python=$(tasklist.exe //FI "IMAGENAME eq python.exe" //FO CSV //NH 2>/dev/null | wc -l)
  if [[ "$orphan_python" -gt 0 ]]; then
    check "WARN" "Encontrados $orphan_python processos python.exe (alguns podem ser órfãos)"
    tasklist.exe //FI "IMAGENAME eq python.exe" //FO TABLE 2>/dev/null | tail -n +4
  else
    check "OK" "Nenhum processo Python órfão"
  fi
  
  orphan_node=$(tasklist.exe //FI "IMAGENAME eq node.exe" //FO CSV //NH 2>/dev/null | wc -l)
  if [[ "$orphan_node" -gt 0 ]]; then
    check "WARN" "Encontrados $orphan_node processos node.exe (alguns podem ser órfãos)"
    tasklist.exe //FI "IMAGENAME eq node.exe" //FO TABLE 2>/dev/null | tail -n +4
  else
    check "OK" "Nenhum processo Node órfão"
  fi
fi

separator "6. PORTAS EM USO"

# Verificar portas
if command -v netstat.exe &> /dev/null; then
  port_5000=$(netstat.exe -ano 2>/dev/null | grep ":5000 " | grep "LISTENING" | awk '{print $5}' | head -1)
  port_50051=$(netstat.exe -ano 2>/dev/null | grep ":50051 " | grep "LISTENING" | awk '{print $5}' | head -1)
  port_3000=$(netstat.exe -ano 2>/dev/null | grep ":3000 " | grep "LISTENING" | awk '{print $5}' | head -1)
  
  if [[ -n "$port_5000" ]]; then
    if [[ -f "$API_PID_FILE" ]] && [[ "$(cat "$API_PID_FILE")" == "$port_5000" ]]; then
      check "OK" "Porta 5000 (API) usada por PID $port_5000 (gerenciado)"
    else
      check "WARN" "Porta 5000 (API) usada por PID $port_5000 (NÃO gerenciado pelos scripts!)"
    fi
  else
    check "WARN" "Porta 5000 (API) livre"
  fi
  
  if [[ -n "$port_50051" ]]; then
    if [[ -f "$WORKER_PID_FILE" ]] && [[ "$(cat "$WORKER_PID_FILE")" == "$port_50051" ]]; then
      check "OK" "Porta 50051 (Worker) usada por PID $port_50051 (gerenciado)"
    else
      check "WARN" "Porta 50051 (Worker) usada por PID $port_50051 (NÃO gerenciado pelos scripts!)"
    fi
  else
    check "WARN" "Porta 50051 (Worker) livre"
  fi
  
  if [[ -n "$port_3000" ]]; then
    if [[ -f "$FRONTEND_PID_FILE" ]] && [[ "$(cat "$FRONTEND_PID_FILE")" == "$port_3000" ]]; then
      check "OK" "Porta 3000 (Frontend) usada por PID $port_3000 (gerenciado)"
    else
      check "WARN" "Porta 3000 (Frontend) usada por PID $port_3000 (NÃO gerenciado pelos scripts!)"
    fi
  else
    check "WARN" "Porta 3000 (Frontend) livre"
  fi
fi

separator "7. DEPENDÊNCIAS DO SISTEMA"

command -v python &> /dev/null && check "OK" "Python encontrado: $(python --version 2>&1)" || check "ERROR" "Python NÃO encontrado"
command -v python3 &> /dev/null && check "OK" "Python3 encontrado: $(python3 --version 2>&1)" || check "WARN" "Python3 NÃO encontrado"
command -v node &> /dev/null && check "OK" "Node.js encontrado: $(node --version 2>&1)" || check "ERROR" "Node.js NÃO encontrado"
command -v npm &> /dev/null && check "OK" "npm encontrado: $(npm --version 2>&1)" || check "ERROR" "npm NÃO encontrado"
command -v curl &> /dev/null && check "OK" "curl encontrado" || check "WARN" "curl não encontrado (health checks podem falhar)"

separator "8. LOGS RECENTES"

if [[ -f "$API_LOG" ]]; then
  api_size=$(du -h "$API_LOG" 2>/dev/null | awk '{print $1}')
  check "OK" "Log da API: $API_LOG ($api_size)"
  echo "    Últimas 3 linhas:"
  tail -n 3 "$API_LOG" 2>/dev/null | sed 's/^/    /'
else
  check "WARN" "Log da API não existe ainda"
fi

echo ""

if [[ -f "$WORKER_LOG" ]]; then
  worker_size=$(du -h "$WORKER_LOG" 2>/dev/null | awk '{print $1}')
  check "OK" "Log do Worker: $WORKER_LOG ($worker_size)"
  echo "    Últimas 3 linhas:"
  tail -n 3 "$WORKER_LOG" 2>/dev/null | sed 's/^/    /'
else
  check "WARN" "Log do Worker não existe ainda"
fi

separator "RESUMO"

echo ""
echo "Erros críticos: $ERRORS"
echo "Avisos: $WARNINGS"
echo ""

if [[ $ERRORS -gt 0 ]]; then
  echo "❌ AÇÃO NECESSÁRIA: Corrija os erros acima"
  echo ""
  echo "Comandos sugeridos:"
  echo "  bash scripts/setup_env.sh        # Criar venvs e instalar dependências"
  echo "  bash scripts/migrate_to_script_control.sh  # Migrar processos órfãos"
  exit 1
elif [[ $WARNINGS -gt 0 ]]; then
  echo "⚠ AVISOS ENCONTRADOS: Revise os avisos acima"
  echo ""
  echo "Se há processos órfãos, execute:"
  echo "  bash scripts/migrate_to_script_control.sh"
  exit 0
else
  echo "✓ TUDO OK: Sistema configurado corretamente!"
  echo ""
  echo "Comandos disponíveis:"
  echo "  bash scripts/start_dev.sh {api|worker|frontend|backend|all}"
  echo "  bash scripts/stop_dev.sh {api|worker|frontend|backend|all}"
  echo "  bash scripts/status_dev.sh"
  echo "  bash scripts/test_dev.sh"
  exit 0
fi