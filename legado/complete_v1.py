#!/usr/bin/env python3
"""
Script para completar os arquivos faltantes do Passo 1
Execute: python complete_v1.py
"""

import os
from pathlib import Path

def criar_arquivo(caminho, conteudo):
    """Cria arquivo com conteúdo"""
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print(f"✓ {caminho}")

print("=" * 60)
print("COMPLETANDO ARQUIVOS - PASSO 1")
print("=" * 60 + "\n")

# ===== 1. MAIN.PY =====
print("[1/5] Criando api-gateway/main.py...")

main_py = '''"""
API Gateway FastAPI v2.0
- GraphQL inteligente
- WebSocket real-time
- Connection Pool otimizado
"""

from fastapi import FastAPI, WebSocket
from fastapi.cors import CORSMiddleware
from fastapi.websockets import WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, JSONResponse
from strawberry.fastapi import GraphQLRouter
import strawberry
import asyncio
import json
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator
import sys
import os

# Adicionar pasta ao path para imports
sys.path.insert(0, os.path.dirname(__file__))

# Imports locais
from database import engine, get_db_session, check_db_health, close_db

# ===== SETUP LOGGING =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== IMPORTS SCHEMA =====
try:
    from schema import schema
    logger.info("✓ GraphQL schema importado")
except ImportError as e:
    logger.warning(f"⚠️  schema.py não encontrado: {e}")
    schema = None

# ===== LIFECYCLE =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia startup/shutdown da aplicação"""
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 Iniciando API Gateway v2.0...")
    logger.info("=" * 60)
    
    try:
        health = await check_db_health()
        if health['status'] == 'healthy':
            logger.info(f"✓ Database: {health['message']}")
        else:
            logger.warning(f"⚠️  Database: {health.get('error', 'Unknown error')}")
    except Exception as e:
        logger.error(f"❌ Erro ao verificar database: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Encerrando API Gateway...")
    close_db()
    logger.info("✓ Conexões fechadas")

# ===== FASTAPI APP =====
app = FastAPI(
    title="PLD Data Generator API v2.0",
    version="2.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# ===== CORS =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("✓ CORS habilitado para desenvolvimento")

# ===== GRAPHQL =====
if schema:
    graphql_router = GraphQLRouter(schema, path="/graphql")
    app.include_router(graphql_router)
    logger.info("✓ GraphQL endpoint em http://localhost:5000/graphql")

# ===== WEBSOCKET MANAGER =====
class ConnectionManager:
    """Gerencia conexões WebSocket"""
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        """Aceita nova conexão"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"✓ WebSocket conectado: {client_id} (Total: {len(self.active_connections)})")

    def disconnect(self, client_id: str):
        """Remove conexão"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        logger.info(f"✗ WebSocket desconectado: {client_id} (Total: {len(self.active_connections)})")

    async def broadcast(self, message: dict):
        """Envia mensagem para todos"""
        dead = []
        for client_id, conn in self.active_connections.items():
            try:
                await conn.send_json(message)
            except Exception as e:
                logger.warning(f"Erro enviando para {client_id}: {e}")
                dead.append(client_id)
        
        for cid in dead:
            self.disconnect(cid)

manager = ConnectionManager()

# ===== WEBSOCKET ENDPOINT =====
@app.websocket("/ws/monitoramento")
async def websocket_monitoramento(websocket: WebSocket):
    """WebSocket real-time para dashboard"""
    client_id = f"monitor_{datetime.now().timestamp()}"
    await manager.connect(client_id, websocket)
    
    try:
        while True:
            # Aguarda dados do cliente (keepalive)
            data = await websocket.receive_text()
            
            # Coleta status do banco
            with get_db_session() as session:
                from sqlalchemy import text
                try:
                    result = session.execute(
                        text("SELECT COUNT(*) FROM ADSVC_EXECUTAR WITH (NOLOCK)")
                    )
                    fila = result.scalar() or 0
                except Exception as e:
                    logger.error(f"Erro ao consultar fila: {e}")
                    fila = 0
                
                status = {
                    "timestamp": datetime.now().isoformat(),
                    "fila_pendente": fila,
                    "status_geral": "CRÍTICO" if fila > 1000 else "ESTÁVEL",
                    "clientes_conectados": len(manager.active_connections)
                }
            
            await websocket.send_json(status)
            await asyncio.sleep(2)  # Atualiza a cada 2s
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"WebSocket desconectado normalmente: {client_id}")
    except Exception as e:
        logger.error(f"Erro WebSocket: {e}")
        manager.disconnect(client_id)

# ===== REST ENDPOINTS =====

@app.get("/health")
async def health_check():
    """Health check da API e banco de dados"""
    health = await check_db_health()
    status_code = 200 if health['status'] == 'healthy' else 503
    
    return JSONResponse(
        content={
            "status": health['status'],
            "message": health.get('message', 'Unknown'),
            "pool_size": health.get('pool_size', 'N/A'),
            "pool_checked_out": health.get('pool_checked_out', 'N/A')
        },
        status_code=status_code
    )

@app.get("/status")
async def api_status():
    """Status geral da API"""
    return {
        "api": "online",
        "version": "2.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.now().isoformat(),
        "graphql": "enabled" if schema else "disabled",
        "websocket": "enabled"
    }

# ===== SSE STREAMING =====
@app.post("/api/gerar_clientes/stream")
async def gerar_clientes_stream(request: dict = {}):
    """Server-Sent Events para monitorar progresso"""
    quantidade = request.get('quantidade', 1000) if isinstance(request, dict) else 1000
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Simula progresso de geração"""
        for i in range(0, 101, 10):
            status = {
                "percentual": i,
                "mensagem": f"Processando... {i}%",
                "registros_inseridos": i * (quantidade // 100),
                "status": "PROCESSANDO" if i < 100 else "FINALIZADO",
                "timestamp": datetime.now().isoformat()
            }
            
            yield f"data: {json.dumps(status)}\\n\\n"
            await asyncio.sleep(1)
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ===== STATIC FILES (SPA) =====
try:
    static_path = os.path.join(os.path.dirname(__file__), "..", "static")
    if os.path.exists(static_path):
        app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
        logger.info(f"✓ Static files montados de: {static_path}")
    else:
        logger.warning(f"⚠️  Pasta static não encontrada em: {static_path}")
except Exception as e:
    logger.warning(f"⚠️  Não foi possível montar static files: {e}")

# ===== MAIN =====
if __name__ == "__main__":
    import uvicorn
    
    print()
    print("=" * 60)
    print("🚀 PLD Data Generator API v2.0")
    print("=" * 60)
    print()
    print("📚 Documentação disponível:")
    print("  • Swagger: http://localhost:5000/docs")
    print("  • GraphQL: http://localhost:5000/graphql")
    print("  • Health:  http://localhost:5000/health")
    print("  • Status:  http://localhost:5000/status")
    print()
    print("🌐 WebSocket:")
    print("  • ws://localhost:5000/ws/monitoramento")
    print()
    print("=" * 60)
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        workers=1,  # Mudar para 4 em produção
        log_level="info",
        reload=True
    )
'''

criar_arquivo('api-gateway/main.py', main_py)

# ===== 2. SCHEMA.PY =====
print("[2/5] Criando api-gateway/schema.py...")

schema_py = '''"""
GraphQL Schema com Strawberry
Define tipos GraphQL, queries e mutations
"""

import strawberry
from typing import List, Optional
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

# ===== TIPOS GRAPHQL =====

@strawberry.type
class ClienteType:
    """Tipo GraphQL para Cliente"""
    cd_cliente: str
    de_cliente: str
    cd_tp_cliente: str
    cic_cpf: str
    de_email: Optional[str] = None
    fl_bloqueado: int = 0

@strawberry.type
class MovimentacaoType:
    """Tipo GraphQL para Movimentação"""
    cd_identificacao: str
    cd_cliente: str
    vl_operacao: float
    tp_deb_cred: str
    dt_movimenta: datetime
    de_forma: str

@strawberry.type
class MonitoramentoType:
    """Tipo GraphQL para Monitoramento"""
    fila_pendente: int
    status_geral: str
    timestamp: datetime
    clientes_conectados: int = 0

@strawberry.type
class HealthType:
    """Tipo GraphQL para Health Check"""
    status: str
    pool_size: int
    pool_checked_out: int
    message: str

@strawberry.type
class ProcessoType:
    """Tipo GraphQL para Processo de Geração"""
    id_processo: str
    percentual: int
    mensagem: str
    registros_inseridos: int
    status: str
    timestamp: str

# ===== QUERIES =====

@strawberry.type
class Query:
    """Queries GraphQL disponíveis"""
    
    @strawberry.field
    async def health_check(self) -> HealthType:
        """Health check do sistema e pool de conexões"""
        from database import check_db_health
        
        health = await check_db_health()
        return HealthType(
            status=health['status'],
            pool_size=health.get('pool_size', 0),
            pool_checked_out=health.get('pool_checked_out', 0),
            message=health['message']
        )
    
    @strawberry.field
    async def monitoramento_status(self) -> MonitoramentoType:
        """Status de monitoramento em tempo real"""
        from database import get_db_session
        from sqlalchemy import text
        
        try:
            with get_db_session() as session:
                result = session.execute(
                    text("SELECT COUNT(*) FROM ADSVC_EXECUTAR WITH (NOLOCK)")
                )
                fila = result.scalar() or 0
        except Exception as e:
            print(f"Erro ao consultar fila: {e}")
            fila = 0
        
        return MonitoramentoType(
            fila_pendente=fila,
            status_geral="CRÍTICO" if fila > 1000 else "ESTÁVEL" if fila > 100 else "SAUDÁVEL",
            timestamp=datetime.now(),
            clientes_conectados=0
        )
    
    @strawberry.field
    async def clientes_count(self) -> int:
        """Conta total de clientes"""
        from database import get_db_session
        from sqlalchemy import text
        
        try:
            with get_db_session() as session:
                result = session.execute(
                    text("SELECT COUNT(*) FROM TAB_CLIENTES_PLD WITH (NOLOCK)")
                )
                return result.scalar() or 0
        except Exception as e:
            print(f"Erro ao contar clientes: {e}")
            return 0

# ===== MUTATIONS =====

@strawberry.type
class Mutation:
    """Mutations GraphQL disponíveis"""
    
    @strawberry.mutation
    async def iniciar_geracao_clientes(
        self,
        quantidade: int,
        qtd_pf: Optional[int] = None,
        qtd_pj: Optional[int] = None
    ) -> str:
        """Inicia processo de geração de clientes"""
        import uuid
        
        processo_id = str(uuid.uuid4())[:8]
        qtd_pf_final = qtd_pf or (quantidade // 2)
        qtd_pj_final = qtd_pj or (quantidade // 2)
        
        print(f"🚀 Processo {processo_id}: Gerando {quantidade} clientes")
        print(f"   PF: {qtd_pf_final}, PJ: {qtd_pj_final}")
        
        return f"Processo {processo_id} iniciado com sucesso"

# ===== SCHEMA =====
schema = strawberry.Schema(query=Query, mutation=Mutation)
'''

criar_arquivo('api-gateway/schema.py', schema_py)

# ===== 3. CONFIG.PY =====
print("[3/5] Criando config/config.py...")

config_py = '''"""
Configurações centralizadas da aplicação
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class DatabaseConfig:
    """Configurações de banco de dados"""
    driver: str = os.getenv('DB_DRIVER', '{ODBC Driver 17 for SQL Server}')
    server: str = os.getenv('DB_SERVER', 'localhost')
    database: str = os.getenv('DB_NAME', 'PLD')
    user: str = os.getenv('DB_USER', 'sa')
    password: str = os.getenv('DB_PASSWORD', '')
    pool_size: int = int(os.getenv('DB_POOL_SIZE', '10'))
    max_overflow: int = int(os.getenv('DB_MAX_OVERFLOW', '20'))
    
    @property
    def connection_url(self) -> str:
        """Gera URL de conexão do pool"""
        return (
            f"mssql+pyodbc://{self.user}:{self.password}@"
            f"{self.server}/{self.database}"
            f"?driver={self.driver}&TrustServerCertificate=yes"
        )

@dataclass
class GRPCConfig:
    """Configurações de gRPC (futuro)"""
    host: str = os.getenv('GRPC_HOST', 'localhost')
    port: int = int(os.getenv('GRPC_PORT', '50051'))
    max_workers: int = int(os.getenv('GRPC_WORKERS', '10'))

@dataclass
class AppConfig:
    """Configurações gerais da aplicação"""
    environment: str = os.getenv('ENVIRONMENT', 'development')
    debug: bool = os.getenv('DEBUG', 'true').lower() == 'true'
    api_title: str = "PLD Data Generator API v2.0"
    api_version: str = "2.0.0"
    
    # CORS
    cors_origins: list = [
        "http://localhost:3000",
        "http://localhost:5000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5000"
    ]
    
    # Database
    db: DatabaseConfig = DatabaseConfig()
    
    # gRPC
    grpc: GRPCConfig = GRPCConfig()
    
    @property
    def is_production(self) -> bool:
        """Verifica se está em produção"""
        return self.environment == 'production'

# Singleton global
config = AppConfig()
'''

criar_arquivo('config/config.py', config_py)

# ===== 4. DOCKER-COMPOSE.YML =====
print("[4/5] Criando docker-compose.yml...")

docker_compose = '''version: '3.8'

services:
  # API Gateway FastAPI
  api-gateway:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "5000:5000"
    environment:
      - DB_SERVER=seu_servidor
      - DB_NAME=PLD
      - DB_USER=sa
      - DB_PASSWORD=sua_senha
      - DB_DRIVER={ODBC Driver 17 for SQL Server}
      - ENVIRONMENT=development
      - DEBUG=true
    depends_on:
      - redis
    networks:
      - pld-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Redis para caching (futuro)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - pld-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

networks:
  pld-network:
    driver: bridge
'''

criar_arquivo('docker-compose.yml', docker_compose)

# ===== 5. DOCKERFILE.API =====
print("[5/5] Criando Dockerfile.api...")

dockerfile = '''FROM python:3.11-slim

WORKDIR /app

# Instalar dependências de sistema
RUN apt-get update && apt-get install -y \\
    curl \\
    unixodbc \\
    unixodbc-dev \\
    odbcinst \\
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY api-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY api-gateway/ .
COPY config/ config/
COPY static/ static/ 2>/dev/null || true

# Expor porta
EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \\
    CMD curl -f http://localhost:5000/health || exit 1

# Comando para iniciar
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
'''

criar_arquivo('Dockerfile.api', dockerfile)

# ===== .ENV EXAMPLE =====
print("[6/5] Criando/atualizando .env.example...")

env_example = '''# ===== DATABASE =====
DB_DRIVER={ODBC Driver 17 for SQL Server}
DB_SERVER=seu_servidor_sql
DB_NAME=PLD
DB_USER=sa
DB_PASSWORD=sua_senha
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# ===== GRPC =====
GRPC_HOST=localhost
GRPC_PORT=50051
GRPC_WORKERS=10

# ===== APP =====
ENVIRONMENT=development
DEBUG=true
'''

criar_arquivo('.env.example', env_example)

# ===== CRIAR __INIT__.PY FILES =====
print("[7/5] Criando __init__.py para imports...")

criar_arquivo('api-gateway/__init__.py', '')
criar_arquivo('config/__init__.py', '')

print()
print("=" * 60)
print("✅ PASSO 1 COMPLETADO COM SUCESSO!")
print("=" * 60)
print()
print("📁 Arquivos criados:")
print("  ✓ api-gateway/main.py (FastAPI)")
print("  ✓ api-gateway/schema.py (GraphQL)")
print("  ✓ config/config.py (Configurações)")
print("  ✓ docker-compose.yml")
print("  ✓ Dockerfile.api")
print("  ✓ .env.example")
print()
print("📋 Próximos passos:")
print()
print("  1️⃣  Configurar .env:")
print("     → cp .env.example .env")
print("     → Editar .env com credenciais SQL Server")
print()
print("  2️⃣  Instalar dependências:")
print("     → pip install -r api-gateway/requirements.txt")
print()
print("  3️⃣  Iniciar API Gateway:")
print("     → cd api-gateway")
print("     → uvicorn main:app --reload --host 0.0.0.0 --port 5000")
print()
print("  4️⃣  Testar endpoints:")
print("     → Health: http://localhost:5000/health")
print("     → GraphQL: http://localhost:5000/graphql")
print("     → Docs: http://localhost:5000/docs")
print()
print("=" * 60)
