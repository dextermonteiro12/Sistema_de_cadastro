#!/usr/bin/env python3
"""
Script de Auto-Implementação da Arquitetura v2.0
Cria toda a estrutura de pastas e arquivos necessários
"""

import os
import sys
from pathlib import Path

# cores para output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RED = '\033[91m'
    ENDC = '\033[0m'

def criar_pasta(caminho):
    """Cria pasta se não existir"""
    Path(caminho).mkdir(parents=True, exist_ok=True)
    print(f"{Colors.GREEN}✓{Colors.ENDC} Pasta criada: {caminho}")

def criar_arquivo(caminho, conteudo):
    """Cria arquivo com conteúdo"""
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print(f"{Colors.GREEN}✓{Colors.ENDC} Arquivo criado: {caminho}")

def main():
    base_dir = Path.cwd()
    
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"SETUP v2.0 - Arquitetura de Alta Performance")
    print(f"{'='*60}{Colors.ENDC}\n")
    
    # ===== PASSO 1: Criar Estrutura de Pastas =====
    print(f"{Colors.YELLOW}[1/12] Criando estrutura de pastas...{Colors.ENDC}")
    
    pastas = [
        'api-gateway',
        'api-gateway/resolvers',
        'api-gateway/middleware',
        'microservice-worker',
        'microservice-worker/services',
        'microservice-worker/protos',
        'config',
        'static',
    ]
    
    for pasta in pastas:
        criar_pasta(base_dir / pasta)
    
    # ===== PASSO 2: Criar database.py =====
    print(f"\n{Colors.YELLOW}[2/12] Configurando Pool de Conexões SQLAlchemy...{Colors.ENDC}")
    
    database_py = '''"""
Configuração de Pool de Conexões SQL Server com SQLAlchemy
"""
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import os
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'mssql+pyodbc://usuario:senha@servidor/banco?driver=ODBC+Driver+17+for+SQL+Server'
)

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,
    connect_args={
        'timeout': 30,
        'isolation_level': 'READ COMMITTED',
        'TrustServerCertificate': 'yes',
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

async def check_db_health() -> dict:
    try:
        with get_db_session() as session:
            session.execute(text("SELECT 1"))
        return {"status": "healthy", "message": "✓ Banco respondendo"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

def close_db():
    engine.dispose()
'''
    criar_arquivo(base_dir / 'api-gateway/database.py', database_py)

    # ===== PASSO 3: Criar requirements.txt =====
    requirements_txt = '''fastapi==0.104.1\nuvicorn==0.24.0\npydantic==2.5.0\nstrawberry-graphql==0.220.0\nsqlalchemy==2.0.23\npyodbc==5.1.0\npython-dotenv==1.0.0\ngrpcio==1.59.2\nFaker==20.1.1'''
    criar_arquivo(base_dir / 'api-gateway/requirements.txt', requirements_txt)

    # ===== PASSO 4: Criar config.py =====
    config_py = '''import os\nfrom dataclasses import dataclass\n@dataclass\nclass AppConfig:\n    api_title: str = "PLD API v2.0"\n    api_version: str = "2.0.0"\n    cors_origins: list = ["*"]\nconfig = AppConfig()'''
    criar_arquivo(base_dir / 'config/config.py', config_py)

    # ===== PASSO 5: Criar main.py FastAPI =====
    main_py = '''from fastapi import FastAPI\napp = FastAPI()\n@app.get("/")\ndef read_root(): return {"status": "online"}'''
    criar_arquivo(base_dir / 'api-gateway/main.py', main_py)

    # (Nota: Omiti aqui os textos longos das outras variáveis para brevidade, mas o seu código original deve ser mantido)

    # ===== PASSO 12: Criar README.md (Onde o erro ocorria) =====
    print(f"\n{Colors.YELLOW}[12/12] Finalizando README.md...{Colors.ENDC}")
    
    readme_content = '''# 🚀 PLD Data Generator v2.0 - Arquitetura de Alta Performance

## 🏗️ Estrutura do Projeto
O projeto foi organizado para suportar alta carga e processamento distribuído.

## 🚀 Como Iniciar
1. Configure seu `.env` com as credenciais do SQL Server.
2. Instale as dependências: `pip install -r api-gateway/requirements.txt`
3. Execute a API: `python api-gateway/main.py`
'''
    criar_arquivo(base_dir / 'README.md', readme_content)

    print(f"\n{Colors.GREEN}{'='*60}")
    print(f"✅ ESTRUTURA v2.0 CRIADA COM SUCESSO!")
    print(f"{'='*60}{Colors.ENDC}\n")

# ESSENCIAL PARA O SCRIPT RODAR:
if __name__ == "__main__":
    main()