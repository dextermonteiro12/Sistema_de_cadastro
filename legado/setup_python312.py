#!/usr/bin/env python3
"""
Setup completo para Python 3.12
Execute: python setup_python312.py
"""

import subprocess
import sys
import os
from pathlib import Path

print("=" * 70)
print(f"SETUP PYTHON {sys.version_info.major}.{sys.version_info.minor}")
print("=" * 70 + "\n")

# ===== VERIFICAÇÃO =====
print(f"✓ Python: {sys.version}")
print(f"✓ Executable: {sys.executable}\n")

if sys.version_info < (3, 12):
    print("⚠️  Aviso: Python < 3.12. Recomenda-se usar 3.12+")
    print("Ative o venv com Python 3.12 primeiro:")
    print("  source venv312/bin/activate")
    sys.exit(1)

# ===== REQUIREMENTS COMPATÍVEL COM 3.12 =====
print("[1/3] Criando requirements compatível...")

requirements = '''# ===== BACKEND MODERNO =====
fastapi>=0.115.0
uvicorn>=0.30.0
pydantic>=2.10.0

# ===== GRAPHQL =====
strawberry-graphql>=0.230.0
strawberry-graphql[asgi]>=0.230.0

# ===== DATABASE =====
sqlalchemy>=2.0.23
pyodbc>=5.3.0
python-dotenv>=1.0.0

# ===== gRPC =====
grpcio>=1.60.0
grpcio-tools>=1.60.0

# ===== UTILITÁRIOS =====
Faker>=20.1.0
pydantic-core>=2.14.0
annotated-types>=0.6.0

# ===== PERFORMANCE =====
slowapi>=0.1.9
redis>=5.0.1
pybreaker>=1.4.0

# ===== MONITORING =====
prometheus-client>=0.19.0
python-json-logger>=2.0.7

# ===== DESENVOLVIMENTO =====
black>=23.12.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
'''

with open('api-gateway/requirements.txt', 'w', encoding='utf-8') as f:
    f.write(requirements)

print("✓ requirements.txt criado (compatível com Python 3.12)")

# ===== UPGRADE PIP =====
print("\n[2/3] Atualizando pip, setuptools, wheel...")

subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel'], 
               capture_output=True)
print("✓ pip atualizado")

# ===== INSTALAR DEPENDÊNCIAS =====
print("\n[3/3] Instalando dependências...")
print("(Isto pode levar 2-3 minutos...)\n")

result = subprocess.run(
    [sys.executable, '-m', 'pip', 'install', '-r', 'api-gateway/requirements.txt'],
    cwd='.'
)

if result.returncode == 0:
    print("\n" + "=" * 70)
    print("✅ SETUP CONCLUÍDO COM SUCESSO")
    print("=" * 70 + "\n")
    
    # ===== TESTE FINAL =====
    print("TESTANDO IMPORTS...\n")
    
    sys.path.insert(0, 'api-gateway')
    
    try:
        print("[1/3] FastAPI...", end=' ')
        from fastapi import FastAPI
        print("✓")
        
        print("[2/3] SQLAlchemy...", end=' ')
        from sqlalchemy import create_engine, text
        print("✓")
        
        print("[3/3] Strawberry GraphQL...", end=' ')
        import strawberry
        print("✓")
        
        print("\n" + "=" * 70)
        print("✅ TUDO FUNCIONANDO!")
        print("=" * 70 + "\n")
        
        print("🚀 PRÓXIMOS PASSOS:\n")
        print("1. Editar .env se necessário")
        print("   nano .env  ou  code .env\n")
        
        print("2. Iniciar servidor FastAPI:")
        print("   cd api-gateway")
        print("   uvicorn main:app --reload --port 5000\n")
        
        print("3. Acessar endpoints:")
        print("   • Health: http://localhost:5000/health")
        print("   • GraphQL: http://localhost:5000/graphql")
        print("   • Docs: http://localhost:5000/docs\n")
        
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Erro ao testar: {e}")
        print("\nTente executar novamente:")
        print("  python setup_python312.py")
        sys.exit(1)
        
else:
    print("\n❌ Erro na instalação de dependências")
    print("\nTente manualmente:")
    print("  pip install -r api-gateway/requirements.txt")
    sys.exit(1)