"""
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
