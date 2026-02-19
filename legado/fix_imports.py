#!/usr/bin/env python3
"""
Script para resolver conflito de imports e migrar para v2.0
Execute: python fix_imports.py
"""

import os
from pathlib import Path

print("=" * 70)
print("CORRIGINDO CONFLITO DE IMPORTS")
print("=" * 70 + "\n")

# ===== OPÇÃO 1: FAZER BACKUP DO ANTIGO E USAR O NOVO =====
print("[1/3] Fazendo backup de config.py antigo...")

config_antigo = Path('config.py')
if config_antigo.exists():
    # Fazer backup
    backup_path = Path('config_backup.py')
    config_antigo.rename(backup_path)
    print(f"✓ Backup criado: config_backup.py")
else:
    print("✓ config.py já não existe")

# ===== OPÇÃO 2: ATUALIZAR IMPORTS NAS ROTAS =====
print("\n[2/3] Atualizando imports nos arquivos legados...")

# Arquivos que precisam ser alterados
files_to_update = [
    'Routes/movimentacoes.py',
    'Routes/clientes.py',
    'Routes/ambiente.py',
    'Routes/monitoramento.py',
    'Routes/home.py',
    'Routes/cargacotit.py'
]

for file_path in files_to_update:
    if Path(file_path).exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Substituir imports
        # De: from config import Config, get_connection_string
        # Para: from utils import get_connection_string
        
        original_content = content
        
        # Remover ou comentar import de Config (não mais necessário)
        content = content.replace('from config import Config\n', '')
        content = content.replace('from config import Config', '')
        
        # Manter get_connection_string de utils
        if 'get_connection_string' not in content and 'from utils import' not in content:
            # Adicionar import de utils se não existir
            lines = content.split('\n')
            import_idx = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    import_idx = i + 1
                else:
                    break
            
            lines.insert(import_idx, 'from utils import get_connection_string')
            content = '\n'.join(lines)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ {file_path}")
        else:
            print(f"⊘ {file_path} (sem mudanças)")
    else:
        print(f"⚠️  {file_path} não encontrado")

# ===== OPÇÃO 3: USAR O NOVO SISTEMA V2.0 =====
print("\n[3/3] Próximos passos para v2.0...")

print("""
Para usar o novo sistema v2.0 (FastAPI + Pool Dinâmico):

1. PARAR de executar App.py (Flask antigo)
2. INICIAR api-gateway/main.py (FastAPI novo)
   
   Comando:
   cd api-gateway
   uvicorn main:app --reload --port 5000

3. O frontend agora usa endpoints novos:
   POST /config/validar       → Valida DB
   POST /config/teste         → Testa conexão
   GET  /config/status/{key}  → Vê status
   
4. Todos os dados vêm do frontend via /config/validar
   Não precisa mais de .env com credenciais SQL

5. Se AINDA PRECISAR usar App.py (Flask antigo):
   Adicione isto ao topo do seu App.py:
""")

print("""
   import sys
   sys.path.insert(0, 'utils')  # Para resolver imports
""")

print("\n" + "=" * 70)
print("✅ CORREÇÃO CONCLUÍDA")
print("=" * 70)
print()
print("Qual opção você escolhe?")
print()
print("  A) Usar FastAPI v2.0 (RECOMENDADO)")
print("     uvicorn api-gateway.main:app --reload --port 5000")
print()
print("  B) Continuar com Flask antigo")
print("     python App.py")
print()
print("=" * 70)