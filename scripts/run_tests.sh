#!/usr/bin/env bash
# scripts/run_tests.sh - Executar testes da aplicação

set -euo pipefail
source "$(dirname "$0")/_common.sh"

msg "=== EXECUTANDO TESTES ==="

# Teste API
msg "Testando API Gateway..."
cd "$API_DIR"

if [[ ! -d ".venv" ]]; then
  error "venv não encontrado. Execute: bash scripts/setup_env.sh"
  exit 1
fi

# Verificar se diretório de testes existe
if [[ ! -d "tests" ]]; then
  error "Diretório tests/ não encontrado em $API_DIR"
  exit 1
fi

# Ativar venv e instalar pytest se necessário
if [[ -f ".venv/Scripts/python.exe" ]]; then
  msg "Instalando dependências de teste..."
  .venv/Scripts/python.exe -m pip install -q pytest pytest-cov pytest-asyncio httpx
  
  msg "Executando testes..."
  .venv/Scripts/python.exe -m pytest tests/ -v --tb=short
else
  msg "Instalando dependências de teste..."
  .venv/bin/python -m pip install -q pytest pytest-cov pytest-asyncio httpx
  
  msg "Executando testes..."
  .venv/bin/python -m pytest tests/ -v --tb=short
fi

msg "✓ Testes da API concluídos"

# Voltar para raiz
cd - > /dev/null

msg "=== TODOS OS TESTES CONCLUÍDOS ==="