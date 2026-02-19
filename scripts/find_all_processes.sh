#!/usr/bin/env bash
# scripts/find_all_processes.sh - Encontrar todos os processos Python/Node rodando

echo "=== PROCESSOS PYTHON ==="
if command -v tasklist.exe &> /dev/null; then
  # Windows
  tasklist.exe //FI "IMAGENAME eq python.exe" //FO TABLE 2>/dev/null || echo "Nenhum processo python.exe encontrado"
else
  # Unix/Linux/Mac
  ps aux | grep -i python | grep -v grep || echo "Nenhum processo Python encontrado"
fi

echo ""
echo "=== PROCESSOS NODE ==="
if command -v tasklist.exe &> /dev/null; then
  # Windows
  tasklist.exe //FI "IMAGENAME eq node.exe" //FO TABLE 2>/dev/null || echo "Nenhum processo node.exe encontrado"
else
  # Unix/Linux/Mac
  ps aux | grep -i node | grep -v grep || echo "Nenhum processo Node encontrado"
fi

echo ""
echo "=== PROCESSOS GERENCIADOS PELOS SCRIPTS ==="
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PID_DIR="$ROOT_DIR/.run/pids"

if [[ -f "$PID_DIR/api.pid" ]]; then
  echo "API (script): PID $(cat "$PID_DIR/api.pid" 2>/dev/null || echo 'N/A')"
fi

if [[ -f "$PID_DIR/worker.pid" ]]; then
  echo "Worker (script): PID $(cat "$PID_DIR/worker.pid" 2>/dev/null || echo 'N/A')"
fi

if [[ -f "$PID_DIR/frontend.pid" ]]; then
  echo "Frontend (script): PID $(cat "$PID_DIR/frontend.pid" 2>/dev/null || echo 'N/A')"
fi

echo ""
echo "=== PORTAS EM USO ==="
if command -v netstat.exe &> /dev/null; then
  # Windows - verificar portas comuns do seu sistema
  echo "Porta 5000 (API):"
  netstat.exe -ano | grep ":5000 " || echo "  Nenhuma conexão"
  echo "Porta 50051 (gRPC Worker):"
  netstat.exe -ano | grep ":50051 " || echo "  Nenhuma conexão"
  echo "Porta 3000 (Frontend React):"
  netstat.exe -ano | grep ":3000 " || echo "  Nenhuma conexão"
else
  # Unix/Linux/Mac
  echo "Porta 5000 (API):"
  lsof -i :5000 || echo "  Nenhuma conexão"
  echo "Porta 50051 (gRPC Worker):"
  lsof -i :50051 || echo "  Nenhuma conexão"
  echo "Porta 3000 (Frontend React):"
  lsof -i :3000 || echo "  Nenhuma conexão"
fi