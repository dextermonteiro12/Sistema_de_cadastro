from fastapi import FastAPI, Request, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from strawberry.fastapi import GraphQLRouter
from datetime import datetime
from sqlalchemy import text
import logging
import asyncio
import json
import os
import random
import re
import threading
import string
import uuid
from datetime import timedelta
from typing import Optional
from faker import Faker

from routes.config import router as config_router
from routes.auth import router as auth_router, verify_jwt_token
from routes.user_config import router as user_config_router
from database import get_db_session, db_manager
from schema import schema
from grpc_client import gerar_clientes as grpc_gerar_clientes, job_status as grpc_job_status
from auth_database import AuthDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENAPI_TAGS = [
    {
        "name": "Sistema",
        "description": "Status e informações gerais da API."
    },
    {
        "name": "Autenticação",
        "description": "Login, registro, validação de token e sessão."
    },
    {
        "name": "Configuração",
        "description": "Validação e gerenciamento de conexões/configurações de banco."
    },
    {
        "name": "Configuração do Usuário",
        "description": "Persistência das configurações por usuário autenticado."
    },
    {
        "name": "Dashboard UI",
        "description": "Endpoints consumidos pelas telas Home/Monitoramento da aplicação web."
    },
    {
        "name": "Operações",
        "description": "Rotinas de geração e processamento de dados no ambiente."
    },
    {
        "name": "gRPC Jobs",
        "description": "Disparo e acompanhamento de jobs assíncronos de geração."
    },
    {
        "name": "BI",
        "description": "Endpoints otimizados para consumo por Power BI e integrações analíticas."
    }
]

app = FastAPI(
    title="PLD Data Generator API",
    version="2.0.0",
    description=(
        "API para geração de dados PLD, monitoramento operacional e integração analítica.\n\n"
        "**Autenticação**\n"
        "- UI: JWT no header `Authorization: Bearer <token>` + `config_key`\n"
        "- BI: `X-BI-API-Key` (quando `BI_API_KEY` estiver configurada) ou JWT + `config_key`\n\n"
        "**Configuração ativa**\n"
        "- Endpoints de negócio exigem `config_key` ativa no backend."
    ),
    openapi_tags=OPENAPI_TAGS
)

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

fake = Faker("pt_BR")

PF_NOMES = ["ALICE", "BRUNO", "CARLA", "DANIEL", "ELISA", "FELIPE", "GABRIELA", "HENRIQUE", "ISABELA", "JOAO", "LARISSA", "MARCOS"]
PF_SOBRENOMES = ["SILVA", "SOUZA", "OLIVEIRA", "PEREIRA", "COSTA", "ALMEIDA", "ROCHA", "GOMES", "MARTINS", "ARAUJO"]
PJ_RADICAIS = ["ALFA", "NOVA", "PRIME", "VETOR", "ORION", "AURORA", "VERTICE", "ATLANTIS", "INTEGRA", "SIGMA"]
PJ_COMPLEMENTOS = ["CONSULTORIA", "TECNOLOGIA", "SERVICOS", "COMERCIO", "INDUSTRIA", "SOLUCOES", "LOGISTICA", "PARTICIPACOES"]
PJ_SUFIXOS = ["LTDA", "S/A", "EIRELI"]


def _gerar_cpf_fake() -> str:
    return ''.join(random.choices(string.digits, k=11))


def _gerar_rg_fake() -> str:
    return ''.join(random.choices(string.digits, k=9))


def _clean_name_no_digits(value: str) -> str:
    base = re.sub(r"\d", "", str(value or "").upper())
    return re.sub(r"\s+", " ", base).strip()


def _fake_pf_name() -> str:
    return _clean_name_no_digits(f"{random.choice(PF_NOMES)} {random.choice(PF_SOBRENOMES)}")


def _fake_pj_name() -> str:
    return _clean_name_no_digits(f"{random.choice(PJ_RADICAIS)} {random.choice(PJ_COMPLEMENTOS)} {random.choice(PJ_SUFIXOS)}")


def _detectar_versao_sistema(session) -> str:
    def _normalize_versao(raw_value) -> Optional[str]:
        if raw_value is None:
            return None

        value = str(raw_value).strip().upper()
        if not value:
            return None

        if value in {"V9", "9", "09", "009"}:
            return "V9"
        if value in {"V8", "8", "08", "008"}:
            return "V8"

        if "V9" in value:
            return "V9"
        if "V8" in value:
            return "V8"

        match = re.search(r"\d+", value)
        if match:
            try:
                major = int(match.group(0))
                return "V9" if major >= 9 else "V8"
            except Exception:
                return None

        digits = re.sub(r"\D", "", value)
        if digits:
            if digits.startswith("9") or "009" in digits:
                return "V9"
            if digits.startswith("8") or "008" in digits:
                return "V8"

        return None

    try:
        row = session.execute(text("SELECT TOP 1 * FROM AD_SISTEMAS_VERSOES WITH (NOLOCK) ORDER BY 1 DESC")).fetchone()
        if row:
            cd_versao = None
            try:
                mapping = row._mapping
                if "CD_VERSAO" in mapping:
                    cd_versao = mapping["CD_VERSAO"]
                else:
                    for key in mapping.keys():
                        if str(key).upper() == "CD_VERSAO":
                            cd_versao = mapping[key]
                            break
            except Exception:
                cd_versao = None

            if cd_versao is None:
                try:
                    keys = list(row._mapping.keys())
                    upper_keys = [str(k).upper() for k in keys]
                    if "CD_VERSAO" in upper_keys:
                        idx = upper_keys.index("CD_VERSAO")
                        cd_versao = row[idx]
                except Exception:
                    cd_versao = None

            if cd_versao is None:
                cd_versao = row[0]

            detected = _normalize_versao(cd_versao)
            if detected:
                return detected
        return "V8"
    except Exception:
        return "V8"


def _gerar_data_pld(modo: str, data_referencia_base):
    hoje = datetime.now().date()
    if modo == "mes_atual":
        dia = random.randint(1, hoje.day) if hoje.day > 1 else 1
        return hoje.replace(day=dia)
    if modo == "mes_anterior":
        primeiro = hoje.replace(day=1)
        ultimo_anterior = primeiro - timedelta(days=1)
        dia = random.randint(1, ultimo_anterior.day)
        return ultimo_anterior.replace(day=dia)
    return data_referencia_base


def _movfin_nacional(session, versao: str, clientes: list, data_ref, modo_data: str, qtd_solicitada: int):
    tabela = "TAB_CLIENTES_MOVFIN_PLD"
    lista_formas = ["Pix", "TED", "DOC", "TEC", "Boletos", "Cheques"]
    lista_produtos = ["Conta de Depósito", "Cartão de Crédito", "Crédito Pessoal", "Financiamento", "PIX", "TED", "DOC"]
    lista_nat_operacao = ["10000", "12407", "40000"]

    colunas = [
        "CD_IDENTIFICACAO", "CD_VEIC_LEGAL", "CD_AGENCIA", "CD_AGENCIA_MOVTO",
        "CD_CONTA", "CD_CLIENTE", "DT_MOVIMENTA", "DTHR_MOVIMENTA", "CD_MOEDA",
        "VL_OPERACAO", "TP_DEB_CRED", "CD_FORMA", "DE_CONTRAPARTE", "DE_BANCO_CONTRA",
        "DE_AGENCIA_CONTRA", "CD_CONTA_CONTRA", "CD_PAIS_CONTRA", "DE_ORIGEM_OPE",
        "CD_PRODUTO", "DE_FINALIDADE", "CPF_CNPJ_CONTRA", "DS_CIDADE_CONTRA",
        "DS_COMP_HISTORICO", "VL_RENDIMENTO", "DT_PREV_LIQUIDACAO", "CD_ISPB_EMISSOR",
        "NR_CHEQUE", "DE_TP_DOCTO_CONTRA", "NR_DOCTO_CONTRA", "DE_EXECUTOR",
        "CPF_EXECUTOR", "NR_PASSAPORTE_EXEC", "FL_IOF_CARENCIA", "DE_ORDENANTE",
        "UF_MOVTO"
    ]

    if versao == "V8":
        colunas.extend(["NR_POS", "DS_CIDADE_POS", "DS_CANAL", "DS_ORIGEM_RECURSO", "DS_DESTINO_RECURSO", "CD_PROVISIONAMENTO", "DS_AMBIENTE_NEG", "CD_NAT_OPERACAO"])
    else:
        colunas.extend(["CD_NAT_OPERACAO", "NR_POS", "DS_CIDADE_POS", "DS_CANAL", "DS_ORIGEM_RECURSO", "DS_DESTINO_RECURSO", "CD_PROVISIONAMENTO", "DS_AMBIENTE_NEG", "CD_COMPRA"])

    placeholders = ", ".join([f":{c}" for c in colunas])
    sql = text(f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES ({placeholders})")

    lote = []
    vezes = int(qtd_solicitada) if qtd_solicitada else 1
    for cli in clientes:
        id_cliente_real = str(cli[0])[:20]
        for _ in range(vezes):
            for natureza in ["C", "D"]:
                dt_final = _gerar_data_pld(modo_data, data_ref)
                dthr = datetime.combine(dt_final, datetime.now().time())
                registro = {
                    "CD_IDENTIFICACAO": str(uuid.uuid4())[:40], "CD_VEIC_LEGAL": 1, "CD_AGENCIA": "0001", "CD_AGENCIA_MOVTO": "0001",
                    "CD_CONTA": "12345-6", "CD_CLIENTE": id_cliente_real, "DT_MOVIMENTA": dt_final, "DTHR_MOVIMENTA": dthr, "CD_MOEDA": "BRL",
                    "VL_OPERACAO": round(random.uniform(100, 5000), 2), "TP_DEB_CRED": natureza, "CD_FORMA": random.choice(lista_formas),
                    "DE_CONTRAPARTE": _fake_pf_name()[:120], "DE_BANCO_CONTRA": "BANCO X", "DE_AGENCIA_CONTRA": "0001", "CD_CONTA_CONTRA": "12345",
                    "CD_PAIS_CONTRA": "BRASIL", "DE_ORIGEM_OPE": "SISTEMA", "CD_PRODUTO": random.choice(lista_produtos), "DE_FINALIDADE": "PAGAMENTO",
                    "CPF_CNPJ_CONTRA": "000.000.000-00", "DS_CIDADE_CONTRA": "SAO PAULO", "DS_COMP_HISTORICO": "CARGA ALEATORIA", "VL_RENDIMENTO": 0,
                    "DT_PREV_LIQUIDACAO": dt_final, "CD_ISPB_EMISSOR": 12345678, "NR_CHEQUE": "0", "DE_TP_DOCTO_CONTRA": "DOC", "NR_DOCTO_CONTRA": "0",
                    "DE_EXECUTOR": "EXECUTOR", "CPF_EXECUTOR": "000.000.000-00", "NR_PASSAPORTE_EXEC": "0", "FL_IOF_CARENCIA": 0,
                    "DE_ORDENANTE": _fake_pf_name()[:120], "UF_MOVTO": "SP", "CD_NAT_OPERACAO": random.choice(lista_nat_operacao),
                    "NR_POS": "POS01", "DS_CIDADE_POS": "SAO PAULO", "DS_CANAL": "WEB", "DS_ORIGEM_RECURSO": "RECURSO",
                    "DS_DESTINO_RECURSO": "DESTINO", "CD_PROVISIONAMENTO": "PROV01", "DS_AMBIENTE_NEG": "VIRTUAL", "CD_COMPRA": f"CMP-{random.randint(100,999)}"
                }
                lote.append({c: registro.get(c) for c in colunas})

                if len(lote) >= 5000:
                    session.execute(sql, lote)
                    lote = []

    if lote:
        session.execute(sql, lote)


def _movfin_moeda_estrangeira(session, versao: str, clientes: list, data_ref, modo_data: str, qtd_solicitada: int):
    tabela = "TAB_CLIENTES_MOVFIN_ME_PLD"
    lista_formas = ["Pix", "TED", "DOC", "TEC", "Boletos", "Cheques"]
    lista_produtos = ["CONTA DEPOSITO", "CARTAO CREDITO", "CAMBIO", "TED", "PIX"]
    lista_moedas = ["USD", "EUR", "GBP"]
    lista_nat_operacao = ["10000", "12407", "40000"]

    colunas_base = [
        "CD_IDENTIFICACAO", "CD_VEIC_LEGAL", "CD_AGENCIA", "CD_CONTA", "CD_CLIENTE", "DT_MOVIMENTA", "DTHR_MOVIMENTA", "CD_MOEDA_ME",
        "VL_OPERACAO_ME", "TX_COTACAO_ME", "VL_OPERACAO_USD", "TP_DEB_CRED", "CD_FORMA", "DE_CONTRAPARTE", "DE_BANCO_CONTRA",
        "DE_AGENCIA_CONTRA", "CD_CONTA_CONTRA", "CD_PAIS_CONTRA", "DE_ORIGEM_OPE", "CD_PRODUTO", "DE_FINALIDADE", "CPF_CNPJ_CONTRA",
        "DS_CIDADE_CONTRA", "DS_COMP_HISTORICO", "DE_TP_DOCTO_CONTRA", "NR_DOCTO_CONTRA", "DE_EXECUTOR", "CPF_EXECUTOR",
        "NR_PASSAPORTE_EXEC", "DE_ORDENANTE"
    ]
    colunas_finais = ["CD_NAT_OPERACAO", "UF_MOVTO", "DE_OPERADOR", "TX_PTAX"] if versao == "V9" else ["UF_MOVTO", "DE_OPERADOR", "TX_PTAX", "CD_NAT_OPERACAO"]
    colunas = colunas_base + colunas_finais

    placeholders = ", ".join([f":{c}" for c in colunas])
    sql = text(f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES ({placeholders})")

    lote = []
    vezes = int(qtd_solicitada) if qtd_solicitada else 1
    hora_atual = datetime.now().time()

    for cli in clientes:
        id_cliente_real = str(cli[0])[:20]
        for _ in range(vezes):
            for natureza in ["C", "D"]:
                dt_final = _gerar_data_pld(modo_data, data_ref)
                dthr = datetime.combine(dt_final, hora_atual)
                moeda = random.choice(lista_moedas)
                vl_me = round(random.uniform(500, 10000), 2)
                cotacao = round(random.uniform(5.0, 6.0), 4)
                vl_usd = round(vl_me if moeda == "USD" else (vl_me * 1.1), 2)

                registro = {
                    "CD_IDENTIFICACAO": str(uuid.uuid4())[:40], "CD_VEIC_LEGAL": 1, "CD_AGENCIA": "0001", "CD_CONTA": "ME-9988-X", "CD_CLIENTE": id_cliente_real,
                    "DT_MOVIMENTA": dt_final, "DTHR_MOVIMENTA": dthr, "CD_MOEDA_ME": moeda, "VL_OPERACAO_ME": vl_me, "TX_COTACAO_ME": cotacao,
                    "VL_OPERACAO_USD": vl_usd, "TP_DEB_CRED": natureza, "CD_FORMA": random.choice(lista_formas), "DE_CONTRAPARTE": _fake_pj_name()[:120],
                    "DE_BANCO_CONTRA": "INTER BANK CORP", "DE_AGENCIA_CONTRA": "AG-LONDON-01", "CD_CONTA_CONTRA": "ACC-776655", "CD_PAIS_CONTRA": "GBR",
                    "DE_ORIGEM_OPE": "CAMBIO_ONLINE", "CD_PRODUTO": random.choice(lista_produtos), "DE_FINALIDADE": "PAGAMENTO_INVOICE", "CPF_CNPJ_CONTRA": id_cliente_real,
                    "DS_CIDADE_CONTRA": "LONDRES", "DS_COMP_HISTORICO": "LIQ_CAMBIO_ME", "DE_TP_DOCTO_CONTRA": "INVOICE", "NR_DOCTO_CONTRA": str(random.randint(5000, 8000)),
                    "DE_EXECUTOR": _fake_pf_name()[:120], "CPF_EXECUTOR": "00000000000", "NR_PASSAPORTE_EXEC": "N/A", "DE_ORDENANTE": _fake_pj_name()[:120],
                    "UF_MOVTO": "SP", "DE_OPERADOR": "OPERADOR_AUTO", "TX_PTAX": cotacao, "CD_NAT_OPERACAO": random.choice(lista_nat_operacao)
                }
                lote.append({c: registro.get(c) for c in colunas})

                if len(lote) >= 5000:
                    session.execute(sql, lote)
                    lote = []

    if lote:
        session.execute(sql, lote)


def _movfin_intermediador(session, clientes: list, data_ref, modo_data: str, qtd_solicitada: int):
    tabela = "TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD"
    colunas = [
        "CD_IDENTIFICACAO", "CD_CLIENTE", "DT_MOVIMENTA", "NR_ORDEMPAGAMENTO", "DT_PAGAMENTO", "CPF_CNPJ", "DE_CLIENTE", "TP_DOC",
        "DE_MOEDA", "VL_ME", "VL_USD", "VL_CONTABIL_MN", "VL_FECHAMENTOVENDA_MN", "VL_GIRO", "DS_SITUACAO", "TP_MOVIMENTACAO",
        "DE_ORIGINADOR", "TP_DOCUMENTOORIGINADOR", "CPF_CNPJ_ORIGINADOR", "DE_PAISORIGINADOR", "DE_FAVORECIDO", "TP_DOCUMENTOFAVORECIDO",
        "CPF_CNPJ_FAVORECIDO", "DE_PAISFAVORECIDO", "DE_DETALHESPAGAMENTO", "TP_CONTACORRENTE", "DE_ORIGEM"
    ]
    placeholders = ", ".join([f":{c}" for c in colunas])
    sql = text(f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES ({placeholders})")

    clientes_pj = [c for c in clientes if str(c[2] or "").strip() == "02"]
    if not clientes_pj:
        return

    lote = []
    tipos_obrigatorios = ["DebitoRemessa", "OrdemDePagamento"]
    opcoes_favorecido = ["Netflix", "Microsoft", "Spotify"]
    opcoes_pais_fav = ["USA", "Canada", "Italia"]
    vezes = int(qtd_solicitada) if qtd_solicitada else 1

    for cli in clientes_pj:
        cd_cliente_atual = str(cli[0] or "").strip()
        de_cliente_atual = _clean_name_no_digits(str(cli[1] or "").strip())
        if not de_cliente_atual:
            de_cliente_atual = _fake_pj_name()
        for _ in range(vezes):
            for tipo_mov in tipos_obrigatorios:
                dt_mov = _gerar_data_pld(modo_data, data_ref)
                vl_brl = round(random.uniform(1000, 5000), 2)
                registro = {
                    "CD_IDENTIFICACAO": str(uuid.uuid4())[:40], "CD_CLIENTE": cd_cliente_atual, "DT_MOVIMENTA": dt_mov,
                    "NR_ORDEMPAGAMENTO": str(random.randint(100000, 999999)), "DT_PAGAMENTO": dt_mov, "CPF_CNPJ": cd_cliente_atual,
                    "DE_CLIENTE": de_cliente_atual, "TP_DOC": "CNPJ", "DE_MOEDA": "DOLAR AMERICANO", "VL_ME": round(vl_brl / 5.3, 2),
                    "VL_USD": round(vl_brl / 5.3, 2), "VL_CONTABIL_MN": vl_brl, "VL_FECHAMENTOVENDA_MN": vl_brl, "VL_GIRO": 0.0,
                    "DS_SITUACAO": "LIQUIDADA", "TP_MOVIMENTACAO": tipo_mov, "DE_ORIGINADOR": _fake_pf_name()[:120], "TP_DOCUMENTOORIGINADOR": "CPF",
                    "CPF_CNPJ_ORIGINADOR": _gerar_cpf_fake(), "DE_PAISORIGINADOR": "Brasil", "DE_FAVORECIDO": random.choice(opcoes_favorecido),
                    "TP_DOCUMENTOFAVORECIDO": "CNPJ", "CPF_CNPJ_FAVORECIDO": "", "DE_PAISFAVORECIDO": random.choice(opcoes_pais_fav),
                    "DE_DETALHESPAGAMENTO": "PAGTO SERVICOS", "TP_CONTACORRENTE": "CONTA CORRENTE", "DE_ORIGEM": 1
                }
                lote.append({c: registro.get(c) for c in colunas})

                if len(lote) >= 5000:
                    session.execute(sql, lote)
                    lote = []

    if lote:
        session.execute(sql, lote)

def _get_user_id_from_request(request: Request) -> Optional[str]:
    """
    Extrai user_id do token JWT no header Authorization.
    Retorna None se token ausente ou inválido.
    """
    authorization = request.headers.get("Authorization")
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


def _validate_user_owns_config(user_id: str, config_key: str) -> bool:
    """
    Valida se o config_key pertence ao usuário.
    Verifica se config_key está nas bases configuradas pelo usuário.
    """
    try:
        user_config = AuthDB.get_user_config(user_id)
        if not user_config:
            return False
        
        # Verificar se config_key existe nas bases do usuário
        bases = user_config.get("bases", [])
        for base in bases:
            if base.get("config_key") == config_key:
                return True
        
        return False
    except Exception as e:
        logger.error(f"Erro ao validar config do usuário: {e}")
        return False


def _require_user_config(request: Request, body: dict) -> tuple[Optional[str], Optional[str], Optional[JSONResponse]]:
    """
    Helper que valida autenticação e autorização para config_key.
    
    Returns:
        (user_id, config_key, error_response)
        - Se sucesso: (user_id, config_key, None)
        - Se erro: (None, None, JSONResponse com erro)
    
    Usage:
        user_id, config_key, error = _require_user_config(request, body)
        if error:
            return error
        
        # Continuar com lógica da rota...
    """
    # 1. Validar autenticação
    user_id = _get_user_id_from_request(request)
    if not user_id:
        return None, None, JSONResponse(
            {"erro": "Não autenticado. Token JWT ausente ou inválido."},
            status_code=401
        )
    
    # 2. Obter config_key
    config_key = _resolve_config_key(request, body or {})
    if not config_key:
        return None, None, JSONResponse(
            {"erro": "config_key não informado"},
            status_code=400
        )
    
    # 3. Validar autorização
    if not _validate_user_owns_config(user_id, config_key):
        logger.warning(f"Usuário {user_id} tentou acessar config_key {config_key} sem autorização")
        return None, None, JSONResponse(
            {"erro": "Você não tem permissão para acessar esta configuração"},
            status_code=403
        )
    
    return user_id, config_key, None


def _extract_server_and_base(config_key: str) -> tuple[str, str]:
    """
    Extrai servidor e base a partir do config_key no formato:
    session_id:usuario@servidor:banco
    """
    if not config_key:
        return "N/A", "N/A"

    try:
        prefix, base = config_key.rsplit(":", 1)
        server = "N/A"
        if "@" in prefix:
            server = prefix.split("@", 1)[1]
        return server or "N/A", base or "N/A"
    except Exception:
        return "N/A", "N/A"


def _require_bi_access(request: Request, config_key: Optional[str]) -> tuple[Optional[str], Optional[str], Optional[JSONResponse]]:
    """
    Validação para endpoints BI.

    Aceita duas estratégias:
    1) API key técnica via header X-BI-API-Key (quando BI_API_KEY estiver configurada)
    2) JWT do usuário + autorização do config_key (fallback/default)
    """
    resolved_config_key = config_key or request.headers.get("X-Config-Key") or request.headers.get("x-config-key")
    if not resolved_config_key:
        return None, None, JSONResponse({"erro": "config_key não informado"}, status_code=400)

    # API key técnica para integração Power BI
    configured_bi_api_key = (os.getenv("BI_API_KEY") or "").strip()
    request_bi_api_key = (request.headers.get("X-BI-API-Key") or request.headers.get("x-bi-api-key") or "").strip()
    if configured_bi_api_key and request_bi_api_key and request_bi_api_key == configured_bi_api_key:
        return "bi_service", resolved_config_key, None

    # Fallback para JWT de usuário
    user_id = _get_user_id_from_request(request)
    if not user_id:
        return None, None, JSONResponse(
            {"erro": "Não autenticado. Token JWT ausente ou inválido."},
            status_code=401
        )

    if not _validate_user_owns_config(user_id, resolved_config_key):
        return None, None, JSONResponse(
            {"erro": "Você não tem permissão para acessar esta configuração"},
            status_code=403
        )

    return user_id, resolved_config_key, None


def _get_clientes_pendentes_count(config_key: str) -> int:
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
            return int(result[0] if result else 0)
    except Exception:
        return 0


def _get_erros_servico_24h(config_key: str) -> int:
    try:
        with get_db_session(config_key) as session:
            return int(session.execute(text("""
                SELECT COUNT(1) FROM TB_SERVICO_EXEC WITH (NOLOCK)
                WHERE DS_ERRO <> ''
                  AND DT_HR_EXECUTADO >= DATEADD(hh, -24, GETDATE())
            """)).scalar() or 0)
    except Exception:
        return 0


def _collect_bi_home(config_key: str) -> dict:
    dash = _collect_dashboard(config_key)
    fila_pendente = int(dash.get("fila_geral", {}).get("pendente", 0) or 0)
    processados = int(dash.get("fila_geral", {}).get("processados", 0) or 0)
    log_total = int(dash.get("log_pesquisas", {}).get("total_registros", 0) or 0)
    erros_24h = _get_erros_servico_24h(config_key)
    clientes_pendentes = _get_clientes_pendentes_count(config_key)

    tempos = [float(item.get("tempo", 0) or 0) for item in dash.get("performance", [])]
    latencia_media = round(sum(tempos) / len(tempos), 2) if tempos else 0.0

    status_geral = "ESTAVEL"
    if fila_pendente > 1000 or erros_24h > 50:
        status_geral = "CRITICO"
    elif fila_pendente > 500 or erros_24h > 10 or clientes_pendentes > 0:
        status_geral = "ATENCAO"

    server, base = _extract_server_and_base(config_key)

    def _kpi_status(valor: float, low: float, high: float, invert: bool = False) -> str:
        if invert:
            if valor >= high:
                return "ok"
            if valor >= low:
                return "warning"
            return "critical"

        if valor <= low:
            return "ok"
        if valor <= high:
            return "warning"
        return "critical"

    return {
        "base": base,
        "servidor": server,
        "dt_coleta": datetime.utcnow().isoformat() + "Z",
        "status_geral": status_geral,
        "janela_referencia": "24h",
        "kpis": [
            {"kpi": "fila_pendente", "valor": fila_pendente, "unidade": "qtd", "status": _kpi_status(fila_pendente, 1000, 3000)},
            {"kpi": "processados_total", "valor": processados, "unidade": "qtd", "status": "ok"},
            {"kpi": "erros_24h", "valor": erros_24h, "unidade": "qtd", "status": _kpi_status(erros_24h, 10, 50)},
            {"kpi": "clientes_pendentes", "valor": clientes_pendentes, "unidade": "qtd", "status": _kpi_status(clientes_pendentes, 0, 50)},
            {"kpi": "latencia_media_ms", "valor": latencia_media, "unidade": "ms", "status": _kpi_status(latencia_media, 300, 800)},
            {"kpi": "log_pesquisas_total", "valor": log_total, "unidade": "qtd", "status": "ok"}
        ]
    }


def _collect_bi_monitoramento(config_key: str, top_n: int = 100) -> dict:
    server, base = _extract_server_and_base(config_key)
    top_n = max(1, min(int(top_n or 100), 500))

    dash = _collect_dashboard(config_key)
    filas_por_regra = [
        {
            "regra": item.get("regra", ""),
            "qtd_pendente": int(item.get("qtd", 0) or 0)
        }
        for item in dash.get("regras", [])[:top_n]
    ]

    tempo_por_regra: dict[str, dict[str, float]] = {}
    tabelas_exec = [
        "ADSVC_EXECUTANDO", "ADSVC_EXECUTANDO_MF1", "ADSVC_EXECUTANDO_MF2",
        "ADSVC_EXECUTANDO_MF3", "ADSVC_EXECUTANDO_MF4", "ADSVC_EXECUTANDO_MF5",
        "ADSVC_EXECUTANDO_LV1", "ADSVC_EXECUTANDO_LV2", "ADSVC_EXECUTANDO_LV3",
        "ADSVC_EXECUTANDO_LV4", "ADSVC_EXECUTANDO_LV5"
    ]

    with get_db_session(config_key) as session:
        for table_name in tabelas_exec:
            try:
                rows = session.execute(text(f"""
                    SELECT LEFT(DS_COMANDO1, 20) AS regra,
                           AVG(CAST(QT_TEMPO_EXEC AS FLOAT)) AS tempo_medio
                    FROM {table_name} WITH (NOLOCK)
                    GROUP BY LEFT(DS_COMANDO1, 20)
                """)).fetchall()

                for row in rows:
                    regra = (row[0] or "").strip()
                    if not regra:
                        continue
                    media = float(row[1] or 0)
                    if regra not in tempo_por_regra:
                        tempo_por_regra[regra] = {"sum": 0.0, "count": 0.0}
                    tempo_por_regra[regra]["sum"] += media
                    tempo_por_regra[regra]["count"] += 1.0
            except Exception:
                continue

        tempo_medio_por_regra = sorted([
            {
                "regra": regra,
                "tempo_medio_ms": round((dados["sum"] / dados["count"]), 2)
            }
            for regra, dados in tempo_por_regra.items() if dados["count"] > 0
        ], key=lambda item: item["tempo_medio_ms"], reverse=True)[:top_n]

        try:
            services_rows = session.execute(text(f"""
                SELECT TOP {top_n}
                    s.CD_SERVICO,
                    s.DS_SERVICO,
                    MAX(ISNULL(p.FL_ATIVADO, 0)) AS FL_ATIVADO,
                    SUM(CASE WHEN e.DS_ERRO <> '' THEN 1 ELSE 0 END) AS ERROS_24H
                FROM TB_SERVICO s WITH (NOLOCK)
                LEFT JOIN TB_SERVICO_PARAM p WITH (NOLOCK)
                    ON p.CD_SERVICO = s.CD_SERVICO
                LEFT JOIN TB_SERVICO_EXEC e WITH (NOLOCK)
                    ON e.CD_SERVICO = s.CD_SERVICO
                   AND e.DT_HR_EXECUTADO >= DATEADD(hh, -24, GETDATE())
                GROUP BY s.CD_SERVICO, s.DS_SERVICO
                ORDER BY s.CD_SERVICO
            """)).fetchall()
            servicos = [
                {
                    "cd_servico": int(row[0] or 0),
                    "descricao": row[1] or "",
                    "status": "ATIVADO" if int(row[2] or 0) == 1 else "DESATIVADO",
                    "erros_24h": int(row[3] or 0)
                }
                for row in services_rows
            ]
        except Exception:
            servicos = []

        integracao = []
        domains = [
            ("MOVFIN", "TB_INTEG_MOVFIN", "DT_MOVIMENTA"),
            ("MOVFIN_ME", "TB_INTEG_MOVFIN_ME", "DT_MOVIMENTA"),
            ("SINACOR", "TB_INTEG_ORDENS_SINACOR", "DT_MOVIMENTO"),
            ("INTERMEDIADOR", "TB_MOVFIN_INTERMEDIADOR", "DT_MOVIMENTA")
        ]
        for dominio, table_name, date_col in domains:
            try:
                row = session.execute(text(f"""
                    SELECT COUNT(1) AS qtd, MAX({date_col}) AS dt_mais_recente
                    FROM {table_name} WITH (NOLOCK)
                """)).fetchone()
                integracao.append({
                    "dominio": dominio,
                    "qtd_total": int((row[0] if row else 0) or 0),
                    "dt_mais_recente": row[1].isoformat() if row and row[1] else None
                })
            except Exception:
                continue

        try:
            ocorrencias_rows = session.execute(text(f"""
                SELECT TOP {top_n}
                    o.CD_REFERENCIA,
                    COUNT(1) AS QTD
                FROM TB_OCORRENCIAS_CLIENTE oc WITH (NOLOCK)
                INNER JOIN TB_OCORRENCIAS o WITH (NOLOCK)
                    ON oc.CD_OCORRENCIA = o.CD_OCORRENCIA
                WHERE oc.DT_OCORRENCIA >= DATEADD(day, -100, GETDATE())
                GROUP BY o.CD_REFERENCIA
                ORDER BY QTD DESC
            """)).fetchall()
            ocorrencias = [
                {
                    "ocorrencia": row[0] or "",
                    "qtd": int(row[1] or 0)
                }
                for row in ocorrencias_rows
            ]
        except Exception:
            ocorrencias = []

    return {
        "base": base,
        "servidor": server,
        "dt_coleta": datetime.utcnow().isoformat() + "Z",
        "filas_por_regra": filas_por_regra,
        "tempo_medio_por_regra": tempo_medio_por_regra,
        "servicos": servicos,
        "integracao": integracao,
        "ocorrencias": ocorrencias
    }


def _get_graphql_context(request: Request):
    """
    Fornece contexto para resolvers GraphQL.
    Valida autenticação e autorização antes de fornecer config_key.
    """
    # Extrair config_key do request
    config_key = _resolve_config_key(request, {})
    
    # Se não há config_key, retornar contexto sem ele
    if not config_key:
        return {"config_key": None, "user_id": None, "error": "config_key não informado"}
    
    # Validar autenticação
    user_id = _get_user_id_from_request(request)
    if not user_id:
        return {"config_key": None, "user_id": None, "error": "Não autenticado"}
    
    # Validar autorização
    if not _validate_user_owns_config(user_id, config_key):
        logger.warning(f"GraphQL: Usuário {user_id} tentou acessar config_key {config_key} sem autorização")
        return {"config_key": None, "user_id": user_id, "error": "Não autorizado para esta configuração"}
    
    # Sucesso - contexto válido
    return {"config_key": config_key, "user_id": user_id, "error": None}

app.include_router(GraphQLRouter(schema, context_getter=_get_graphql_context), prefix="/graphql")

def _resolve_config_key(request: Request, body: dict) -> str | None:
    """
    Resolve config_key de body ou headers.
    ⚠️ ATENÇÃO: Esta função NÃO valida se config_key pertence ao usuário!
    Use _validate_user_owns_config() para validar.
    """
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

@app.get("/", tags=["Sistema"], summary="Mensagem raiz da API")
async def root():
    return {"message": "PLD Data Generator API v2.0"}

@app.get("/health", tags=["Sistema"], summary="Health check da API")
async def health():
    return {"status": "online", "version": "2.0.0", "timestamp": datetime.now().isoformat()}


@app.get(
    "/bi/home",
    tags=["BI"],
    summary="Indicadores executivos para Power BI",
    description="Retorna snapshot executivo (KPIs) da base informada para consumo analítico.",
    responses={
        200: {
            "description": "Snapshot executivo retornado com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "base": "EGUARDIAN",
                        "servidor": "ADV-NOT000337,1433",
                        "dt_coleta": "2026-02-25T21:30:00Z",
                        "status_geral": "ESTAVEL",
                        "janela_referencia": "24h",
                        "kpis": [
                            {"kpi": "fila_pendente", "valor": 123, "unidade": "qtd", "status": "ok"},
                            {"kpi": "processados_total", "valor": 45678, "unidade": "qtd", "status": "ok"},
                            {"kpi": "erros_24h", "valor": 3, "unidade": "qtd", "status": "warning"},
                            {"kpi": "clientes_pendentes", "valor": 12, "unidade": "qtd", "status": "warning"},
                            {"kpi": "latencia_media_ms", "valor": 240.5, "unidade": "ms", "status": "ok"},
                            {"kpi": "log_pesquisas_total", "valor": 90210, "unidade": "qtd", "status": "ok"}
                        ]
                    }
                }
            }
        },
        401: {"description": "Não autenticado (JWT ausente/inválido ou BI API key inválida)"},
        403: {"description": "Sem permissão para acessar a configuração informada"},
        404: {"description": "config_key não ativa no backend"},
        500: {"description": "Erro interno ao coletar dados"}
    }
)
async def bi_home(
    request: Request,
    config_key: Optional[str] = Query(None, description="Configuração ativa da base (config_key)"),
    x_bi_api_key: Optional[str] = Header(None, alias="X-BI-API-Key", description="Chave técnica BI (opcional quando BI_API_KEY estiver configurada)")
):
    """
    Endpoint executivo para Power BI.
    Suporta autenticação por X-BI-API-Key (quando BI_API_KEY estiver configurada)
    ou JWT + autorização da config_key.
    """
    _, resolved_config_key, error = _require_bi_access(request, config_key)
    if error:
        return error

    try:
        if not db_manager.obter_engine(resolved_config_key):
            return JSONResponse({"erro": "config_key não ativa no backend"}, status_code=404)
        return _collect_bi_home(resolved_config_key)
    except Exception as e:
        logger.error(f"Erro /bi/home: {e}")
        return JSONResponse({"erro": str(e)}, status_code=500)


@app.get(
    "/bi/monitoramento",
    tags=["BI"],
    summary="Detalhamento operacional para Power BI",
    description="Retorna métricas de filas, tempos médios, serviços, integração e ocorrências.",
    responses={
        200: {
            "description": "Detalhamento operacional retornado com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "base": "EGUARDIAN",
                        "servidor": "ADV-NOT000337,1433",
                        "dt_coleta": "2026-02-25T21:30:00Z",
                        "filas_por_regra": [
                            {"regra": "REGRA_X", "qtd_pendente": 1200},
                            {"regra": "REGRA_Y", "qtd_pendente": 450}
                        ],
                        "tempo_medio_por_regra": [
                            {"regra": "REGRA_X", "tempo_medio_ms": 380.5},
                            {"regra": "REGRA_Y", "tempo_medio_ms": 120.4}
                        ],
                        "servicos": [
                            {"cd_servico": 131, "descricao": "API", "status": "ATIVADO", "erros_24h": 1}
                        ],
                        "integracao": [
                            {"dominio": "MOVFIN", "qtd_total": 34567, "dt_mais_recente": "2026-02-25T20:55:00"}
                        ],
                        "ocorrencias": [
                            {"ocorrencia": "OC123", "qtd": 77}
                        ]
                    }
                }
            }
        },
        401: {"description": "Não autenticado (JWT ausente/inválido ou BI API key inválida)"},
        403: {"description": "Sem permissão para acessar a configuração informada"},
        404: {"description": "config_key não ativa no backend"},
        500: {"description": "Erro interno ao coletar dados"}
    }
)
async def bi_monitoramento(
    request: Request,
    config_key: Optional[str] = Query(None, description="Configuração ativa da base (config_key)"),
    top_n: int = Query(100, ge=1, le=500, description="Limite de linhas por bloco de retorno"),
    x_bi_api_key: Optional[str] = Header(None, alias="X-BI-API-Key", description="Chave técnica BI (opcional quando BI_API_KEY estiver configurada)")
):
    """
    Endpoint detalhado para Power BI.
    """
    _, resolved_config_key, error = _require_bi_access(request, config_key)
    if error:
        return error

    try:
        if not db_manager.obter_engine(resolved_config_key):
            return JSONResponse({"erro": "config_key não ativa no backend"}, status_code=404)
        return _collect_bi_monitoramento(resolved_config_key, top_n=top_n)
    except Exception as e:
        logger.error(f"Erro /bi/monitoramento: {e}")
        return JSONResponse({"erro": str(e)}, status_code=500)

@app.post("/login", tags=["Sistema"], summary="Login legado simples")
async def login(body: dict):
    username = body.get("username")
    password = body.get("password")
    if username == "admin" and password == "1234":
        return {"status": "ok", "user": "admin", "tipo": "ADMIN"}
    return JSONResponse(content={"message":"Erro"}, status_code=401)

@app.post("/api/saude-servidor", tags=["Dashboard UI"], summary="Indicadores de saúde do servidor")
async def saude_servidor(request: Request, body: dict):
    """
    Retorna indicadores de saúde do servidor.
    Requer autenticação JWT e valida que config_key pertence ao usuário.
    """
    # Validar autenticação e autorização
    user_id, config_key, error = _require_user_config(request, body or {})
    if error:
        return error
    
    # Executar operação
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

@app.post("/api/clientes-pendentes", tags=["Dashboard UI"], summary="Quantidade de clientes pendentes")
async def clientes_pendentes(request: Request, body: dict):
    """Retorna quantidade de clientes sem integrar. Requer autenticação."""
    # Validar autenticação e autorização
    user_id, config_key, error = _require_user_config(request, body or {})
    if error:
        return error
    
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

@app.post("/status_dashboard", tags=["Dashboard UI"], summary="Resumo consolidado do dashboard")
async def status_dashboard(request: Request, body: dict):
    user_id, config_key, error = _require_user_config(request, body or {})
    if error:
        return error
    try:
        return _collect_dashboard(config_key)
    except Exception as e:
        return JSONResponse({"status":"erro","erro": str(e)}, status_code=500)

@app.post("/api/dashboard/log-pesquisas", tags=["Dashboard UI"], summary="Resumo de log de pesquisas")
async def log_pesquisas(request: Request, body: dict):
    user_id, config_key, error = _require_user_config(request, body or {})
    if error:
        return error
    try:
        dash = _collect_dashboard(config_key)
        lp = dash["log_pesquisas"]
        return {"status":"ok","dados":{"total": lp.get("total_registros", 0), "data_inicio": lp.get("data_antiga","N/A"), "data_fim": lp.get("data_recente","N/A")}}
    except Exception as e:
        return JSONResponse({"status":"erro","erro":str(e)}, status_code=500)

@app.post("/api/dashboard/fila-adsvc", tags=["Dashboard UI"], summary="Indicadores de fila ADSVC")
async def fila_adsvc(request: Request, body: dict):
    user_id, config_key, error = _require_user_config(request, body or {})
    if error:
        return error
    try:
        dash = _collect_dashboard(config_key)
        fg = dash["fila_geral"]
        return {"status":"ok","dados":{"pendentes": fg.get("pendente", 0), "processados": fg.get("processados", 0)}}
    except Exception as e:
        return JSONResponse({"status":"erro","erro":str(e)}, status_code=500)

@app.post("/api/dashboard/performance-workers", tags=["Dashboard UI"], summary="Performance dos workers")
async def perf_workers(request: Request, body: dict):
    user_id, config_key, error = _require_user_config(request, body or {})
    if error:
        return error
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

@app.post("/gerar_clientes", tags=["Operações"], summary="Geração simples de clientes")
async def gerar_clientes(request: Request, body: dict):
    user_id, config_key, error = _require_user_config(request, body or {})
    if error:
        return error
    quantidade = body.get("quantidade", 100)
    return {"status": "ok", "mensagem": f"Gerando {quantidade} clientes...", "config_key": config_key}

@app.post("/monitoramento", tags=["Operações"], summary="Status operacional resumido")
async def monitoramento(body: dict):
    return {"status": "ok", "mensagem": "Sistema operacional", "workers_ativos": 4, "registros_processados": 15000}

@app.post("/movimentacoes", tags=["Operações"], summary="Processar movimentações")
async def movimentacoes(request: Request, body: dict):
    user_id, config_key, error = _require_user_config(request, body or {})
    if error:
        return error
    return {"status": "ok", "mensagem": "Movimentações processadas", "total": 250}


@app.post("/gerar_movimentacoes", tags=["Operações"], summary="Gerar movimentações de carga")
async def gerar_movimentacoes(request: Request, body: dict):
    user_id, config_key, error = _require_user_config(request, body or {})
    if error:
        return error

    dados = body or {}
    data_str = dados.get("data_referencia")
    tipo = str(dados.get("tipo", "MOVFIN") or "MOVFIN")
    modo_data = str(dados.get("modo_data", "fixa") or "fixa")
    busca = (dados.get("busca") or "").strip()
    quantidade = int(dados.get("quantidade", 1) or 1)

    try:
        data_ref = datetime.strptime(str(data_str), "%Y-%m-%d").date()
    except Exception:
        data_ref = datetime.now().date()

    def worker(key: str, dt_base, tp_carga: str, modo: str, termo_busca: str, qtd_total: int):
        try:
            with get_db_session(key) as session:
                versao = _detectar_versao_sistema(session)

                sql_clientes = "SELECT CD_CLIENTE, DE_CLIENTE, CD_TP_CLIENTE FROM TAB_CLIENTES_PLD"
                params = {}
                if termo_busca:
                    sql_clientes += " WHERE CD_CLIENTE = :busca OR CIC_CPF = :busca OR DE_CLIENTE LIKE :busca_like"
                    params = {"busca": termo_busca, "busca_like": f"%{termo_busca}%"}

                clientes = session.execute(text(sql_clientes), params).fetchall()
                if not clientes:
                    logger.warning("Nenhum cliente encontrado na TAB_CLIENTES_PLD para carga de movimentações")
                    return

                if tp_carga == "MOVFIN":
                    _movfin_nacional(session, versao, clientes, dt_base, modo, qtd_total)
                elif tp_carga == "MOVFIN_ME":
                    _movfin_moeda_estrangeira(session, versao, clientes, dt_base, modo, qtd_total)
                elif tp_carga == "MOVFIN_INTERMEDIADOR":
                    _movfin_intermediador(session, clientes, dt_base, modo, qtd_total)
                else:
                    logger.warning(f"Tipo de carga não suportado: {tp_carga}")
                    return
        except Exception as exc:
            logger.error(f"Erro crítico em gerar_movimentacoes ({tp_carga}): {exc}")

    threading.Thread(target=worker, args=(config_key, data_ref, tipo, modo_data, busca, quantidade), daemon=True).start()

    return {
        "status": "ok",
        "message": f"Processamento de {tipo} iniciado.",
        "detalhes": "Lote: 50.000 | Usando TAB_CLIENTES_PLD como base."
    }

@app.post("/check_ambiente", tags=["Operações"], summary="Verificar estrutura do ambiente SQL")
async def check_ambiente(request: Request, body: dict):
    user_id, config_key, error = _require_user_config(request, body or {})
    if error:
        return error
    try:
        with get_db_session(config_key) as session:
            versao = _detectar_versao_sistema(session)

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

@app.post("/setup_ambiente", tags=["Operações"], summary="Criar/ajustar estrutura do ambiente SQL")
async def setup_ambiente(request: Request, body: dict):
    user_id, config_key, error = _require_user_config(request, body or {})
    if error:
        return error
    versao_input = str((body or {}).get("versao") or "").strip().upper()
    if versao_input in {"V9", "9", "09", "009"}:
        versao = "V9"
    elif versao_input in {"V8", "8", "08", "008"}:
        versao = "V8"
    else:
        versao = None

    scripts_v8 = {
        "CLIENTES": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_PLD' AND xtype='U')
            CREATE TABLE TAB_CLIENTES_PLD (
                CD_CLIENTE char(20) PRIMARY KEY, DE_CLIENTE varchar(120), CD_TP_CLIENTE char(2), DE_ENDERECO varchar(80),
                DE_CIDADE varchar(40), DE_ESTADO char(2), DE_PAIS varchar(40), CD_CEP varchar(10), DE_ENDERECO_RES varchar(80),
                DE_CIDADE_RES varchar(40), DE_ESTADO_RES char(2), DE_PAIS_RES varchar(40), CD_CEP_RES varchar(10),
                DE_ENDERECO_CML varchar(80), DE_CIDADE_CML varchar(40), DE_ESTADO_CML char(2), DE_PAIS_CML varchar(40),
                CD_CEP_CML varchar(10), DE_FONE1 varchar(14), DE_FONE2 varchar(14), DT_ABERTURA_REL datetime, CIC_CPF varchar(20),
                DS_GRUPO_CLIENTE varchar(50), DT_DESATIVACAO datetime, DT_ULT_ALTERACAO datetime, DS_RAMO_ATV varchar(80),
                FL_FUNDO_INVEST bit, FL_CLI_EVENTUAL bit, DE_RESPONS_CADASTRO varchar(60), DE_CONF_CADASTRO varchar(60),
                CD_RISCO smallint, CD_NAIC varchar(20), DE_LINHA_NEGOCIO varchar(20), FL_CADASTRO_PROC bit,
                FL_NAO_RESIDENTE bit, FL_GRANDES_FORTUNAS bit, DT_CONSTITUICAO datetime, DE_PAIS_SEDE varchar(40),
                DE_SIT_CADASTRO varchar(40), FL_BLOQUEADO bit, CD_RISCO_INERENTE smallint, IP_ELETRONICO varchar(104),
                DE_EMAIL varchar(100), FL_RELACIONAMENTO_TERCEIROS bit, FL_ADMIN_CARTOES bit, FL_EMPRESA_TRUST bit,
                FL_FACILITADORA_PAGTO bit, CD_NAT_JURIDICA varchar(5), FL_EMP_REGULADA bit
            )""",
        "MOVFIN": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_MOVFIN_PLD' AND xtype='U')
            CREATE TABLE TAB_CLIENTES_MOVFIN_PLD (CD_IDENTIFICACAO varchar(40) PRIMARY KEY, CD_VEIC_LEGAL smallint, CD_AGENCIA char(10), CD_AGENCIA_MOVTO char(10), CD_CONTA varchar(50), CD_CLIENTE varchar(20), DT_MOVIMENTA datetime, DTHR_MOVIMENTA datetime, CD_MOEDA varchar(10), VL_OPERACAO money, TP_DEB_CRED char(1), CD_FORMA varchar(20), DE_CONTRAPARTE varchar(120), DE_BANCO_CONTRA varchar(60), DE_AGENCIA_CONTRA varchar(60), CD_CONTA_CONTRA varchar(50), CD_PAIS_CONTRA varchar(40), DE_ORIGEM_OPE varchar(40), CD_PRODUTO varchar(20), DE_FINALIDADE varchar(400), CPF_CNPJ_CONTRA varchar(20), DS_CIDADE_CONTRA varchar(60), DS_COMP_HISTORICO varchar(50), VL_RENDIMENTO money, DT_PREV_LIQUIDACAO datetime, CD_ISPB_EMISSOR int, NR_CHEQUE varchar(20), DE_TP_DOCTO_CONTRA varchar(40), NR_DOCTO_CONTRA varchar(50), DE_EXECUTOR varchar(60), CPF_EXECUTOR varchar(20), NR_PASSAPORTE_EXEC varchar(20), FL_IOF_CARENCIA bit, CD_NAT_OPERACAO varchar(20), DE_ORDENANTE varchar(120), UF_MOVTO char(2), NR_POS varchar(20), DS_CIDADE_POS varchar(60), DS_CANAL varchar(15), DS_ORIGEM_RECURSO varchar(40), DS_DESTINO_RECURSO varchar(40), CD_PROVISIONAMENTO varchar(40), DS_AMBIENTE_NEG varchar(20))""",
        "MOVFIN_ME": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_MOVFIN_ME_PLD' AND xtype='U')
            CREATE TABLE TAB_CLIENTES_MOVFIN_ME_PLD (CD_IDENTIFICACAO varchar(40) PRIMARY KEY, CD_VEIC_LEGAL smallint, CD_AGENCIA char(10), CD_CONTA varchar(50), CD_CLIENTE varchar(20), DT_MOVIMENTA datetime, DTHR_MOVIMENTA datetime, CD_MOEDA_ME varchar(10), VL_OPERACAO_ME money, TX_COTACAO_ME money, VL_OPERACAO_USD money, TP_DEB_CRED char(1), CD_FORMA varchar(20), DE_CONTRAPARTE varchar(120), CD_BIC_BANCO_CONTRA varchar(20), DE_BANCO_CONTRA varchar(60), DE_AGENCIA_CONTRA varchar(60), CD_CONTA_CONTRA varchar(50), CD_PAIS_CONTRA varchar(40), DE_ORIGEM_OPE varchar(40), CD_PRODUTO char(20), DE_FINALIDADE varchar(60), CPF_CNPJ_CONTRA varchar(20), DS_CIDADE_CONTRA varchar(60), DS_COMP_HISTORICO varchar(50), DE_TP_DOCTO_CONTRA varchar(40), NR_DOCTO_CONTRA varchar(50), DE_EXECUTOR varchar(60), CPF_EXECUTOR varchar(20), NR_PASSAPORTE_EXEC varchar(20), CD_NAT_OPERACAO varchar(20), DE_ORDENANTE varchar(120), UF_MOVTO char(2), DE_OPERADOR varchar(60), TX_PTAX float)""",
        "MOVFIN_INT": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD' AND xtype='U')
            CREATE TABLE TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD (CD_IDENTIFICACAO char(40) PRIMARY KEY, CD_CLIENTE varchar(20), DT_MOVIMENTA datetime, NR_ORDEMPAGAMENTO varchar(10), DT_PAGAMENTO datetime, CPF_CNPJ char(20), DE_CLIENTE varchar(120), TP_DOC varchar(20), DE_MOEDA varchar(50), VL_ME money, VL_USD money, VL_CONTABIL_MN money, VL_FECHAMENTOVENDA_MN money, VL_GIRO money, DS_SITUACAO varchar(40), TP_MOVIMENTACAO varchar(40), DE_ORIGINADOR varchar(120), TP_DOCUMENTOORIGINADOR varchar(40), CPF_CNPJ_ORIGINADOR varchar(20), DE_PAISORIGINADOR varchar(50), DE_FAVORECIDO varchar(120), TP_DOCUMENTOFAVORECIDO varchar(40), CPF_CNPJ_FAVORECIDO varchar(20), DE_PAISFAVORECIDO varchar(50), DE_DETALHESPAGAMENTO varchar(1000), TP_CONTACORRENTE varchar(40), DE_ORIGEM smallint)""",
        "CO_TIT": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_CO_TIT_PLD' AND xtype='U')
            CREATE TABLE TAB_CLIENTES_CO_TIT_PLD (CD_CLIENTE CHAR(20) NOT NULL,DE_NOME_CO VARCHAR(120) NOT NULL,DE_END_CO VARCHAR(80) NOT NULL, DE_CID_CO VARCHAR(40) NOT NULL, CD_UF VARCHAR(2) NOT NULL, DE_PAIS_CO VARCHAR(40) NOT NULL, CD_CEP_CO VARCHAR(10) NOT NULL, DE_FONE1_CO VARCHAR(14) NOT NULL, DE_FONE2_CO VARCHAR(14) NOT NULL, RG VARCHAR(15) NOT NULL, RG_EMISSOR VARCHAR(20) NOT NULL, CPF VARCHAR(15) NOT NULL, NM_PAI VARCHAR(60) NOT NULL, NM_MAE VARCHAR(60) NOT NULL, NM_CONJUGE VARCHAR(60) NOT NULL, NACIONALIDADE VARCHAR(20) NOT NULL,    DT_NASCIMENTO DATETIME NOT NULL, SEXO CHAR(1) NOT NULL, DS_PROFISSAO VARCHAR(80) NOT NULL, CD_TP_CLIENTE CHAR(2) NOT NULL, CNPJ VARCHAR(20) NOT NULL, DS_RAMO_ATV VARCHAR(80) NOT NULL, DS_CARGO VARCHAR(80) NOT NULL, FL_EST_CIVIL CHAR(1) NOT NULL, DE_ATV_PRINCIPAL VARCHAR(80) NOT NULL, DE_FORMA_CONSTITUICAO VARCHAR(50) NOT NULL, DT_CONSTITUICAO DATETIME NOT NULL, FL_PEP BIT NOT NULL, FL_CO_TIT_FINAL BIT NOT NULL, TX_PARTICIPACAO FLOAT NOT NULL, DE_PAIS_DOMICILIO VARCHAR(40) NOT NULL, DE_PAIS_NASCIMENTO VARCHAR(40) NOT NULL, DE_NATUREZA VARCHAR(40) NOT NULL, DE_SIT_CADASTRO VARCHAR(40) NOT NULL, DT_INICIO_RELACIONAMENTO DATETIME NOT NULL, DT_FIM_RELACIONAMENTO DATETIME NOT NULL, FL_SERVIDOR_PUBLICO BIT NOT NULL)"""
    }

    scripts_v9 = {
        "CLIENTES": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_PLD' AND xtype='U')
            CREATE TABLE TAB_CLIENTES_PLD (
                CD_CLIENTE char(20) PRIMARY KEY, DE_CLIENTE varchar(120), CD_TP_CLIENTE char(2), DE_ENDERECO varchar(80),
                DE_CIDADE varchar(40), DE_ESTADO char(2), DE_PAIS varchar(40), CD_CEP varchar(10), DE_FONE1 varchar(14),
                DE_FONE2 varchar(14), DT_ABERTURA_REL datetime, CIC_CPF varchar(20), DS_GRUPO_CLIENTE varchar(50),
                DE_ENDERECO_RES varchar(80), DE_CIDADE_RES varchar(40), DE_ESTADO_RES char(2), DE_PAIS_RES varchar(40),
                CD_CEP_RES varchar(10), DE_ENDERECO_CML varchar(80), DE_CIDADE_CML varchar(40), DE_ESTADO_CML char(2),
                DE_PAIS_CML varchar(40), CD_CEP_CML varchar(10), DT_DESATIVACAO datetime, DT_ULT_ALTERACAO datetime,
                DS_RAMO_ATV varchar(80), FL_FUNDO_INVEST bit, FL_CLI_EVENTUAL bit, DE_RESPONS_CADASTRO varchar(60),
                DE_CONF_CADASTRO varchar(60), CD_RISCO smallint, CD_NAIC varchar(20), DE_LINHA_NEGOCIO varchar(20),
                FL_CADASTRO_PROC bit, FL_NAO_RESIDENTE bit, FL_GRANDES_FORTUNAS bit, DE_PAIS_SEDE varchar(40),
                DE_SIT_CADASTRO varchar(40), FL_BLOQUEADO bit, CD_RISCO_INERENTE smallint, DT_CONSTITUICAO datetime,
                IP_ELETRONICO varchar(104), DE_EMAIL varchar(100), FL_RELACIONAMENTO_TERCEIROS bit, FL_ADMIN_CARTOES bit,
                FL_EMPRESA_TRUST bit, FL_FACILITADORA_PAGTO bit, CD_NAT_JURIDICA varchar(5), FL_EMP_REGULADA bit,
                DE_PAIS_DOMICILIO_FISCAL varchar(40), DE_PAIS_CONTROLE_ACIONARIO varchar(40), CD_ORIGEM_RECURSOS smallint,
                ID_TITULARIDADE int, DS_CANAL varchar(25)
            )""",
        "MOVFIN": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_MOVFIN_PLD' AND xtype='U')
            CREATE TABLE TAB_CLIENTES_MOVFIN_PLD (
                CD_IDENTIFICACAO varchar(40) PRIMARY KEY, CD_VEIC_LEGAL smallint, CD_AGENCIA char(10), CD_AGENCIA_MOVTO char(10),
                CD_CONTA varchar(50), CD_CLIENTE varchar(20), DT_MOVIMENTA datetime, DTHR_MOVIMENTA datetime, CD_MOEDA varchar(10),
                VL_OPERACAO money, TP_DEB_CRED char(1), CD_FORMA varchar(20), DE_CONTRAPARTE varchar(120), DE_BANCO_CONTRA varchar(60),
                DE_AGENCIA_CONTRA varchar(60), CD_CONTA_CONTRA varchar(50), CD_PAIS_CONTRA varchar(40), DE_ORIGEM_OPE varchar(40),
                CD_PRODUTO varchar(20), DE_FINALIDADE varchar(400), CPF_CNPJ_CONTRA varchar(20), DS_CIDADE_CONTRA varchar(60),
                DS_COMP_HISTORICO varchar(300), VL_RENDIMENTO money, DT_PREV_LIQUIDACAO datetime, CD_ISPB_EMISSOR int,
                NR_CHEQUE varchar(20), DE_TP_DOCTO_CONTRA varchar(40), NR_DOCTO_CONTRA varchar(50), DE_EXECUTOR varchar(60),
                CPF_EXECUTOR varchar(20), NR_PASSAPORTE_EXEC varchar(20), FL_IOF_CARENCIA bit, CD_NAT_OPERACAO varchar(20),
                DE_ORDENANTE varchar(120), UF_MOVTO char(2), NR_POS varchar(20), DS_CIDADE_POS varchar(60), DS_CANAL varchar(15),
                DS_ORIGEM_RECURSO varchar(40), DS_DESTINO_RECURSO varchar(40), CD_PROVISIONAMENTO varchar(40), DS_AMBIENTE_NEG varchar(20),
                CD_COMPRA varchar(50)
            )""",
        "MOVFIN_ME": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_MOVFIN_ME_PLD' AND xtype='U')
            CREATE TABLE TAB_CLIENTES_MOVFIN_ME_PLD (CD_IDENTIFICACAO varchar(40) PRIMARY KEY, CD_VEIC_LEGAL smallint, CD_AGENCIA char(10), CD_CONTA varchar(50), CD_CLIENTE varchar(20), DT_MOVIMENTA datetime, DTHR_MOVIMENTA datetime, CD_MOEDA_ME varchar(10), VL_OPERACAO_ME money, TX_COTACAO_ME money, VL_OPERACAO_USD money, TP_DEB_CRED char(1), CD_FORMA varchar(20), DE_CONTRAPARTE varchar(120), CD_BIC_BANCO_CONTRA varchar(20), DE_BANCO_CONTRA varchar(60), DE_AGENCIA_CONTRA varchar(60), CD_CONTA_CONTRA varchar(50), CD_PAIS_CONTRA varchar(40), DE_ORIGEM_OPE varchar(40), CD_PRODUTO char(20), DE_FINALIDADE varchar(60), CPF_CNPJ_CONTRA varchar(20), DS_CIDADE_CONTRA varchar(60), DS_COMP_HISTORICO varchar(50), DE_TP_DOCTO_CONTRA varchar(40), NR_DOCTO_CONTRA varchar(50), DE_EXECUTOR varchar(60), CPF_EXECUTOR varchar(20), NR_PASSAPORTE_EXEC varchar(20), CD_NAT_OPERACAO varchar(20), DE_ORDENANTE varchar(120), UF_MOVTO char(2), DE_OPERADOR varchar(60), TX_PTAX float)""",
        "MOVFIN_INT": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD' AND xtype='U')
            CREATE TABLE TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD (CD_IDENTIFICACAO char(40) PRIMARY KEY, CD_CLIENTE varchar(20), DT_MOVIMENTA datetime, NR_ORDEMPAGAMENTO varchar(10), DT_PAGAMENTO datetime, CPF_CNPJ char(20), DE_CLIENTE varchar(120), TP_DOC varchar(20), DE_MOEDA varchar(50), VL_ME money, VL_USD money, VL_CONTABIL_MN money, VL_FECHAMENTOVENDA_MN money, VL_GIRO money, DS_SITUACAO varchar(40), TP_MOVIMENTACAO varchar(40), DE_ORIGINADOR varchar(120), TP_DOCUMENTOORIGINADOR varchar(40), CPF_CNPJ_ORIGINADOR varchar(20), DE_PAISORIGINADOR varchar(50), DE_FAVORECIDO varchar(120), TP_DOCUMENTOFAVORECIDO varchar(40), CPF_CNPJ_FAVORECIDO varchar(20), DE_PAISFAVORECIDO varchar(50), DE_DETALHESPAGAMENTO varchar(1000), TP_CONTACORRENTE varchar(40), DE_ORIGEM smallint)""",
        "CO_TIT": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_CO_TIT_PLD' AND xtype='U')
            CREATE TABLE TAB_CLIENTES_CO_TIT_PLD (CD_CLIENTE CHAR(20) NOT NULL,DE_NOME_CO VARCHAR(120) NOT NULL,DE_END_CO VARCHAR(80) NOT NULL, DE_CID_CO VARCHAR(40) NOT NULL, CD_UF VARCHAR(2) NOT NULL, DE_PAIS_CO VARCHAR(40) NOT NULL, CD_CEP_CO VARCHAR(10) NOT NULL, DE_FONE1_CO VARCHAR(14) NOT NULL, DE_FONE2_CO VARCHAR(14) NOT NULL, RG VARCHAR(15) NOT NULL, RG_EMISSOR VARCHAR(20) NOT NULL, CPF VARCHAR(15) NOT NULL, NM_PAI VARCHAR(60) NOT NULL, NM_MAE VARCHAR(60) NOT NULL, NM_CONJUGE VARCHAR(60) NOT NULL, NACIONALIDADE VARCHAR(20) NOT NULL,    DT_NASCIMENTO DATETIME NOT NULL, SEXO CHAR(1) NOT NULL, DS_PROFISSAO VARCHAR(80) NOT NULL, CD_TP_CLIENTE CHAR(2) NOT NULL, CNPJ VARCHAR(20) NOT NULL, DS_RAMO_ATV VARCHAR(80) NOT NULL, DS_CARGO VARCHAR(80) NOT NULL, FL_EST_CIVIL CHAR(1) NOT NULL, DE_ATV_PRINCIPAL VARCHAR(80) NOT NULL, DE_FORMA_CONSTITUICAO VARCHAR(50) NOT NULL, DT_CONSTITUICAO DATETIME NOT NULL, FL_PEP BIT NOT NULL, FL_CO_TIT_FINAL BIT NOT NULL, TX_PARTICIPACAO FLOAT NOT NULL, DE_PAIS_DOMICILIO VARCHAR(40) NOT NULL, DE_PAIS_NASCIMENTO VARCHAR(40) NOT NULL, DE_NATUREZA VARCHAR(40) NOT NULL, DE_SIT_CADASTRO VARCHAR(40) NOT NULL, DT_INICIO_RELACIONAMENTO DATETIME NOT NULL, DT_FIM_RELACIONAMENTO DATETIME NOT NULL, FL_SERVIDOR_PUBLICO BIT NOT NULL,DE_PAIS_DOMICILIO_FISCAL VARCHAR(40) NOT NULL, DE_PAIS_CONTROLE_ACIONARIO VARCHAR(40) NOT NULL, DE_PAIS_SEDE VARCHAR(40) NOT NULL,CD_RISCO SMALLINT NOT NULL)"""
    }

    schema_v8 = {
        "TAB_CLIENTES_PLD": [
            ("CD_CLIENTE", "char(20)"), ("DE_CLIENTE", "varchar(120)"), ("CD_TP_CLIENTE", "char(2)"), ("DE_ENDERECO", "varchar(80)"),
            ("DE_CIDADE", "varchar(40)"), ("DE_ESTADO", "char(2)"), ("DE_PAIS", "varchar(40)"), ("CD_CEP", "varchar(10)"),
            ("DE_ENDERECO_RES", "varchar(80)"), ("DE_CIDADE_RES", "varchar(40)"), ("DE_ESTADO_RES", "char(2)"), ("DE_PAIS_RES", "varchar(40)"),
            ("CD_CEP_RES", "varchar(10)"), ("DE_ENDERECO_CML", "varchar(80)"), ("DE_CIDADE_CML", "varchar(40)"), ("DE_ESTADO_CML", "char(2)"),
            ("DE_PAIS_CML", "varchar(40)"), ("CD_CEP_CML", "varchar(10)"), ("DE_FONE1", "varchar(14)"), ("DE_FONE2", "varchar(14)"),
            ("DT_ABERTURA_REL", "datetime"), ("CIC_CPF", "varchar(20)"), ("DS_GRUPO_CLIENTE", "varchar(50)"), ("DT_DESATIVACAO", "datetime"),
            ("DT_ULT_ALTERACAO", "datetime"), ("DS_RAMO_ATV", "varchar(80)"), ("FL_FUNDO_INVEST", "bit"), ("FL_CLI_EVENTUAL", "bit"),
            ("DE_RESPONS_CADASTRO", "varchar(60)"), ("DE_CONF_CADASTRO", "varchar(60)"), ("CD_RISCO", "smallint"), ("CD_NAIC", "varchar(20)"),
            ("DE_LINHA_NEGOCIO", "varchar(20)"), ("FL_CADASTRO_PROC", "bit"), ("FL_NAO_RESIDENTE", "bit"), ("FL_GRANDES_FORTUNAS", "bit"),
            ("DT_CONSTITUICAO", "datetime"), ("DE_PAIS_SEDE", "varchar(40)"), ("DE_SIT_CADASTRO", "varchar(40)"), ("FL_BLOQUEADO", "bit"),
            ("CD_RISCO_INERENTE", "smallint"), ("IP_ELETRONICO", "varchar(104)"), ("DE_EMAIL", "varchar(100)"), ("FL_RELACIONAMENTO_TERCEIROS", "bit"),
            ("FL_ADMIN_CARTOES", "bit"), ("FL_EMPRESA_TRUST", "bit"), ("FL_FACILITADORA_PAGTO", "bit"), ("CD_NAT_JURIDICA", "varchar(5)"),
            ("FL_EMP_REGULADA", "bit")
        ],
        "TAB_CLIENTES_MOVFIN_PLD": [
            ("CD_IDENTIFICACAO", "varchar(40)"), ("CD_VEIC_LEGAL", "smallint"), ("CD_AGENCIA", "char(10)"), ("CD_AGENCIA_MOVTO", "char(10)"),
            ("CD_CONTA", "varchar(50)"), ("CD_CLIENTE", "varchar(20)"), ("DT_MOVIMENTA", "datetime"), ("DTHR_MOVIMENTA", "datetime"),
            ("CD_MOEDA", "varchar(10)"), ("VL_OPERACAO", "money"), ("TP_DEB_CRED", "char(1)"), ("CD_FORMA", "varchar(20)"),
            ("DE_CONTRAPARTE", "varchar(120)"), ("DE_BANCO_CONTRA", "varchar(60)"), ("DE_AGENCIA_CONTRA", "varchar(60)"), ("CD_CONTA_CONTRA", "varchar(50)"),
            ("CD_PAIS_CONTRA", "varchar(40)"), ("DE_ORIGEM_OPE", "varchar(40)"), ("CD_PRODUTO", "varchar(20)"), ("DE_FINALIDADE", "varchar(400)"),
            ("CPF_CNPJ_CONTRA", "varchar(20)"), ("DS_CIDADE_CONTRA", "varchar(60)"), ("DS_COMP_HISTORICO", "varchar(50)"), ("VL_RENDIMENTO", "money"),
            ("DT_PREV_LIQUIDACAO", "datetime"), ("CD_ISPB_EMISSOR", "int"), ("NR_CHEQUE", "varchar(20)"), ("DE_TP_DOCTO_CONTRA", "varchar(40)"),
            ("NR_DOCTO_CONTRA", "varchar(50)"), ("DE_EXECUTOR", "varchar(60)"), ("CPF_EXECUTOR", "varchar(20)"), ("NR_PASSAPORTE_EXEC", "varchar(20)"),
            ("FL_IOF_CARENCIA", "bit"), ("CD_NAT_OPERACAO", "varchar(20)"), ("DE_ORDENANTE", "varchar(120)"), ("UF_MOVTO", "char(2)"),
            ("NR_POS", "varchar(20)"), ("DS_CIDADE_POS", "varchar(60)"), ("DS_CANAL", "varchar(15)"), ("DS_ORIGEM_RECURSO", "varchar(40)"),
            ("DS_DESTINO_RECURSO", "varchar(40)"), ("CD_PROVISIONAMENTO", "varchar(40)"), ("DS_AMBIENTE_NEG", "varchar(20)")
        ],
        "TAB_CLIENTES_MOVFIN_ME_PLD": [
            ("CD_IDENTIFICACAO", "varchar(40)"), ("CD_VEIC_LEGAL", "smallint"), ("CD_AGENCIA", "char(10)"), ("CD_CONTA", "varchar(50)"),
            ("CD_CLIENTE", "varchar(20)"), ("DT_MOVIMENTA", "datetime"), ("DTHR_MOVIMENTA", "datetime"), ("CD_MOEDA_ME", "varchar(10)"),
            ("VL_OPERACAO_ME", "money"), ("TX_COTACAO_ME", "money"), ("VL_OPERACAO_USD", "money"), ("TP_DEB_CRED", "char(1)"),
            ("CD_FORMA", "varchar(20)"), ("DE_CONTRAPARTE", "varchar(120)"), ("CD_BIC_BANCO_CONTRA", "varchar(20)"), ("DE_BANCO_CONTRA", "varchar(60)"),
            ("DE_AGENCIA_CONTRA", "varchar(60)"), ("CD_CONTA_CONTRA", "varchar(50)"), ("CD_PAIS_CONTRA", "varchar(40)"), ("DE_ORIGEM_OPE", "varchar(40)"),
            ("CD_PRODUTO", "char(20)"), ("DE_FINALIDADE", "varchar(60)"), ("CPF_CNPJ_CONTRA", "varchar(20)"), ("DS_CIDADE_CONTRA", "varchar(60)"),
            ("DS_COMP_HISTORICO", "varchar(50)"), ("DE_TP_DOCTO_CONTRA", "varchar(40)"), ("NR_DOCTO_CONTRA", "varchar(50)"), ("DE_EXECUTOR", "varchar(60)"),
            ("CPF_EXECUTOR", "varchar(20)"), ("NR_PASSAPORTE_EXEC", "varchar(20)"), ("CD_NAT_OPERACAO", "varchar(20)"), ("DE_ORDENANTE", "varchar(120)"),
            ("UF_MOVTO", "char(2)"), ("DE_OPERADOR", "varchar(60)"), ("TX_PTAX", "float")
        ],
        "TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD": [
            ("CD_IDENTIFICACAO", "char(40)"), ("CD_CLIENTE", "varchar(20)"), ("DT_MOVIMENTA", "datetime"), ("NR_ORDEMPAGAMENTO", "varchar(10)"),
            ("DT_PAGAMENTO", "datetime"), ("CPF_CNPJ", "char(20)"), ("DE_CLIENTE", "varchar(120)"), ("TP_DOC", "varchar(20)"),
            ("DE_MOEDA", "varchar(50)"), ("VL_ME", "money"), ("VL_USD", "money"), ("VL_CONTABIL_MN", "money"),
            ("VL_FECHAMENTOVENDA_MN", "money"), ("VL_GIRO", "money"), ("DS_SITUACAO", "varchar(40)"), ("TP_MOVIMENTACAO", "varchar(40)"),
            ("DE_ORIGINADOR", "varchar(120)"), ("TP_DOCUMENTOORIGINADOR", "varchar(40)"), ("CPF_CNPJ_ORIGINADOR", "varchar(20)"), ("DE_PAISORIGINADOR", "varchar(50)"),
            ("DE_FAVORECIDO", "varchar(120)"), ("TP_DOCUMENTOFAVORECIDO", "varchar(40)"), ("CPF_CNPJ_FAVORECIDO", "varchar(20)"), ("DE_PAISFAVORECIDO", "varchar(50)"),
            ("DE_DETALHESPAGAMENTO", "varchar(1000)"), ("TP_CONTACORRENTE", "varchar(40)"), ("DE_ORIGEM", "smallint")
        ],
        "TAB_CLIENTES_CO_TIT_PLD": [
            ("CD_CLIENTE", "char(20)"), ("DE_NOME_CO", "varchar(120)"), ("DE_END_CO", "varchar(80)"), ("DE_CID_CO", "varchar(40)"),
            ("CD_UF", "varchar(2)"), ("DE_PAIS_CO", "varchar(40)"), ("CD_CEP_CO", "varchar(10)"), ("DE_FONE1_CO", "varchar(14)"),
            ("DE_FONE2_CO", "varchar(14)"), ("RG", "varchar(15)"), ("RG_EMISSOR", "varchar(20)"), ("CPF", "varchar(15)"),
            ("NM_PAI", "varchar(60)"), ("NM_MAE", "varchar(60)"), ("NM_CONJUGE", "varchar(60)"), ("NACIONALIDADE", "varchar(20)"),
            ("DT_NASCIMENTO", "datetime"), ("SEXO", "char(1)"), ("DS_PROFISSAO", "varchar(80)"), ("CD_TP_CLIENTE", "char(2)"),
            ("CNPJ", "varchar(20)"), ("DS_RAMO_ATV", "varchar(80)"), ("DS_CARGO", "varchar(80)"), ("FL_EST_CIVIL", "char(1)"),
            ("DE_ATV_PRINCIPAL", "varchar(80)"), ("DE_FORMA_CONSTITUICAO", "varchar(50)"), ("DT_CONSTITUICAO", "datetime"), ("FL_PEP", "bit"),
            ("FL_CO_TIT_FINAL", "bit"), ("TX_PARTICIPACAO", "float"), ("DE_PAIS_DOMICILIO", "varchar(40)"), ("DE_PAIS_NASCIMENTO", "varchar(40)"),
            ("DE_NATUREZA", "varchar(40)"), ("DE_SIT_CADASTRO", "varchar(40)"), ("DT_INICIO_RELACIONAMENTO", "datetime"), ("DT_FIM_RELACIONAMENTO", "datetime"),
            ("FL_SERVIDOR_PUBLICO", "bit")
        ]
    }

    schema_v9 = {
        **schema_v8,
        "TAB_CLIENTES_PLD": schema_v8["TAB_CLIENTES_PLD"] + [
            ("DE_PAIS_DOMICILIO_FISCAL", "varchar(40)"), ("DE_PAIS_CONTROLE_ACIONARIO", "varchar(40)"),
            ("CD_ORIGEM_RECURSOS", "smallint"), ("ID_TITULARIDADE", "int"), ("DS_CANAL", "varchar(25)")
        ],
        "TAB_CLIENTES_MOVFIN_PLD": [
            ("CD_IDENTIFICACAO", "varchar(40)"), ("CD_VEIC_LEGAL", "smallint"), ("CD_AGENCIA", "char(10)"), ("CD_AGENCIA_MOVTO", "char(10)"),
            ("CD_CONTA", "varchar(50)"), ("CD_CLIENTE", "varchar(20)"), ("DT_MOVIMENTA", "datetime"), ("DTHR_MOVIMENTA", "datetime"),
            ("CD_MOEDA", "varchar(10)"), ("VL_OPERACAO", "money"), ("TP_DEB_CRED", "char(1)"), ("CD_FORMA", "varchar(20)"),
            ("DE_CONTRAPARTE", "varchar(120)"), ("DE_BANCO_CONTRA", "varchar(60)"), ("DE_AGENCIA_CONTRA", "varchar(60)"), ("CD_CONTA_CONTRA", "varchar(50)"),
            ("CD_PAIS_CONTRA", "varchar(40)"), ("DE_ORIGEM_OPE", "varchar(40)"), ("CD_PRODUTO", "varchar(20)"), ("DE_FINALIDADE", "varchar(400)"),
            ("CPF_CNPJ_CONTRA", "varchar(20)"), ("DS_CIDADE_CONTRA", "varchar(60)"), ("DS_COMP_HISTORICO", "varchar(300)"), ("VL_RENDIMENTO", "money"),
            ("DT_PREV_LIQUIDACAO", "datetime"), ("CD_ISPB_EMISSOR", "int"), ("NR_CHEQUE", "varchar(20)"), ("DE_TP_DOCTO_CONTRA", "varchar(40)"),
            ("NR_DOCTO_CONTRA", "varchar(50)"), ("DE_EXECUTOR", "varchar(60)"), ("CPF_EXECUTOR", "varchar(20)"), ("NR_PASSAPORTE_EXEC", "varchar(20)"),
            ("FL_IOF_CARENCIA", "bit"), ("CD_NAT_OPERACAO", "varchar(20)"), ("DE_ORDENANTE", "varchar(120)"), ("UF_MOVTO", "char(2)"),
            ("NR_POS", "varchar(20)"), ("DS_CIDADE_POS", "varchar(60)"), ("DS_CANAL", "varchar(15)"), ("DS_ORIGEM_RECURSO", "varchar(40)"),
            ("DS_DESTINO_RECURSO", "varchar(40)"), ("CD_PROVISIONAMENTO", "varchar(40)"), ("DS_AMBIENTE_NEG", "varchar(20)"), ("CD_COMPRA", "varchar(50)")
        ],
        "TAB_CLIENTES_CO_TIT_PLD": schema_v8["TAB_CLIENTES_CO_TIT_PLD"] + [
            ("DE_PAIS_DOMICILIO_FISCAL", "varchar(40)"), ("DE_PAIS_CONTROLE_ACIONARIO", "varchar(40)"),
            ("DE_PAIS_SEDE", "varchar(40)"), ("CD_RISCO", "smallint")
        ]
    }

    def _split_column_defs(def_block: str) -> list[str]:
        parts = []
        current = []
        depth = 0
        for ch in def_block:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth = max(0, depth - 1)

            if ch == "," and depth == 0:
                segment = "".join(current).strip()
                if segment:
                    parts.append(segment)
                current = []
            else:
                current.append(ch)

        tail = "".join(current).strip()
        if tail:
            parts.append(tail)
        return parts

    def _extract_columns_from_create_sql(create_sql: str) -> tuple[str | None, list[tuple[str, str]]]:
        sql_text = (create_sql or "").strip()
        upper = sql_text.upper()
        create_pos = upper.find("CREATE TABLE")
        if create_pos < 0:
            return None, []

        open_paren = sql_text.find("(", create_pos)
        close_paren = sql_text.rfind(")")
        if open_paren < 0 or close_paren <= open_paren:
            return None, []

        table_expr = sql_text[create_pos + len("CREATE TABLE"):open_paren].strip()
        table_name = table_expr.split()[-1].replace("[", "").replace("]", "") if table_expr else None
        block = sql_text[open_paren + 1:close_paren]

        columns: list[tuple[str, str]] = []
        for raw in _split_column_defs(block):
            line = raw.split("--", 1)[0].strip()
            if not line:
                continue

            tokens = line.split()
            if len(tokens) < 2:
                continue

            keyword = tokens[0].upper()
            if keyword in {"PRIMARY", "CONSTRAINT", "FOREIGN", "UNIQUE", "CHECK"}:
                continue

            col_name = tokens[0].replace("[", "").replace("]", "")
            col_type = tokens[1]
            columns.append((col_name, col_type))

        return table_name, columns

    try:
        with get_db_session(config_key) as session:
            if not versao:
                versao = _detectar_versao_sistema(session)

            selected_scripts = scripts_v9 if str(versao).upper() == "V9" else scripts_v8
            colunas_adicionadas = {}
            schema_dos_scripts = {}

            for _, sql in selected_scripts.items():
                session.execute(text(sql))
                tabela_script, colunas_script = _extract_columns_from_create_sql(sql)
                if tabela_script and colunas_script:
                    schema_dos_scripts[tabela_script] = colunas_script

            for tabela, definicoes in schema_dos_scripts.items():
                rows = session.execute(text(f"""
                    SELECT COLUMN_NAME
                    FROM INFORMATION_SCHEMA.COLUMNS WITH (NOLOCK)
                    WHERE TABLE_NAME = '{tabela}'
                """)).fetchall()
                existentes = {str(row[0]).upper() for row in rows}

                adicionadas_tabela = []
                for coluna, tipo_sql in definicoes:
                    if coluna.upper() in existentes:
                        continue
                    session.execute(text(f"ALTER TABLE {tabela} ADD {coluna} {tipo_sql} NULL"))
                    adicionadas_tabela.append(coluna)

                if adicionadas_tabela:
                    colunas_adicionadas[tabela] = adicionadas_tabela

        return {
            "status": "ok",
            "message": f"Estrutura {versao} configurada com nomes padronizados!",
            "migracao_segura": {
                "colunas_adicionadas": colunas_adicionadas,
                "total_tabelas_ajustadas": len(colunas_adicionadas)
            }
        }
    except Exception as e:
        return JSONResponse({"status":"erro","erro":str(e)}, status_code=500)


@app.post("/executar_carga_cotit", tags=["Operações"], summary="Executar carga de dependentes (CO_TIT)")
async def executar_carga_cotit(request: Request, body: dict):
    user_id, config_key, error = _require_user_config(request, body or {})
    if error:
        return error

    versao_sistema = str((body or {}).get("versao") or "").upper()

    def worker_carga(key: str, versao_hint: str):
        try:
            with get_db_session(key) as session:
                versao = versao_hint if versao_hint in {"V8", "V9"} else _detectar_versao_sistema(session)

                session.execute(text("DELETE FROM TAB_CLIENTES_CO_TIT_PLD"))

                clientes = session.execute(text("SELECT CD_CLIENTE, DE_CLIENTE, CD_TP_CLIENTE FROM TAB_CLIENTES_PLD WITH (NOLOCK)")).fetchall()
                hoje = datetime.now()

                colunas = [
                    "CD_CLIENTE", "DE_NOME_CO", "DE_END_CO", "DE_CID_CO", "CD_UF", "DE_PAIS_CO",
                    "CD_CEP_CO", "DE_FONE1_CO", "DE_FONE2_CO", "RG", "RG_EMISSOR", "CPF",
                    "NM_PAI", "NM_MAE", "NM_CONJUGE", "NACIONALIDADE", "DT_NASCIMENTO", "SEXO",
                    "DS_PROFISSAO", "CD_TP_CLIENTE", "CNPJ", "DS_RAMO_ATV", "DS_CARGO", "FL_EST_CIVIL",
                    "DE_ATV_PRINCIPAL", "DE_FORMA_CONSTITUICAO", "DT_CONSTITUICAO", "FL_PEP",
                    "FL_CO_TIT_FINAL", "TX_PARTICIPACAO", "DE_PAIS_DOMICILIO", "DE_PAIS_NASCIMENTO",
                    "DE_NATUREZA", "DE_SIT_CADASTRO", "DT_INICIO_RELACIONAMENTO", "DT_FIM_RELACIONAMENTO",
                    "FL_SERVIDOR_PUBLICO"
                ]

                if versao == "V9":
                    colunas.extend(["DE_PAIS_DOMICILIO_FISCAL", "DE_PAIS_CONTROLE_ACIONARIO", "DE_PAIS_SEDE", "CD_RISCO"])

                existentes_rows = session.execute(text("""
                    SELECT COLUMN_NAME
                    FROM INFORMATION_SCHEMA.COLUMNS WITH (NOLOCK)
                    WHERE TABLE_NAME = 'TAB_CLIENTES_CO_TIT_PLD'
                """)).fetchall()
                existentes = {str(row[0]).upper() for row in existentes_rows}
                colunas_final = [col for col in colunas if col.upper() in existentes]

                params = ", ".join([f":{col}" for col in colunas_final])
                sql_insert = text(f"INSERT INTO TAB_CLIENTES_CO_TIT_PLD ({', '.join(colunas_final)}) VALUES ({params})")

                lote = []
                for cli in clientes:
                    cd_titular_original = str(cli[0] or "").strip()
                    nome_titular_original = str(cli[1] or "")
                    tp_cliente = str(cli[2] or "").strip()

                    iteracoes = 1 if tp_cliente == "01" else 3

                    for _ in range(iteracoes):
                        is_real_titular = tp_cliente == "01"

                        sexo = random.choice(["M", "F"])
                        cpf_final = re.sub(r"\D", "", cd_titular_original)[:11] if is_real_titular else _gerar_cpf_fake()
                        nome_final = _clean_name_no_digits(nome_titular_original if is_real_titular else _fake_pf_name())
                        if not nome_final:
                            nome_final = _fake_pf_name()

                        registro = {
                            "CD_CLIENTE": cd_titular_original,
                            "DE_NOME_CO": nome_final[:120],
                            "DE_END_CO": fake.street_name().upper()[:80],
                            "DE_CID_CO": fake.city().upper()[:40],
                            "CD_UF": fake.state_abbr().upper(),
                            "DE_PAIS_CO": "BRASIL",
                            "CD_CEP_CO": re.sub(r"\D", "", fake.postcode())[:8],
                            "DE_FONE1_CO": re.sub(r"\D", "", fake.msisdn())[:14],
                            "DE_FONE2_CO": re.sub(r"\D", "", fake.msisdn())[:14],
                            "RG": _gerar_rg_fake(),
                            "RG_EMISSOR": "SSP",
                            "CPF": cpf_final,
                            "NM_PAI": _fake_pf_name()[:60],
                            "NM_MAE": _fake_pf_name()[:60],
                            "NM_CONJUGE": (_fake_pf_name()[:60] if random.random() > 0.5 else ""),
                            "NACIONALIDADE": "BRASILEIRA",
                            "DT_NASCIMENTO": hoje - timedelta(days=random.randint(7000, 20000)),
                            "SEXO": sexo,
                            "DS_PROFISSAO": "EMPRESARIO" if tp_cliente == "02" else "ANALISTA",
                            "CD_TP_CLIENTE": "01",
                            "CNPJ": "",
                            "DS_RAMO_ATV": "OUTROS",
                            "DS_CARGO": "SOCIO" if tp_cliente == "02" else "TITULAR",
                            "FL_EST_CIVIL": random.choice(["S", "C", "D"]),
                            "DE_ATV_PRINCIPAL": "ATIVIDADE PRINCIPAL",
                            "DE_FORMA_CONSTITUICAO": "OUTROS",
                            "DT_CONSTITUICAO": hoje - timedelta(days=3650),
                            "FL_PEP": 0,
                            "FL_CO_TIT_FINAL": 1 if is_real_titular else 0,
                            "TX_PARTICIPACAO": 100.0 if is_real_titular else 0.0,
                            "DE_PAIS_DOMICILIO": "BRASIL",
                            "DE_PAIS_NASCIMENTO": "BRASIL",
                            "DE_NATUREZA": "PESSOA FISICA",
                            "DE_SIT_CADASTRO": "ATIVO",
                            "DT_INICIO_RELACIONAMENTO": hoje - timedelta(days=180),
                            "DT_FIM_RELACIONAMENTO": hoje + timedelta(days=365),
                            "FL_SERVIDOR_PUBLICO": 0,
                            "DE_PAIS_DOMICILIO_FISCAL": "BRASIL",
                            "DE_PAIS_CONTROLE_ACIONARIO": "BRASIL",
                            "DE_PAIS_SEDE": "BRASIL",
                            "CD_RISCO": 1,
                        }

                        lote.append({col: registro.get(col) for col in colunas_final})

                        if len(lote) >= 1000:
                            session.execute(sql_insert, lote)
                            lote = []

                if lote:
                    session.execute(sql_insert, lote)
        except Exception as exc:
            logger.error(f"Erro crítico carga CO_TIT: {exc}")

    threading.Thread(target=worker_carga, args=(config_key, versao_sistema), daemon=True).start()
    return {"status": "ok", "message": "Carga CO_TIT iniciada com sucesso.", "mensagem": "Carga CO_TIT iniciada com sucesso."}

@app.post("/grpc/gerar_clientes", tags=["gRPC Jobs"], summary="Disparar job de geração de clientes")
async def grpc_gerar_clientes_endpoint(request: Request, body: dict):
    user_id, config_key, error = _require_user_config(request, body or {})
    if error:
        return error

    config = db_manager.get_config(config_key)
    if not config:
        return JSONResponse({"status":"erro","message":"config nao encontrada"}, status_code=400)

    quantidade = int(body.get("quantidade", 0))
    qtd_pf = int(body.get("qtd_pf", 0) or 0)
    qtd_pj = int(body.get("qtd_pj", 0) or 0)
    versao = str(body.get("versao", "") or "")
    customizacao = body.get("customizacao") or {}

    try:
        resp = grpc_gerar_clientes(
            config,
            config_key,
            quantidade,
            qtd_pf,
            qtd_pj,
            versao=versao,
            customizacao=customizacao
        )
        return {
            "status": resp.status,
            "job_id": resp.job_id,
            "message": resp.message,
            "inserted": getattr(resp, "inserted", 0)
        }
    except Exception as e:
        return JSONResponse({"status":"erro","erro": str(e)}, status_code=500)

@app.get("/grpc/job_status/{job_id}", tags=["gRPC Jobs"], summary="Status atual de um job")
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

@app.get("/grpc/job_status/stream/{job_id}", tags=["gRPC Jobs"], summary="Status de job por stream (SSE)")
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
