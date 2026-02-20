"""
Rotas para gerenciar configurações de banco de dados por usuário.
Integra com auth_database.py para persistência de credenciais.
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List
import logging
from auth_database import AuthDB
from routes.auth import verify_jwt_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user-config", tags=["user-configuration"])


# ===== MODELOS PYDANTIC =====

class SaveConfigRequest(BaseModel):
    """Request para salvar configuração do usuário"""
    xml_path: str
    sql_server: str
    sql_username: str
    sql_password: str
    bases: List[dict]  # Lista de bases do XML


class UserConfigResponse(BaseModel):
    """Response com configuração do usuário"""
    config_id: str
    xml_path: str
    sql_server: str
    sql_username: str
    bases: List[dict]
    created_at: str
    updated_at: str


# ===== FUNÇÕES AUXILIARES =====

def get_user_from_header(authorization: str = Header(None)) -> Optional[str]:
    """
    Extrai user_id do token JWT do header
    Returns: user_id se válido, None caso contrário
    """
    if not authorization:
        return None
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    token = parts[1]
    payload = verify_jwt_token(token)
    
    if not payload:
        return None
    
    return payload.get("user_id")


# ===== ENDPOINTS =====

@router.post("/save")
async def save_user_config(
    request: SaveConfigRequest,
    authorization: str = Header(None)
):
    """
    Salva configuração de banco de dados do usuário com credenciais criptografadas.
    Requer autenticação JWT.
    
    Example:
        POST /user-config/save
        Authorization: Bearer <token>
        {
            "xml_path": "C:\\Advice",
            "sql_server": "advSUSTENTSP03",
            "sql_username": "sa",
            "sql_password": "senha123",
            "bases": [
                {
                    "id": "CORP:CORP:CORP",
                    "sistema": "CORP",
                    "empresa": "CORP",
                    "servidor": "advSUSTENTSP03",
                    "banco": "CORP",
                    "usuario": "sa",
                    "label": "CORP | CORP | CORP"
                },
                ...
            ]
        }
    """
    user_id = get_user_from_header(authorization)
    
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Token inválido ou ausente"
        )
    
    if not request.bases or len(request.bases) == 0:
        raise HTTPException(
            status_code=400,
            detail="Pelo menos uma base é obrigatória"
        )
    
    try:
        result = AuthDB.save_user_config(
            user_id=user_id,
            xml_path=request.xml_path,
            sql_server=request.sql_server,
            sql_username=request.sql_username,
            sql_password=request.sql_password,
            bases=request.bases
        )
        
        logger.info(f"Configuração salva para usuário {user_id}: {len(request.bases)} base(s)")
        
        return {
            "status": "ok",
            "message": f"Configuração salva com sucesso: {len(request.bases)} base(s)",
            "config_id": result["config_id"],
            "total_bases": len(request.bases)
        }
    except Exception as e:
        logger.error(f"Erro ao salvar configuração: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao salvar configuração: {str(e)}"
        )


@router.get("/get", response_model=UserConfigResponse)
async def get_user_config(authorization: str = Header(None)):
    """
    Obtém configuração atual do usuário (credenciais descriptografadas).
    Requer autenticação JWT.
    """
    user_id = get_user_from_header(authorization)
    
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Token inválido ou ausente"
        )
    
    config = AuthDB.get_user_config(user_id)
    
    if not config:
        raise HTTPException(
            status_code=404,
            detail="Nenhuma configuração encontrada para este usuário"
        )
    
    return UserConfigResponse(
        config_id=config["config_id"],
        xml_path=config["xml_path"],
        sql_server=config["sql_server"],
        sql_username=config["sql_username"],
        bases=config["bases"],
        created_at=config["created_at"],
        updated_at=config["updated_at"]
    )


@router.get("/bases")
async def get_user_bases(authorization: str = Header(None)):
    """
    Lista as bases disponíveis para o usuário autenticado.
    Retorna apenas a lista de bases sem credenciais.
    """
    user_id = get_user_from_header(authorization)
    
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Token inválido ou ausente"
        )
    
    config = AuthDB.get_user_config(user_id)
    
    if not config:
        return {
            "status": "ok",
            "total": 0,
            "bases": []
        }
    
    bases = config["bases"]
    
    return {
        "status": "ok",
        "total": len(bases),
        "bases": bases
    }


@router.get("/info")
async def get_config_info(authorization: str = Header(None)):
    """
    Retorna informações da configuração do usuário (sem senhas).
    """
    user_id = get_user_from_header(authorization)
    
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Token inválido ou ausente"
        )
    
    config = AuthDB.get_user_config(user_id)
    
    if not config:
        return {
            "status": "not_configured",
            "has_config": False,
            "total_bases": 0,
            "xml_path": None,
            "sql_server": None,
            "sql_username": None
        }
    
    return {
        "status": "configured",
        "has_config": True,
        "total_bases": len(config["bases"]),
        "xml_path": config["xml_path"],
        "sql_server": config["sql_server"],
        "sql_username": config["sql_username"],
        "created_at": config["created_at"],
        "updated_at": config["updated_at"]
    }
