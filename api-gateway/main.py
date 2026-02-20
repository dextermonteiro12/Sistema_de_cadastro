from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from strawberry.fastapi import GraphQLRouter
from datetime import datetime
from sqlalchemy import text
import logging
import asyncio
import json

from routes.config import router as config_router
from routes.auth import router as auth_router
from routes.user_config import router as user_config_router
from database import get_db_session, db_manager
from schema import schema
from grpc_client import gerar_clientes as grpc_gerar_clientes, job_status as grpc_job_status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PLD Data Generator API", version="2.0.0")

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# Rotas de autenticação (sem proteção)
app.include_router(auth_router)

# Rotas de configuração do usuário (com proteção JWT)
app.include_router(user_config_router)

# Rotas de configuração
app.include_router(config_router)

def _get_graphql_context(request: Request):
    return {"config_key": _resolve_config_key(request, {})}

app.include_router(GraphQLRouter(schema, context_getter=_get_graphql_context), prefix="/graphql")

def _resolve_config_key(request: Request, body: dict) -> str | None:
    return (
        body.get("config_key")
        or request.headers.get("X-Config-Key")
        or request.headers.get("x-config-key")
    )

def _fmt_dt(v):
    try:
        return v.strftime("%d/%m/%Y %H:%M") if v else "N/A"
    except Exception:
        return "N/A"

def _collect_dashboard(config_key: str):
    with get_db_session(config_key) as session:
        log_resumo = {"total_registros": 0, "data_antiga": "N/A", "data_recente": "N/A"}
        try:
            row = session.execute(text("""
                SELECT COUNT(1), MIN(DTHR_PESQUISA), MAX(DTHR_PESQUISA)
                FROM TB_LISTA_PESQUISAS_LOG WITH (NOLOCK)
            """)).fetchone()
            if row and row[0]:
                log_resumo = {
                    "tabela": "TB_LISTA_PESQUISAS_LOG",
                    "total_registros": int(row[0]),
                    "data_antiga": _fmt_dt(row[1]),
                    "data_recente": _fmt_dt(row[2]),
                }
        except Exception:
            log_resumo["status"] = "Tabela de Log não encontrada"

        qtd_pendente = int(session.execute(text("SELECT COUNT(1) FROM ADSVC_EXECUTAR WITH (NOLOCK)")).scalar() or 0)
        try:
            qtd_processados = int(session.execute(text("SELECT COUNT(1) FROM ADSVC_EXECUTADOS_EXCLUIR WITH (NOLOCK)")).scalar() or 0)
        except Exception:
            qtd_processados = 0

        regras_rows = session.execute(text("""
            SELECT TOP 10 LEFT(DS_COMANDO1, 20) as Regra, COUNT(1) as Total
            FROM ADSVC_EXECUTAR WITH (NOLOCK)
            GROUP BY LEFT(DS_COMANDO1, 20)
            ORDER BY Total DESC
        """)).fetchall()
        regras = [{"regra": (r[0] or "").strip(), "qtd": int(r[1] or 0)} for r in regras_rows]

        tabelas_exec = [
            "ADSVC_EXECUTANDO", "ADSVC_EXECUTANDO_MF1", "ADSVC_EXECUTANDO_MF2",
            "ADSVC_EXECUTANDO_MF3", "ADSVC_EXECUTANDO_MF4", "ADSVC_EXECUTANDO_MF5",
            "ADSVC_EXECUTANDO_LV1", "ADSVC_EXECUTANDO_LV2", "ADSVC_EXECUTANDO_LV3",
            "ADSVC_EXECUTANDO_LV4", "ADSVC_EXECUTANDO_LV5"
        ]
        performance = []
        for t in tabelas_exec:
            try:
                row = session.execute(text(f"""
                    SELECT TOP 1 LEFT(DS_COMANDO1, 20), QT_TEMPO_EXEC
                    FROM {t} WITH (NOLOCK)
                    ORDER BY QT_TEMPO_EXEC DESC
                """)).fetchone()
                if row:
                    performance.append({
                        "worker": t.replace("ADSVC_EXECUTANDO_", "").replace("ADSVC_EXECUTANDO", "PRINCIPAL"),
                        "regra": (row[0] or "").strip(),
                        "tempo": float(row[1] or 0),
                    })
            except Exception:
                continue

        return {
            "status": "ok",
            "log_pesquisas": log_resumo,
            "fila_geral": {"pendente": qtd_pendente, "processados": qtd_processados},
            "regras": regras,
            "performance": performance
        }

@app.get("/")
async def root():
    return {"message": "PLD Data Generator API v2.0"}

@app.get("/health")
async def health():
    return {"status": "online", "version": "2.0.0", "timestamp": datetime.now().isoformat()}

@app.post("/login")
async def login(body: dict):
    username = body.get("username")
    password = body.get("password")
    if username == "admin" and password == "1234":
        return {"status": "ok", "user": "admin", "tipo": "ADMIN"}
    return JSONResponse(content={"message":"Erro"}, status_code=401)

@app.post("/api/saude-servidor")
async def saude_servidor(request: Request, body: dict):
    config_key = _resolve_config_key(request, body or {})
    if not config_key:
        return JSONResponse({"erro": "config_key não informado"}, status_code=400)
    try:
        dash = _collect_dashboard(config_key)
        fila_pendente = dash["fila_geral"]["pendente"]
        erros_hoje = 0
        try:
            with get_db_session(config_key) as session:
                erros_hoje = int(session.execute(text("""
                    SELECT COUNT(1) FROM TB_SERVICO_EXEC
                    WHERE DS_ERRO <> '' AND DT_HR_EXECUTADO >= DATEADD(hh, -24, GETDATE())
                """)).scalar() or 0)
        except Exception:
            erros_hoje = 0

        perf = [
            {"Fila": "Fila Principal", "Media": float(fila_pendente)},
            {"Fila": "Fila Secundária", "Media": float(max(fila_pendente // 2, 0))}
        ]

        status_geral = "ESTÁVEL"
        if fila_pendente > 1000 or erros_hoje > 50:
            status_geral = "CRÍTICO"

        return {
            "status_geral": status_geral,
            "cards": {
                "fila_pendente": fila_pendente,
                "erros_servicos": erros_hoje
            },
            "performance_ms": perf
        }
    except Exception as e:
        return JSONResponse({
            "status_geral": "OFFLINE",
            "cards": {"fila_pendente": 0, "erros_servicos": 0},
            "performance_ms": [],
            "erro": str(e)
        }, status_code=500)

@app.post("/api/clientes-pendentes")
async def clientes_pendentes(request: Request, body: dict):
    """Retorna quantidade de clientes sem integrar"""
    config_key = _resolve_config_key(request, body or {})
    if not config_key:
        return JSONResponse({"erro": "config_key não informado"}, status_code=400)
    
    try:
        with get_db_session(config_key) as session:
            result = session.execute(text("""
                IF EXISTS (SELECT TOP 1 'X' FROM SYSOBJECTS WHERE NAME = 'VIEW_CLIENTES_AUX')  
                BEGIN
                    SELECT COUNT(1) as quantidade
                    FROM VIEW_CLIENTES_AUX A WITH(NOLOCK)     
                    LEFT JOIN VIEW_CLIENTES B WITH(NOLOCK) ON A.CD_CLIENTE = B.CD_CLIENTE    
                    WHERE B.CD_CLIENTE IS NULL   
                END
                ELSE
                BEGIN
                    SELECT 0 as quantidade
                END
            """)).fetchone()
            
            quantidade = result[0] if result else 0
            timestamp = datetime.now().isoformat()
            
            return {
                "status": "ok",
                "quantidade": int(quantidade),
                "descricao": "Clientes sem integrar (VIEW_CLIENTES_AUX → VIEW_CLIENTES)",
                "timestamp": timestamp
            }
    except Exception as e:
        logger.error(f"Erro ao consultar clientes pendentes: {str(e)}")
        return JSONResponse({
            "status": "erro",
            "quantidade": 0,
            "erro": str(e),
            "descricao": "Erro ao consultar clientes pendentes"
        }, status_code=500)

@app.post("/status_dashboard")
async def status_dashboard(request: Request, body: dict):
    config_key = _resolve_config_key(request, body or {})
    if not config_key:
        return JSONResponse({"status":"erro","message":"config_key não informado"}, status_code=400)
    try:
        return _collect_dashboard(config_key)
    except Exception as e:
        return JSONResponse({"status":"erro","erro": str(e)}, status_code=500)

@app.post("/api/dashboard/log-pesquisas")
async def log_pesquisas(request: Request, body: dict):
    config_key = _resolve_config_key(request, body or {})
    if not config_key:
        return JSONResponse({"status":"erro","message":"config_key não informado"}, status_code=400)
    try:
        dash = _collect_dashboard(config_key)
        lp = dash["log_pesquisas"]
        return {"status":"ok","dados":{"total": lp.get("total_registros", 0), "data_inicio": lp.get("data_antiga","N/A"), "data_fim": lp.get("data_recente","N/A")}}
    except Exception as e:
        return JSONResponse({"status":"erro","erro":str(e)}, status_code=500)

@app.post("/api/dashboard/fila-adsvc")
async def fila_adsvc(request: Request, body: dict):
    config_key = _resolve_config_key(request, body or {})
    if not config_key:
        return JSONResponse({"status":"erro","message":"config_key não informado"}, status_code=400)
    try:
        dash = _collect_dashboard(config_key)
        fg = dash["fila_geral"]
        return {"status":"ok","dados":{"pendentes": fg.get("pendente", 0), "processados": fg.get("processados", 0)}}
    except Exception as e:
        return JSONResponse({"status":"erro","erro":str(e)}, status_code=500)

@app.post("/api/dashboard/performance-workers")
async def perf_workers(request: Request, body: dict):
    config_key = _resolve_config_key(request, body or {})
    if not config_key:
        return JSONResponse({"status":"erro","message":"config_key não informado"}, status_code=400)
    try:
        dash = _collect_dashboard(config_key)
        dados = [{
            "data_exec": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "worker": p.get("worker","-"),
            "exec": p.get("regra","-"),
            "qtd_tempo": p.get("tempo", 0)
        } for p in dash["performance"]]
        return {"status":"ok","dados": dados}
    except Exception as e:
        return JSONResponse({"status":"erro","erro":str(e)}, status_code=500)

@app.post("/gerar_clientes")
async def gerar_clientes(body: dict):
    config_key = body.get("config_key")
    quantidade = body.get("quantidade", 100)
    return {"status": "ok", "mensagem": f"Gerando {quantidade} clientes...", "config_key": config_key}

@app.post("/monitoramento")
async def monitoramento(body: dict):
    return {"status": "ok", "mensagem": "Sistema operacional", "workers_ativos": 4, "registros_processados": 15000}

@app.post("/movimentacoes")
async def movimentacoes(body: dict):
    return {"status": "ok", "mensagem": "Movimentações processadas", "total": 250}

@app.post("/check_ambiente")
async def check_ambiente(request: Request, body: dict):
    config_key = _resolve_config_key(request, body or {})
    if not config_key:
        return JSONResponse({"status":"erro","message":"config_key nao informado"}, status_code=400)
    try:
        with get_db_session(config_key) as session:
            try:
                row = session.execute(text("SELECT TOP 1 CD_VERSAO FROM AD_SISTEMAS_VERSOES WITH (NOLOCK) ORDER BY 1 DESC")).fetchone()
                versao = "V9" if row and "009" in str(row[0]) else "V8"
            except Exception:
                versao = "V8"

            tabelas = [
                "TAB_CLIENTES_PLD",
                "TAB_CLIENTES_MOVFIN_PLD",
                "TAB_CLIENTES_MOVFIN_ME_PLD",
                "TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD",
                "TAB_CLIENTES_CO_TIT_PLD"
            ]
            status_tabs = {}
            for t in tabelas:
                qtd = session.execute(text(f"SELECT COUNT(*) FROM sys.tables WITH (NOLOCK) WHERE name = '{t}'")).scalar() or 0
                status_tabs[t] = "Criada" if int(qtd) == 1 else "Ausente"
        return {"status":"ok","versao":versao,"tabelas":status_tabs}
    except Exception as e:
        return JSONResponse({"status":"erro","erro":str(e)}, status_code=500)

@app.post("/setup_ambiente")
async def setup_ambiente(request: Request, body: dict):
    config_key = _resolve_config_key(request, body or {})
    if not config_key:
        return JSONResponse({"status":"erro","message":"config_key nao informado"}, status_code=400)
    try:
        with get_db_session(config_key) as session:
            session.execute(text("IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_PLD' AND xtype='U') CREATE TABLE TAB_CLIENTES_PLD (CD_CLIENTE char(20) PRIMARY KEY, DE_CLIENTE varchar(120))"))
            session.execute(text("IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_MOVFIN_PLD' AND xtype='U') CREATE TABLE TAB_CLIENTES_MOVFIN_PLD (CD_IDENTIFICACAO varchar(40) PRIMARY KEY, CD_CLIENTE varchar(20))"))
            session.execute(text("IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_MOVFIN_ME_PLD' AND xtype='U') CREATE TABLE TAB_CLIENTES_MOVFIN_ME_PLD (CD_IDENTIFICACAO varchar(40) PRIMARY KEY, CD_CLIENTE varchar(20))"))
            session.execute(text("IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD' AND xtype='U') CREATE TABLE TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD (CD_IDENTIFICACAO char(40) PRIMARY KEY, CD_CLIENTE varchar(20))"))
            session.execute(text("IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_CO_TIT_PLD' AND xtype='U') CREATE TABLE TAB_CLIENTES_CO_TIT_PLD (CD_CLIENTE char(20) NOT NULL, DE_NOME_CO varchar(120) NOT NULL)"))
        return {"status":"ok","message":"Estrutura criada/verificada com sucesso"}
    except Exception as e:
        return JSONResponse({"status":"erro","erro":str(e)}, status_code=500)

@app.post("/grpc/gerar_clientes")
async def grpc_gerar_clientes_endpoint(body: dict):
    config_key = body.get("config_key")
    if not config_key:
        return JSONResponse({"status":"erro","message":"config_key nao informado"}, status_code=400)

    config = db_manager.get_config(config_key)
    if not config:
        return JSONResponse({"status":"erro","message":"config nao encontrada"}, status_code=400)

    quantidade = int(body.get("quantidade", 0))
    qtd_pf = int(body.get("qtd_pf", 0) or 0)
    qtd_pj = int(body.get("qtd_pj", 0) or 0)

    try:
        resp = grpc_gerar_clientes(config, config_key, quantidade, qtd_pf, qtd_pj)
        return {
            "status": resp.status,
            "job_id": resp.job_id,
            "message": resp.message,
            "inserted": getattr(resp, "inserted", 0)
        }
    except Exception as e:
        return JSONResponse({"status":"erro","erro": str(e)}, status_code=500)

@app.get("/grpc/job_status/{job_id}")
async def grpc_job_status_endpoint(job_id: str):
    try:
        resp = grpc_job_status(job_id)
        return {
            "status": resp.status,
            "percent": resp.percent,
            "inserted": resp.inserted,
            "message": resp.message
        }
    except Exception as e:
        return JSONResponse({"status":"erro","erro": str(e)}, status_code=500)

@app.get("/grpc/job_status/stream/{job_id}")
async def grpc_job_status_stream(job_id: str):
    async def event_gen():
        while True:
            try:
                resp = grpc_job_status(job_id)
                payload = {
                    "status": resp.status,
                    "percent": resp.percent,
                    "inserted": resp.inserted,
                    "message": resp.message
                }
            except Exception as e:
                payload = {"status": "erro", "percent": 0, "inserted": 0, "message": str(e)}

            yield f"data: {json.dumps(payload)}\n\n"

            if payload["status"] in ("done", "error", "not_found", "erro"):
                break
            await asyncio.sleep(1)

    return StreamingResponse(event_gen(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting API Gateway")
    uvicorn.run(app, host="0.0.0.0", port=5000, reload=False)
