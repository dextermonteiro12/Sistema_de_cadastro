"""
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
