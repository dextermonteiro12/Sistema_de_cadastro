# Salve como: complete_setup.py
import os
from pathlib import Path

base = Path('.')

# ===== MAIN.PY =====
main_py = '''"""
API Gateway FastAPI v2.0
- GraphQL inteligente
- WebSocket real-time
- Connection Pool otimizado
"""

from fastapi import FastAPI, WebSocket, BackgroundTasks
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

# Imports locais
from database import engine, get_db_session, check_db_health, close_db
from config.config import config

# ===== SETUP LOGGING =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== IMPORTS SCHEMA (será criado depois) =====
try:
    from schema import schema
except ImportError:
    logger.warning("⚠️ schema.py não encontrado. GraphQL desabilitado temporariamente")
    schema = None

# ===== LIFECYCLE =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia startup/shutdown da aplicação"""
    # Startup
    logger.info("🚀 Iniciando API Gateway v2.0...")
    health = await check_db_health()
    logger.info(f"DB Status: {health['message']}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Encerrando API Gateway...")
    close_db()

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
    allow_origins=["http://localhost:3000", "http://localhost:5000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("✓ CORS habilitado")

# ===== GRAPHQL =====
if schema:
    graphql_router = GraphQLRouter(schema, path="/graphql")
    app.include_router(graphql_router)
    logger.info("✓ GraphQL endpoint em /graphql")

# ===== WEBSOCKET MANAGER =====
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"✓ Cliente {client_id} conectado")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        logger.info(f"✗ Cliente {client_id} desconectado")

    async def broadcast(self, message: dict):
        dead = []
        for client_id, conn in self.active_connections.items():
            try:
                await conn.send_json(message)
            except:
                dead.append(client_id)
        for cid in dead:
            self.disconnect(cid)

manager = ConnectionManager()

# ===== WEBSOCKET =====
@app.websocket("/ws/monitoramento")
async def websocket_monitoramento(websocket: WebSocket):
    """WebSocket real-time para dashboard"""
    client_id = f"client_{datetime.now().timestamp()}"
    await manager.connect(client_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            with get_db_session() as session:
                from sqlalchemy import text
                try:
                    result = session.execute(
                        text("SELECT COUNT(*) FROM ADSVC_EXECUTAR WITH (NOLOCK)")
                    )
                    fila = result.scalar() or 0
                except:
                    fila = 0
                
                status = {
                    "timestamp": datetime.now().isoformat(),
                    "fila_pendente": fila,
                    "status_geral": "CRÍTICO" if fila > 1000 else "ESTÁVEL",
                    "clientes_conectados": len(manager.active_connections)
                }
            
            await websocket.send_json(status)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        manager.disconnect(client_id)

# ===== REST ENDPOINTS =====
@app.get("/health")
async def health_check():
    """Health check"""
    health = await check_db_health()
    return JSONResponse(content=health, status_code=200 if health['status'] == 'healthy' else 503)

@app.get("/status")
async def api_status():
    """Status da API"""
    return {
        "api": "online",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "pool_status": "operational"
    }

# ===== SSE STREAMING =====
@app.post("/api/gerar_clientes/stream")
async def gerar_clientes_stream():
    """Server-Sent Events para progresso"""
    async def event_gen():
        for i in range(0, 101, 10):
            yield f"data: {json.dumps({
                'percentual': i,
                'mensagem': f'Processando... {i}%',
                'registros': i * 100,
                'status': 'PROCESSANDO'
            })}\\n\\n"
            await asyncio.sleep(1)
    
    return StreamingResponse(event_gen(), media_type="text/event-stream")

# ===== STATIC FILES =====
try:
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
    logger.info("✓ Static files montados")
except Exception as e:
    logger.warning(f"⚠️ Static files não encontrados: {e}")

# ===== MAIN =====
if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Iniciando Uvicorn em 0.0.0.0:5000")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        workers=1,  # Aumentar para 4 em produção
        log_level="info"
    )
'''

with open('api-gateway/main.py', 'w', encoding='utf-8') as f:
    f.write(main_py)
print("✓ main.py atualizado")

# ===== SCHEMA.PY =====
schema_py = '''"""
GraphQL Schema com Strawberry
"""

import strawberry
from typing import List, Optional
from datetime import datetime

@strawberry.type
class ClienteType:
    cd_cliente: str
    de_cliente: str
    cd_tp_cliente: str
    cic_cpf: str
    de_email: Optional[str] = None
    fl_bloqueado: int = 0

@strawberry.type
class MonitoramentoType:
    fila_pendente: int
    status_geral: str
    timestamp: datetime
    clientes_conectados: int = 0

@strawberry.type
class HealthType:
    status: str
    pool_size: int
    pool_checked_out: int
    message: str

@strawberry.type
class Query:
    @strawberry.field
    async def health_check(self) -> HealthType:
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
        from database import get_db_session
        from sqlalchemy import text
        try:
            with get_db_session() as session:
                result = session.execute(
                    text("SELECT COUNT(*) FROM ADSVC_EXECUTAR WITH (NOLOCK)")
                )
                fila = result.scalar() or 0
        except:
            fila = 0
        
        return MonitoramentoType(
            fila_pendente=fila,
            status_geral="CRÍTICO" if fila > 1000 else "ESTÁVEL",
            timestamp=datetime.now(),
            clientes_conectados=0
        )

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def iniciar_geracao_clientes(self, quantidade: int) -> str:
        import uuid
        pid = str(uuid.uuid4())[:8]
        return f"Processo {pid} iniciado"

schema = strawberry.Schema(query=Query, mutation=Mutation)
'''

with open('api-gateway/schema.py', 'w', encoding='utf-8') as f:
    f.write(schema_py)
print("✓ schema.py criado")

# ===== CONFIG.PY =====
config_py = '''"""
Configurações centralizadas
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class DatabaseConfig:
    driver: str = os.getenv('DB_DRIVER', '{ODBC Driver 17 for SQL Server}')
    server: str = os.getenv('DB_SERVER', 'localhost')
    database: str = os.getenv('DB_NAME', 'PLD')
    user: str = os.getenv('DB_USER', 'sa')
    password: str = os.getenv('DB_PASSWORD', '')
    pool_size: int = int(os.getenv('DB_POOL_SIZE', '10'))
    max_overflow: int = int(os.getenv('DB_MAX_OVERFLOW', '20'))

@dataclass
class AppConfig:
    environment: str = os.getenv('ENVIRONMENT', 'development')
    debug: bool = os.getenv('DEBUG', 'true').lower() == 'true'
    db: DatabaseConfig = DatabaseConfig()
    
    @property
    def is_production(self) -> bool:
        return self.environment == 'production'

config = AppConfig()
'''

with open('config/config.py', 'w', encoding='utf-8') as f:
    f.write(config_py)
print("✓ config/config.py criado")

# ===== DOCKER-COMPOSE.YML =====
docker_compose = '''version: '3.8'

services:
  api-gateway:
    build: .
    ports:
      - "5000:5000"
    environment:
      DB_SERVER: seu_servidor
      DB_NAME: PLD
      DB_USER: sa
      DB_PASSWORD: sua_senha
      ENVIRONMENT: development
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

networks:
  default:
    name: pld-network
'''

with open('docker-compose.yml', 'w', encoding='utf-8') as f:
    f.write(docker_compose)
print("✓ docker-compose.yml criado")

# ===== DOCKERFILE.API =====
dockerfile = '''FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl unixodbc unixodbc-dev odbcinst && rm -rf /var/lib/apt/lists/*

COPY api-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api-gateway/ .
COPY config/ config/
COPY static/ static/ 2>/dev/null || true

EXPOSE 5000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
'''

with open('Dockerfile.api', 'w', encoding='utf-8') as f:
    f.write(dockerfile)
print("✓ Dockerfile.api criado")

print("\\n✅ SETUP COMPLETADO!")