#!/usr/bin/env python3
"""
Script para criar sistema de configuração dinâmica
Execute: python dynamic_config.py
"""

import os
from pathlib import Path

def criar_arquivo(caminho, conteudo):
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print(f"✓ {caminho}")

print("=" * 70)
print("CONFIGURANDO SISTEMA DINÂMICO DE CONFIG")
print("=" * 70 + "\n")

# ===== 1. NOVO database.py COM SUPORTE A MÚLTIPLAS CONEXÕES =====
print("[1/4] Atualizando api-gateway/database.py...")

database_py = '''"""
Gerenciador de Pool de Conexões com configuração dinâmica
Suporta múltiplas conexões do frontend
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator, Dict, Optional
import os
import logging
from threading import Lock

logger = logging.getLogger(__name__)

# ===== GERENCIADOR DE ENGINES DINÂMICOS =====
class DynamicConnectionManager:
    """
    Gerencia múltiplas engines de banco de dados
    Permite que cada cliente (front) conecte ao seu próprio servidor SQL
    """
    
    def __init__(self):
        self.engines: Dict[str, any] = {}
        self.session_makers: Dict[str, sessionmaker] = {}
        self.lock = Lock()
    
    def criar_engine(
        self,
        config_key: str,
        servidor: str,
        banco: str,
        usuario: str,
        senha: str,
        driver: str = "{ODBC Driver 17 for SQL Server}",
        pool_size: int = 10,
        max_overflow: int = 20
    ):
        """
        Cria um novo engine com pool de conexões
        
        Args:
            config_key: Identificador único (ex: "user_123")
            servidor: Servidor SQL Server
            banco: Nome do banco de dados
            usuario: Usuário SQL
            senha: Senha SQL
            driver: Driver ODBC
            pool_size: Tamanho do pool
            max_overflow: Máximo overflow
        
        Returns:
            bool: True se sucesso, False se erro
        """
        with self.lock:
            try:
                # Construir URL de conexão
                connection_url = (
                    f"mssql+pyodbc://{usuario}:{senha}@"
                    f"{servidor}/{banco}"
                    f"?driver={driver}&TrustServerCertificate=yes"
                )
                
                # Criar engine
                engine = create_engine(
                    connection_url,
                    poolclass=QueuePool,
                    pool_size=pool_size,
                    max_overflow=max_overflow,
                    pool_recycle=3600,
                    pool_pre_ping=True,
                    connect_args={
                        'timeout': 30,
                        'isolation_level': 'READ COMMITTED',
                        'TrustServerCertificate': 'yes',
                        'ConnectTimeout': 300,
                    },
                    echo=False
                )
                
                # Testar conexão
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                
                # Armazenar
                self.engines[config_key] = engine
                self.session_makers[config_key] = sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=engine
                )
                
                logger.info(f"✓ Engine criado: {config_key}")
                logger.info(f"  Servidor: {servidor}")
                logger.info(f"  Banco: {banco}")
                logger.info(f"  Pool: {pool_size} + {max_overflow}")
                
                return True
                
            except Exception as e:
                logger.error(f"✗ Erro ao criar engine {config_key}: {str(e)}")
                return False
    
    def obter_engine(self, config_key: str):
        """Obtém engine existente"""
        if config_key not in self.engines:
            logger.error(f"Engine não encontrado: {config_key}")
            return None
        return self.engines[config_key]
    
    def obter_session_maker(self, config_key: str):
        """Obtém session maker do engine"""
        if config_key not in self.session_makers:
            logger.error(f"Session maker não encontrado: {config_key}")
            return None
        return self.session_makers[config_key]
    
    def listar_engines(self):
        """Lista todos os engines ativos"""
        return list(self.engines.keys())
    
    def fechar_engine(self, config_key: str):
        """Fecha engine específico"""
        with self.lock:
            if config_key in self.engines:
                self.engines[config_key].dispose()
                del self.engines[config_key]
                del self.session_makers[config_key]
                logger.info(f"✓ Engine fechado: {config_key}")
    
    def fechar_todos(self):
        """Fecha todos os engines"""
        with self.lock:
            for config_key in list(self.engines.keys()):
                self.engines[config_key].dispose()
            self.engines.clear()
            self.session_makers.clear()
            logger.info("✓ Todos os engines fechados")

# ===== INSTÂNCIA GLOBAL =====
db_manager = DynamicConnectionManager()

# ===== CONTEXT MANAGER PARA SESSÕES =====
@contextmanager
def get_db_session(config_key: str) -> Generator[Session, None, None]:
    """
    Context manager para usar sessão com engine específico
    
    Usage:
        with get_db_session("user_123") as session:
            session.execute(text("SELECT * FROM tabela"))
    """
    session_maker = db_manager.obter_session_maker(config_key)
    
    if session_maker is None:
        raise ValueError(f"Configuração não encontrada: {config_key}")
    
    session = session_maker()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        session.close()

# ===== FUNÇÃO PARA VALIDAR CONEXÃO =====
async def validar_conexao(
    servidor: str,
    banco: str,
    usuario: str,
    senha: str,
    driver: str = "{ODBC Driver 17 for SQL Server}"
) -> dict:
    """
    Valida conexão com SQL Server
    
    Returns:
        {
            "status": "ok" | "erro",
            "mensagem": "...",
            "versao": "V8" ou "V9" (se OK),
            "detalhes": {...}
        }
    """
    try:
        # Criar engine temporário
        connection_url = (
            f"mssql+pyodbc://{usuario}:{senha}@"
            f"{servidor}/{banco}"
            f"?driver={driver}&TrustServerCertificate=yes"
        )
        
        temp_engine = create_engine(
            connection_url,
            connect_args={
                'timeout': 10,
                'TrustServerCertificate': 'yes'
            }
        )
        
        # Testar conexão
        with temp_engine.connect() as conn:
            # Verificar versão do sistema
            try:
                result = conn.execute(
                    text("SELECT TOP 1 CD_VERSAO FROM AD_SISTEMAS_VERSOES WITH (NOLOCK) ORDER BY 1 DESC")
                )
                row = result.fetchone()
                versao = "V9" if row and "009" in str(row[0]) else "V8"
            except:
                versao = "V8"
            
            # Verificar tabelas
            result = conn.execute(
                text("SELECT COUNT(*) FROM sys.tables WHERE name LIKE 'TAB_CLIENTES%'")
            )
            qtd_tabelas = result.scalar() or 0
        
        temp_engine.dispose()
        
        return {
            "status": "ok",
            "mensagem": "✓ Conexão validada com sucesso",
            "versao": versao,
            "detalhes": {
                "servidor": servidor,
                "banco": banco,
                "versao_sistema": versao,
                "tabelas_pld": qtd_tabelas
            }
        }
        
    except Exception as e:
        error_msg = str(e)
        
        # Mensagens de erro mais claras
        if "login failed" in error_msg.lower():
            erro = "Usuário ou senha incorretos"
        elif "cannot open database" in error_msg.lower():
            erro = "Banco de dados não encontrado"
        elif "connection timeout" in error_msg.lower():
            erro = "Timeout - Servidor não responde"
        elif "named instance not found" in error_msg.lower():
            erro = "Instância SQL não encontrada"
        else:
            erro = error_msg
        
        return {
            "status": "erro",
            "mensagem": f"✗ Erro ao conectar: {erro}",
            "detalhes": {
                "servidor": servidor,
                "banco": banco,
                "erro_completo": error_msg
            }
        }

# ===== HEALTH CHECK =====
async def check_db_health(config_key: str) -> dict:
    """Verifica saúde da conexão específica"""
    try:
        with get_db_session(config_key) as session:
            session.execute(text("SELECT 1"))
        
        engine = db_manager.obter_engine(config_key)
        return {
            "status": "healthy",
            "message": "✓ Banco respondendo",
            "pool_size": engine.pool.size(),
            "pool_checked_out": engine.pool.checkedout()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "✗ Erro ao conectar"
        }

# ===== ENGINE DEFAULT (para compatibilidade) =====
# Se houver .env, criar engine padrão
DEFAULT_CONFIG_KEY = "default"

default_db_url = os.getenv('DATABASE_URL', None)
if default_db_url:
    try:
        default_engine = create_engine(
            default_db_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            pool_pre_ping=True
        )
        db_manager.engines[DEFAULT_CONFIG_KEY] = default_engine
        db_manager.session_makers[DEFAULT_CONFIG_KEY] = sessionmaker(
            bind=default_engine
        )
        logger.info(f"✓ Engine padrão carregado do .env")
    except Exception as e:
        logger.warning(f"⚠️  Sem engine padrão: {e}")

def close_db():
    """Fecha todos os engines"""
    db_manager.fechar_todos()
'''

criar_arquivo('api-gateway/database.py', database_py)

# ===== 2. NOVO ENDPOINT DE CONFIGURAÇÃO =====
print("[2/4] Criando api-gateway/routes/config.py...")

config_routes = '''"""
Rotas para gerenciar configuração de banco de dados
"""

from fastapi import APIRouter, HTTPException, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from database import db_manager, validar_conexao, check_db_health

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["configuration"])

# ===== MODELOS PYDANTIC =====

class DatabaseConfig(BaseModel):
    """Modelo para configuração de banco"""
    servidor: str
    banco: str
    usuario: str
    senha: str
    driver: str = "{ODBC Driver 17 for SQL Server}"

class ValidarConfigRequest(BaseModel):
    """Request para validar configuração"""
    config: DatabaseConfig

# ===== ENDPOINTS =====

@router.post("/validar")
async def validar_configuracao(request: ValidarConfigRequest):
    """
    Valida configuração de banco de dados do frontend
    
    Example:
        POST /config/validar
        {
            "config": {
                "servidor": "localhost",
                "banco": "PLD",
                "usuario": "sa",
                "senha": "senha123"
            }
        }
    """
    config = request.config
    
    logger.info(f"Validando config para: {config.servidor}/{config.banco}")
    
    result = await validar_conexao(
        servidor=config.servidor,
        banco=config.banco,
        usuario=config.usuario,
        senha=config.senha,
        driver=config.driver
    )
    
    if result["status"] != "ok":
        raise HTTPException(status_code=400, detail=result)
    
    # Se validado, criar engine para este cliente
    config_key = f"{config.usuario}@{config.servidor}"
    
    success = db_manager.criar_engine(
        config_key=config_key,
        servidor=config.servidor,
        banco=config.banco,
        usuario=config.usuario,
        senha=config.senha,
        driver=config.driver
    )
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Erro ao criar pool de conexões"
        )
    
    return {
        "status": "ok",
        "mensagem": "✓ Configuração validada e ativada",
        "config_key": config_key,
        "detalhes": result["detalhes"]
    }

@router.post("/teste")
async def testar_conexao(request: ValidarConfigRequest):
    """
    Apenas testa a conexão sem criar engine
    Útil para UI validação antes de salvar
    """
    config = request.config
    
    result = await validar_conexao(
        servidor=config.servidor,
        banco=config.banco,
        usuario=config.usuario,
        senha=config.senha,
        driver=config.driver
    )
    
    status_code = 200 if result["status"] == "ok" else 400
    
    return JSONResponse(content=result, status_code=status_code)

@router.get("/status/{config_key}")
async def status_configuracao(config_key: str):
    """
    Obtém status de uma configuração ativa
    """
    engine = db_manager.obter_engine(config_key)
    
    if engine is None:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    
    health = await check_db_health(config_key)
    
    return {
        "config_key": config_key,
        "status": health["status"],
        "mensagem": health["message"],
        "pool": {
            "tamanho": health.get("pool_size", 0),
            "utilizadas": health.get("pool_checked_out", 0),
            "disponiveis": health.get("pool_size", 0) - health.get("pool_checked_out", 0)
        }
    }

@router.get("/listar")
async def listar_configuracoes():
    """
    Lista todas as configurações ativas
    """
    engines = db_manager.listar_engines()
    
    return {
        "total": len(engines),
        "configuracoes": engines
    }

@router.post("/fechar/{config_key}")
async def fechar_configuracao(config_key: str):
    """
    Fecha uma configuração específica
    """
    db_manager.fechar_engine(config_key)
    
    return {
        "status": "ok",
        "mensagem": f"Configuração {config_key} fechada"
    }
'''

criar_arquivo('api-gateway/routes/__init__.py', '')
criar_arquivo('api-gateway/routes/config.py', config_routes)

# ===== 3. ATUALIZAR MAIN.PY =====
print("[3/4] Atualizando api-gateway/main.py...")

main_py = '''"""
API Gateway FastAPI v2.0 - VERSÃO DINÂMICA
Configuração de banco vem do frontend via API
"""

from fastapi import FastAPI, WebSocket
from fastapi.cors import CORSMiddleware
from fastapi.websockets import WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from strawberry.fastapi import GraphQLRouter
import asyncio
import json
import logging
from datetime import datetime
from contextlib import asynccontextmanager
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database import db_manager, close_db
from routes.config import router as config_router

# ===== LOGGING =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== SCHEMA GRAPHQL =====
try:
    from schema import schema
    logger.info("✓ GraphQL schema carregado")
except ImportError:
    logger.warning("⚠️  schema.py não encontrado")
    schema = None

# ===== LIFECYCLE =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia startup/shutdown"""
    logger.info("=" * 70)
    logger.info("🚀 PLD Data Generator v2.0 - INICIADO")
    logger.info("=" * 70)
    logger.info("✓ Sistema pronto para receber configurações do frontend")
    
    yield
    
    logger.info("🛑 Encerrando...")
    close_db()

# ===== FASTAPI APP =====
app = FastAPI(
    title="PLD Data Generator API v2.0",
    version="2.0.0",
    docs_url="/docs",
    lifespan=lifespan
)

# ===== CORS =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== ROTAS =====
app.include_router(config_router)

# ===== GRAPHQL =====
if schema:
    graphql_router = GraphQLRouter(schema, path="/graphql")
    app.include_router(graphql_router)

# ===== WEBSOCKET MANAGER =====
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def broadcast(self, message: dict):
        dead = []
        for cid, conn in self.active_connections.items():
            try:
                await conn.send_json(message)
            except:
                dead.append(cid)
        for cid in dead:
            self.disconnect(cid)

manager = ConnectionManager()

# ===== WEBSOCKET =====
@app.websocket("/ws/monitoramento/{config_key}")
async def websocket_monitoramento(websocket: WebSocket, config_key: str):
    """WebSocket real-time para configuração específica"""
    client_id = f"mon_{config_key}_{datetime.now().timestamp()}"
    await manager.connect(client_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                from database import get_db_session
                from sqlalchemy import text
                
                with get_db_session(config_key) as session:
                    result = session.execute(
                        text("SELECT COUNT(*) FROM ADSVC_EXECUTAR WITH (NOLOCK)")
                    )
                    fila = result.scalar() or 0
                
                status = {
                    "timestamp": datetime.now().isoformat(),
                    "fila_pendente": fila,
                    "status_geral": "CRÍTICO" if fila > 1000 else "ESTÁVEL",
                    "config_key": config_key
                }
                
                await websocket.send_json(status)
            except Exception as e:
                logger.error(f"Erro WebSocket: {e}")
                await websocket.send_json({"erro": str(e)})
            
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        manager.disconnect(client_id)

# ===== REST ENDPOINTS =====

@app.get("/health")
async def health():
    """Health check geral"""
    engines = db_manager.listar_engines()
    
    return {
        "status": "online",
        "versao": "2.0.0",
        "engines_ativos": len(engines),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint com instruções"""
    return {
        "api": "PLD Data Generator v2.0",
        "mensagem": "Use POST /config/validar para configurar banco de dados",
        "endpoints": {
            "docs": "http://localhost:5000/docs",
            "graphql": "http://localhost:5000/graphql",
            "config_validar": "POST /config/validar",
            "config_teste": "POST /config/teste",
            "config_listar": "GET /config/listar"
        }
    }

# ===== STATIC FILES =====
try:
    static_path = os.path.join(os.path.dirname(__file__), "..", "static")
    if os.path.exists(static_path):
        app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
except:
    pass

# ===== MAIN =====
if __name__ == "__main__":
    import uvicorn
    
    print()
    print("=" * 70)
    print("🚀 PLD Data Generator - API Gateway v2.0")
    print("=" * 70)
    print()
    print("📚 Endpoints:")
    print("  • Health:     http://localhost:5000/health")
    print("  • GraphQL:    http://localhost:5000/graphql")
    print("  • Swagger:    http://localhost:5000/docs")
    print("  • Config:     POST http://localhost:5000/config/validar")
    print()
    print("=" * 70)
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )
'''

criar_arquivo('api-gateway/main.py', main_py)

# ===== 4. .ENV SIMPLIFICADO =====
print("[4/4] Atualizando .env...")

env_content = '''# ===== APLICAÇÃO =====
ENVIRONMENT=development
DEBUG=true

# ===== OPCIONAL: Conexão padrão (se usar) =====
# DATABASE_URL=mssql+pyodbc://usuario:senha@servidor/banco?driver={ODBC+Driver+17+for+SQL+Server}

# ===== NOTA =====
# Configuração de banco é enviada pelo FRONTEND via API
# POST /config/validar com credenciais SQL
'''

criar_arquivo('.env', env_content)

print()
print("=" * 70)
print("✅ SISTEMA DINÂMICO IMPLEMENTADO")
print("=" * 70)
print()
print("📝 O que muda:")
print()
print("  ANTES (Hardcoded):")
print("    .env → DATABASE_URL → Engine fixo")
print()
print("  DEPOIS (Dinâmico):")
print("    Frontend → /config/validar → Engine por cliente")
print()
print("🔄 Fluxo novo:")
print()
print("  1. Usuário configura DB no Frontend (Tela Configuração)")
print("  2. Frontend POST /config/validar")
print("  3. Backend valida e cria engine")
print("  4. Todas operações usam esse engine")
print("  5. Diferentes usuários = Diferentes engines")
print()
print("📋 Endpoints novos:")
print()
print("  POST   /config/validar    → Valida e ativa config")
print("  POST   /config/teste      → Apenas testa (sem ativar)")
print("  GET    /config/status/{key} → Status da config")
print("  GET    /config/listar     → Lista configs ativas")
print("  POST   /config/fechar/{key} → Fecha sessão")
print()
print("=" * 70)
print()
print("Próximos passos:")
print()
print("  1. pip install -r api-gateway/requirements.txt")
print("  2. uvicorn api-gateway.main:app --reload --port 5000")
print("  3. Acessar http://localhost:5000/docs")
print("  4. Fazer POST /config/validar com credenciais SQL")
print()
print("=" * 70)
