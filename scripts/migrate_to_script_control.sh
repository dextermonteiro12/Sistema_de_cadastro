#!/usr/bin/env bash
# scripts/migrate_to_script_control.sh - Migrar processos órfãos para controle dos scripts

source "$(dirname "$0")/_common.sh"

msg "=== DIAGNÓSTICO DE PROCESSOS ÓRFÃOS ==="

# Encontrar TODOS os processos Python e Node
python_pids=$(tasklist.exe //FI "IMAGENAME eq python.exe" //FO CSV //NH 2>/dev/null | cut -d',' -f2 | tr -d '"' | grep -E '^[0-9]+$')
node_pids=$(tasklist.exe //FI "IMAGENAME eq node.exe" //FO CSV //NH 2>/dev/null | cut -d',' -f2 | tr -d '"' | grep -E '^[0-9]+$')

echo ""
echo "Processos Python encontrados:"
echo "$python_pids" | while read pid; do
  [[ -n "$pid" ]] && echo "  PID $pid"
done

echo ""
echo "Processos Node encontrados:"
echo "$node_pids" | while read pid; do
  [[ -n "$pid" ]] && echo "  PID $pid"
done

echo ""
read -p "Deseja PARAR todos esses processos e reiniciar sob controle dos scripts? (yes/no): " confirm

if [[ "$confirm" != "yes" ]]; then
  echo "Operação cancelada."
  exit 0
fi

msg "Parando processos Python..."
echo "$python_pids" | while read pid; do
  if [[ -n "$pid" ]]; then
    taskkill.exe //F //PID "$pid" 2>/dev/null || true
  fi
done

msg "Parando processos Node..."
echo "$node_pids" | while read pid; do
  if [[ -n "$pid" ]]; then
    taskkill.exe //F //PID "$pid" 2>/dev/null || true
  fi
done

# Limpar arquivos PID antigos
rm -f "$API_PID_FILE" "$WORKER_PID_FILE" "$FRONTEND_PID_FILE"

msg "Aguardando portas liberarem..."
sleep 5

msg "Iniciando serviços sob controle dos scripts..."
bash "$(dirname "$0")/start_dev.sh" all

echo ""
msg "✓ Migração concluída!"
msg "Use agora:"
echo "  bash scripts/status_dev.sh   - Ver status"
echo "  bash scripts/stop_dev.sh     - Parar serviços"
echo "  bash scripts/start_dev.sh    - Iniciar serviços"
echo "  tail -f .run/logs/api.log    - Ver logs"