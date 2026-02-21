"""
GraphQL Schema com Strawberry
"""
import strawberry
from typing import Optional
from datetime import datetime
from strawberry.types import Info

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
    async def health_check(self, info: Info) -> HealthType:
        from database import check_db_health
        
        # Validar contexto (autenticação + autorização)
        context = info.context or {}
        if context.get("error"):
            return HealthType(
                status="unauthorized", 
                pool_size=0, 
                pool_checked_out=0, 
                message=context["error"]
            )
        
        config_key = context.get("config_key")
        if not config_key:
            return HealthType(
                status="unavailable", 
                pool_size=0, 
                pool_checked_out=0, 
                message="config_key missing"
            )
        
        health = await check_db_health(config_key)
        return HealthType(
            status=health.get("status", "unknown"),
            pool_size=health.get("pool_size", 0),
            pool_checked_out=health.get("pool_checked_out", 0),
            message=health.get("message", "")
        )

    @strawberry.field
    async def monitoramento_status(self, info: Info) -> MonitoramentoType:
        from database import get_db_session
        from sqlalchemy import text
        
        # Validar contexto
        context = info.context or {}
        if context.get("error"):
            return MonitoramentoType(
                fila_pendente=0, 
                status_geral="UNAUTHORIZED", 
                timestamp=datetime.now(), 
                clientes_conectados=0
            )
        
        config_key = context.get("config_key")
        if not config_key:
            return MonitoramentoType(
                fila_pendente=0, 
                status_geral="UNKNOWN", 
                timestamp=datetime.now(), 
                clientes_conectados=0
            )

        try:
            with get_db_session(config_key) as session:
                result = session.execute(text("SELECT COUNT(*) FROM ADSVC_EXECUTAR WITH (NOLOCK)"))
                fila = result.scalar() or 0
        except Exception:
            fila = 0

        status = "CRITICO" if fila > 1000 else "ESTAVEL" if fila > 100 else "SAUDAVEL"
        return MonitoramentoType(
            fila_pendente=fila, 
            status_geral=status, 
            timestamp=datetime.now(), 
            clientes_conectados=0
        )

    @strawberry.field
    async def clientes_count(self, info: Info) -> int:
        from database import get_db_session
        from sqlalchemy import text
        
        # Validar contexto
        context = info.context or {}
        if context.get("error") or not context.get("config_key"):
            return 0
        
        config_key = context["config_key"]
        try:
            with get_db_session(config_key) as session:
                result = session.execute(text("SELECT COUNT(*) FROM TAB_CLIENTES_PLD WITH (NOLOCK)"))
                return result.scalar() or 0
        except Exception:
            return 0

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def iniciar_geracao_clientes(self, quantidade: int, qtd_pf: Optional[int] = None, qtd_pj: Optional[int] = None) -> str:
        import uuid
        processo_id = str(uuid.uuid4())[:8]
        qtd_pf_final = qtd_pf or (quantidade // 2)
        qtd_pj_final = qtd_pj or (quantidade // 2)
        return f"Processo {processo_id} iniciado: PF={qtd_pf_final}, PJ={qtd_pj_final}"

schema = strawberry.Schema(query=Query, mutation=Mutation)
