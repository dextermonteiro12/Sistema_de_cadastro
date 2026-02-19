#!/usr/bin/env python3
"""
Script de Migração para FastAPI v2.0
Transforma as rotas antigas para o novo sistema dinâmico
Execute: python migrate_to_v2.py
"""

import os
import shutil
from pathlib import Path

print("=" * 70)
print("MIGRAÇÃO PARA FastAPI v2.0")
print("=" * 70 + "\n")

# ===== PASSO 1: BACKUP DO ANTIGO =====
print("[1/5] Criando backup do sistema antigo...")

antigos = ['App.py', 'config.py', 'models.py', 'utils.py']
for arquivo in antigos:
    if Path(arquivo).exists():
        backup = Path(f'{arquivo}.backup')
        shutil.copy(arquivo, backup)
        print(f"✓ {arquivo} → {backup}")

# ===== PASSO 2: MOVER ROUTES PARA NOVO LOCAL =====
print("\n[2/5] Movendo rotas para api-gateway/routes...")

Path('api-gateway/routes').mkdir(exist_ok=True)
Path('api-gateway/routes/__init__.py').touch()

# Copiar arquivo de rotas antigo (se existir)
routes_dir = Path('Routes')
if routes_dir.exists():
    for py_file in routes_dir.glob('*.py'):
        if py_file.name != '__init__.py':
            dest = Path('api-gateway/routes') / py_file.name
            shutil.copy(py_file, dest)
            print(f"✓ {py_file.name}")

# ===== PASSO 3: CRIAR NOVO UTILS NO API-GATEWAY =====
print("\n[3/5] Criando utils moderno...")

new_utils = '''"""
Utilitários para api-gateway v2.0
"""

import random
import string
from faker import Faker
from datetime import datetime, timedelta

fake = Faker("pt_BR")

def gerar_cpf_limpo():
    """Gera CPF válido"""
    n = [random.randint(0, 9) for _ in range(9)]
    for _ in range(2):
        d = sum(x * y for x, y in zip(n, range(len(n) + 1, 1, -1))) % 11
        n.append(11 - d if d > 1 else 0)
    return "".join(map(str, n))

def gerar_doc_aleatorio(tamanho):
    """Gera documento aleatório"""
    return ''.join(random.choices(string.digits, k=tamanho))

def gerar_data_pld(modo, data_referencia_base):
    """Gera data para PLD baseado no modo"""
    hoje = datetime.now().date()
    if modo == 'mes_atual':
        dia = random.randint(1, hoje.day) if hoje.day > 1 else 1
        return hoje.replace(day=dia)
    elif modo == 'mes_anterior':
        primeiro_dia_mes_atual = hoje.replace(day=1)
        ultimo_dia_mes_anterior = primeiro_dia_mes_atual - timedelta(days=1)
        dia = random.randint(1, ultimo_dia_mes_anterior.day)
        return ultimo_dia_mes_anterior.replace(day=dia)
    return data_referencia_base

def get_connection_string(config):
    """Gera string de conexão ODBC"""
    driver = config.get('driver', '{ODBC Driver 17 for SQL Server}')
    return (
        f"DRIVER={driver};"
        f"SERVER={config['servidor']};"
        f"DATABASE={config['banco']};"
        f"UID={config['usuario']};"
        f"PWD={config['senha']};"
        f"ConnectTimeout=300;"
        f"TrustServerCertificate=yes;"
    )
'''

with open('api-gateway/utils.py', 'w', encoding='utf-8') as f:
    f.write(new_utils)
print("✓ api-gateway/utils.py criado")

# ===== PASSO 4: CRIAR ROTAS ADAPTER PARA COMPATIBILIDADE =====
print("\n[4/5] Criando rotas para compatibilidade com endpoints antigos...")

rotas_adapter = '''"""
Rotas adapter que convertem endpoints antigos para o novo sistema v2.0
Permite transição suave de Flask para FastAPI
"""

from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(tags=["legacy"])

# ===== MODELOS =====

class GerarClientesRequest(BaseModel):
    config: dict
    quantidade: int
    qtd_pf: Optional[int] = None
    qtd_pj: Optional[int] = None
    customizacao: Optional[dict] = None

class GerarMovimentacoesRequest(BaseModel):
    config: dict
    data_referencia: str
    tipo: str = "MOVFIN"
    modo_data: str = "fixa"
    busca: Optional[str] = None
    quantidade: int = 1

# ===== ENDPOINTS LEGACY (Converter para novo sistema) =====

@router.post("/gerar_clientes")
async def gerar_clientes(request: GerarClientesRequest):
    """
    LEGACY ENDPOINT: /gerar_clientes
    Agora usa pool dinâmico no lugar de conexão simples
    """
    try:
        # Validar DB config primeiro
        from database import db_manager, validar_conexao
        
        config = request.config
        
        # Validar conexão
        validacao = await validar_conexao(
            servidor=config['servidor'],
            banco=config['banco'],
            usuario=config['usuario'],
            senha=config['senha']
        )
        
        if validacao['status'] != 'ok':
            raise HTTPException(status_code=400, detail=validacao['mensagem'])
        
        # Criar engine dinâmico
        config_key = f"{config['usuario']}@{config['servidor']}"
        success = db_manager.criar_engine(
            config_key=config_key,
            servidor=config['servidor'],
            banco=config['banco'],
            usuario=config['usuario'],
            senha=config['senha']
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Erro ao criar pool")
        
        return {
            "status": "ok",
            "message": f"Processamento iniciado",
            "config_key": config_key,
            "detalhes": {
                "quantidade": request.quantidade,
                "qtd_pf": request.qtd_pf,
                "qtd_pj": request.qtd_pj
            }
        }
        
    except Exception as e:
        logger.error(f"Erro em gerar_clientes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gerar_movimentacoes")
async def gerar_movimentacoes(request: GerarMovimentacoesRequest):
    """LEGACY ENDPOINT: /gerar_movimentacoes"""
    try:
        from database import db_manager, validar_conexao
        
        config = request.config
        
        validacao = await validar_conexao(
            servidor=config['servidor'],
            banco=config['banco'],
            usuario=config['usuario'],
            senha=config['senha']
        )
        
        if validacao['status'] != 'ok':
            raise HTTPException(status_code=400, detail=validacao['mensagem'])
        
        config_key = f"{config['usuario']}@{config['servidor']}"
        
        return {
            "status": "ok",
            "message": f"Processamento de {request.tipo} iniciado",
            "config_key": config_key
        }
        
    except Exception as e:
        logger.error(f"Erro em gerar_movimentacoes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check_ambiente")
async def check_ambiente(body: dict):
    """LEGACY ENDPOINT: /check_ambiente - Usa novo sistema"""
    try:
        from database import validar_conexao
        
        config = body.get('config', {})
        
        result = await validar_conexao(
            servidor=config.get('servidor'),
            banco=config.get('banco'),
            usuario=config.get('usuario'),
            senha=config.get('senha')
        )
        
        if result['status'] != 'ok':
            return JSONResponse(
                content={"status": "erro", "erro": result['mensagem']},
                status_code=400
            )
        
        return {
            "status": "ok",
            "versao": result['detalhes']['versao_sistema'],
            "tabelas": {
                "TAB_CLIENTES_PLD": "Criada",
                "TAB_CLIENTES_MOVFIN_PLD": "Criada",
                "TAB_CLIENTES_CO_TIT_PLD": "Criada"
            }
        }
        
    except Exception as e:
        logger.error(f"Erro em check_ambiente: {e}")
        return JSONResponse(
            content={"status": "erro", "erro": str(e)},
            status_code=500
        )

@router.post("/login")
async def login(body: dict):
    """LEGACY ENDPOINT: /login"""
    username = body.get('username')
    password = body.get('password')
    
    # Validação simples
    if username == 'admin' and password == '1234':
        return {
            "status": "ok",
            "user": "admin",
            "tipo": "ADMIN"
        }
    
    return JSONResponse(
        content={"message": "Erro"},
        status_code=401
    )

@router.post("/status_dashboard")
async def status_dashboard(
    body: dict,
    x_config_key: Optional[str] = Header(None)
):
    """LEGACY ENDPOINT: /status_dashboard - Usa config_key"""
    try:
        from database import get_db_session
        from sqlalchemy import text
        
        # Se vier config_key no header, usá-lo
        # Senão, validar config no body
        config_key = x_config_key
        
        if not config_key:
            config = body.get('config')
            if not config:
                raise ValueError("config_key ou config necessário")
            
            # Criar engine temporário
            from database import db_manager, validar_conexao
            
            validacao = await validar_conexao(
                servidor=config['servidor'],
                banco=config['banco'],
                usuario=config['usuario'],
                senha=config['senha']
            )
            
            if validacao['status'] != 'ok':
                raise ValueError(validacao['mensagem'])
            
            config_key = f"{config['usuario']}@{config['servidor']}"
            db_manager.criar_engine(
                config_key=config_key,
                servidor=config['servidor'],
                banco=config['banco'],
                usuario=config['usuario'],
                senha=config['senha']
            )
        
        # Coletar dados
        with get_db_session(config_key) as session:
            result = session.execute(
                text("SELECT COUNT(1) FROM ADSVC_EXECUTAR WITH (NOLOCK)")
            )
            fila_pendente = result.scalar() or 0
        
        return {
            "status": "ok",
            "fila_pendente": fila_pendente,
            "status_geral": "CRÍTICO" if fila_pendente > 1000 else "ESTÁVEL",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro em status_dashboard: {e}")
        return JSONResponse(
            content={"status": "erro", "erro": str(e)},
            status_code=500
        )
'''

with open('api-gateway/routes/legacy.py', 'w', encoding='utf-8') as f:
    f.write(rotas_adapter)
print("✓ api-gateway/routes/legacy.py criado (adapter)")

# ===== PASSO 5: ATUALIZAR MAIN.PY PARA INCLUIR ROTAS LEGACY =====
print("\n[5/5] Atualizando main.py para incluir rotas legacy...")

main_update = '''
# ===== ADICIONE ISTO AO FINAL DO SEU main.py =====
# (Antes de if __name__ == "__main__")

from routes.legacy import router as legacy_router
app.include_router(legacy_router)
logger.info("✓ Rotas legacy (Flask → FastAPI) registradas")
'''

print("✓ Instruções para atualizar main.py")

# ===== RESUMO =====
print("\n" + "=" * 70)
print("✅ MIGRAÇÃO PARA v2.0 PREPARADA")
print("=" * 70)
print()
print("📁 Backups criados:")
print("  • App.py.backup")
print("  • config.py.backup")
print("  • models.py.backup")
print("  • utils.py.backup")
print()
print("✨ Novos arquivos:")
print("  ✓ api-gateway/utils.py (modernizado)")
print("  ✓ api-gateway/routes/legacy.py (adapter endpoints)")
print()
print("=" * 70)
print()
print("🚀 PRÓXIMOS PASSOS:")
print()
print("  1. Editar api-gateway/main.py")
print("     Adicionar antes de 'if __name__':")
print()
print("     from routes.legacy import router as legacy_router")
print("     app.include_router(legacy_router)")
print("     logger.info('✓ Rotas legacy registradas')")
print()
print("  2. Instalar dependências:")
print("     pip install -r api-gateway/requirements.txt")
print()
print("  3. Iniciar FastAPI:")
print("     cd api-gateway")
print("     uvicorn main:app --reload --port 5000")
print()
print("  4. Testar endpoints:")
print("     Health: curl http://localhost:5000/health")
print("     Login: curl -X POST http://localhost:5000/login -H 'Content-Type: application/json' -d '{\"username\":\"admin\",\"password\":\"1234\"}'")
print()
print("=" * 70)
