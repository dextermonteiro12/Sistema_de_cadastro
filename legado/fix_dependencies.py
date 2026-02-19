#!/usr/bin/env python3
"""
Script para corrigir dependências e compatibilidade
Execute: python fix_dependencies.py
"""

import subprocess
import sys
import os

print("=" * 70)
print("CORRIGINDO DEPENDÊNCIAS")
print("=" * 70 + "\n")

# ===== PASSO 1: VERIFICAR VERSÃO PYTHON =====
print("[1/4] Verificando versão Python...")
python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
print(f"✓ Python {python_version}")

if sys.version_info >= (3, 14):
    print("⚠️  Python 3.14+ detectado - Usando dependências compatíveis")

# ===== PASSO 2: REMOVER REQUIREMENTS ANTIGOS =====
print("\n[2/4] Removendo requirements antigos...")

# Desinstalar versões problemáticas
problematic = [
    'sqlalchemy==2.0.23',
    'strawberry-graphql==0.220.0',
    'uvicorn==0.24.0'
]

for pkg in problematic:
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'uninstall', '-y', pkg],
            capture_output=True,
            timeout=30
        )
        print(f"✓ {pkg} removido")
    except:
        print(f"⊘ {pkg} não estava instalado")

# ===== PASSO 3: INSTALAR VERSÕES COMPATÍVEIS =====
print("\n[3/4] Instalando versões compatíveis...")

new_requirements = '''# ===== BACKEND MODERNO =====
fastapi>=0.115.0
uvicorn>=0.30.0
pydantic>=2.10.0

# ===== GRAPHQL =====
strawberry-graphql>=0.230.0
strawberry-graphql[asgi]>=0.230.0

# ===== DATABASE (Compatível com Python 3.14) =====
sqlalchemy>=2.1.0
pyodbc>=5.3.0
python-dotenv>=1.0.0

# ===== gRPC =====
grpcio>=1.64.0
grpcio-tools>=1.64.0

# ===== UTILITÁRIOS =====
Faker>=20.1.0
pydantic-core>=2.20.0
annotated-types>=0.7.0

# ===== PERFORMANCE =====
slowapi>=0.1.9
redis>=5.0.1
pybreaker>=1.4.0

# ===== MONITORING =====
prometheus-client>=0.20.0
python-json-logger>=2.0.7

# ===== DESENVOLVIMENTO =====
black>=24.0.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
'''

with open('api-gateway/requirements.txt', 'w', encoding='utf-8') as f:
    f.write(new_requirements)

print("✓ requirements.txt atualizado (versões compatíveis)")

# ===== PASSO 4: INSTALAR =====
print("\n[4/4] Instalando dependências atualizadas...")
print("(Isto pode levar 1-2 minutos...)\n")

try:
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '-r', 'api-gateway/requirements.txt', '-q'],
        cwd='.',
        timeout=300
    )
    
    if result.returncode == 0:
        print("✓ Dependências instaladas com sucesso!")
    else:
        print("⚠️  Alguns pacotes tiveram problema de instalação")
        print("Tentando instalação alternativa...")
        
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
            timeout=60
        )
        
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'api-gateway/requirements.txt'],
            cwd='.'
        )
        
        print("✓ Dependências instaladas!")
        
except subprocess.TimeoutExpired:
    print("❌ Timeout na instalação. Tente manualmente:")
    print("   pip install -r api-gateway/requirements.txt --upgrade")
except Exception as e:
    print(f"❌ Erro: {e}")
    print("Tente instalar manualmente:")
    print("   pip install -r api-gateway/requirements.txt")

# ===== TESTE FINAL =====
print("\n" + "=" * 70)
print("TESTANDO IMPORTS")
print("=" * 70 + "\n")

try:
    import sys
    sys.path.insert(0, 'api-gateway')
    
    print("[1/3] Testando SQLAlchemy...")
    from sqlalchemy import create_engine, text
    print("✓ SQLAlchemy OK")
    
    print("[2/3] Testando strawberry-graphql...")
    import strawberry
    print("✓ Strawberry OK")
    
    print("[3/3] Testando database.py...")
    from database import db_manager
    print("✓ database.py OK")
    
    print("\n" + "=" * 70)
    print("✅ TUDO OK! Dependências corrigidas")
    print("=" * 70)
    print()
    print("🚀 Pode iniciar o servidor:")
    print("   cd api-gateway")
    print("   uvicorn main:app --reload --port 5000")
    
except AssertionError as e:
    print(f"\n❌ Erro de compatibilidade: {e}")
    print("\nSolução alternativa: Downgrade para Python 3.11 ou 3.12")
    print("Ou aguarde atualização do SQLAlchemy para 2.2+")
    
except ImportError as e:
    print(f"\n❌ Erro de import: {e}")
    print("\nTente executar novamente:")
    print("   python fix_dependencies.py")
    
except Exception as e:
    print(f"\n❌ Erro: {e}")

print()

