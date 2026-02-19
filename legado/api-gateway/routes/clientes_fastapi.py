from fastapi import APIRouter, Depends
from pydantic import BaseModel
from database import get_db_session

router = APIRouter(prefix='/gerar_clientes', tags=['clientes'])

class GerarClientesRequest(BaseModel):
    config_key: str
    quantidade: int = 100
    qtd_pf: int = None
    qtd_pj: int = None

@router.post('')
async def gerar_clientes(request: GerarClientesRequest):
    """Gera clientes PF e PJ"""
    try:
        with get_db_session(request.config_key) as session:
            # Placeholder - implementar lógica de geração
            return {
                'status': 'ok',
                'mensagem': f'Iniciando geração de {request.quantidade} clientes',
                'config_key': request.config_key
            }
    except Exception as e:
        return {
            'status': 'erro',
            'mensagem': str(e)
        }
