#!/usr/bin/env bash
# scripts/kill_all.sh - Matar TODOS os processos Python e Node (USE COM CUIDADO!)

echo "⚠️  ATENÇÃO: Isso vai matar TODOS os processos Python e Node no sistema!"
read -p "Tem certeza? (yes/no): " confirm

if [[ "$confirm" != "yes" ]]; then
  echo "Operação cancelada."
  exit 0
fi

echo "Matando processos Python..."
if command -v taskkill.exe &> /dev/null; then
  taskkill.exe //F //IM python.exe 2>/dev/null || echo "Nenhum processo Python encontrado"
else
  pkill -9 python 2>/dev/null || echo "Nenhum processo Python encontrado"
fi

echo "Matando processos Node..."
if command -v taskkill.exe &> /dev/null; then
  taskkill.exe //F //IM node.exe 2>/dev/null || echo "Nenhum processo Node encontrado"
else
  pkill -9 node 2>/dev/null || echo "Nenhum processo Node encontrado"
fi

# Limpar arquivos PID
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
rm -f "$ROOT_DIR/.run/pids/"*.pid

echo "✓ Todos os processos foram encerrados"
echo "Execute: bash scripts/start_dev.sh all"