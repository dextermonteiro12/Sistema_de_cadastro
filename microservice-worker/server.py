import grpc
from concurrent import futures
import time
import uuid
import random
import threading
import pyodbc
import json
import math
import re
import string
from datetime import datetime, timedelta

import gerador_pb2
import gerador_pb2_grpc

JOBS = {}
JOBS_LOCK = threading.Lock()

PF_NOMES = ["ALICE", "BRUNO", "CARLA", "DANIEL", "ELISA", "FELIPE", "GABRIELA", "HENRIQUE", "ISABELA", "JOAO", "LARISSA", "MARCOS"]
PF_SOBRENOMES = ["SILVA", "SOUZA", "OLIVEIRA", "PEREIRA", "COSTA", "ALMEIDA", "ROCHA", "GOMES", "MARTINS", "ARAUJO"]
PJ_RADICAIS = ["ALFA", "NOVA", "PRIME", "VETOR", "ORION", "AURORA", "VERTICE", "ATLANTIS", "INTEGRA", "SIGMA"]
PJ_COMPLEMENTOS = ["CONSULTORIA", "TECNOLOGIA", "SERVICOS", "COMERCIO", "INDUSTRIA", "SOLUCOES", "LOGISTICA", "PARTICIPACOES"]
PJ_SUFIXOS = ["LTDA", "S/A", "EIRELI"]


def _rand_digits(size: int) -> str:
    return ''.join(random.choices(string.digits, k=size))


def _digits_only(value: str) -> str:
    return re.sub(r"\D", "", str(value or ""))


def _clean_name_no_digits(value: str) -> str:
    base = re.sub(r"\d", "", str(value or "").upper())
    base = re.sub(r"\s+", " ", base).strip()
    return base


def _fake_pf_name() -> str:
    return f"{random.choice(PF_NOMES)} {random.choice(PF_SOBRENOMES)}"


def _fake_pj_name() -> str:
    return f"{random.choice(PJ_RADICAIS)} {random.choice(PJ_COMPLEMENTOS)} {random.choice(PJ_SUFIXOS)}"


def _to_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return int(default)


def _to_datetime(value, fallback: datetime):
    if isinstance(value, datetime):
        return value
    if not value:
        return fallback
    try:
        return datetime.fromisoformat(str(value).replace("Z", ""))
    except Exception:
        return fallback


def _to_bool_int(value, default=0):
    if value is None:
        return int(default)
    if isinstance(value, bool):
        return 1 if value else 0
    try:
        return 1 if int(value) != 0 else 0
    except Exception:
        return int(default)


def _infer_layout_version(explicit_version: str, available_columns: set[str]) -> str:
    if explicit_version and explicit_version.upper() in {"V8", "V9"}:
        return explicit_version.upper()
    v9_markers = {
        "DE_PAIS_DOMICILIO_FISCAL",
        "DE_PAIS_CONTROLE_ACIONARIO",
        "CD_ORIGEM_RECURSOS",
        "ID_TITULARIDADE",
        "DS_CANAL"
    }
    return "V9" if len(v9_markers.intersection(available_columns)) >= 3 else "V8"


def _fetch_tab_clientes_columns(cursor) -> set[str]:
    rows = cursor.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS WITH (NOLOCK)
        WHERE TABLE_NAME = 'TAB_CLIENTES_PLD'
    """).fetchall()
    return {str(row[0]).upper() for row in rows}


def _build_cliente_record(tp_cli: str, custom: dict, versao: str) -> dict:
    eh_pf = tp_cli == "01"
    hoje = datetime.now()
    data_padrao = datetime(1900, 1, 1)

    doc_random = _rand_digits(11 if eh_pf else 14)
    doc_custom = _digits_only(custom.get("CIC_CPF"))
    documento = doc_custom if doc_custom else doc_random
    nome_custom = (custom.get("DE_CLIENTE") or "").strip()
    if nome_custom:
        nome = nome_custom
    else:
        nome = _fake_pf_name() if eh_pf else _fake_pj_name()

    nome = _clean_name_no_digits(nome)
    if not nome:
        nome = _fake_pf_name() if eh_pf else _fake_pj_name()

    ds_ramo = custom.get("DS_RAMO_ATV") or ("PESSOA FISICA" if eh_pf else random.choice(["ARQUITETURA", "ENGENHARIA", "TI", "VAREJO", "INDUSTRIA", "CONSULTORIA"]))
    dt_constituicao = _to_datetime(custom.get("DT_CONSTITUICAO"), hoje - timedelta(days=random.randint(365, 3650)))
    dt_desativacao = _to_datetime(custom.get("DT_DESATIVACAO"), data_padrao)
    nat_juridica = (custom.get("CD_NAT_JURIDICA") or ("0000" if eh_pf else random.choice(["2062", "2135", "3999"])))

    record = {
        "CD_CLIENTE": uuid.uuid4().hex[:20].upper(),
        "DE_CLIENTE": nome[:120],
        "CD_TP_CLIENTE": tp_cli,
        "DE_ENDERECO": f"RUA {random.randint(1, 9999)} TESTE"[:80],
        "DE_CIDADE": "SAO PAULO",
        "DE_ESTADO": "SP",
        "DE_PAIS": "BRASIL",
        "CD_CEP": _rand_digits(8),
        "DE_FONE1": _rand_digits(11),
        "DE_FONE2": _rand_digits(11),
        "DT_ABERTURA_REL": hoje,
        "CIC_CPF": documento[:14],
        "DS_GRUPO_CLIENTE": "PF" if eh_pf else "PJ",
        "DE_ENDERECO_RES": "RUA TESTE"[:80],
        "DE_CIDADE_RES": "SAO PAULO",
        "DE_ESTADO_RES": "SP",
        "DE_PAIS_RES": "BRASIL",
        "CD_CEP_RES": "00000000",
        "DE_ENDERECO_CML": "RUA CML"[:80],
        "DE_CIDADE_CML": "SAO PAULO",
        "DE_ESTADO_CML": "SP",
        "DE_PAIS_CML": "BRASIL",
        "CD_CEP_CML": "00000000",
        "DT_DESATIVACAO": dt_desativacao,
        "DT_ULT_ALTERACAO": hoje,
        "DS_RAMO_ATV": str(ds_ramo)[:80],
        "FL_FUNDO_INVEST": _to_bool_int(custom.get("FL_FUNDO_INVEST"), 0),
        "FL_CLI_EVENTUAL": _to_bool_int(custom.get("FL_CLI_EVENTUAL"), 0),
        "DE_RESPONS_CADASTRO": "SISTEMA",
        "DE_CONF_CADASTRO": "SISTEMA",
        "CD_RISCO": _to_int(custom.get("CD_RISCO"), 1),
        "CD_NAIC": "0000",
        "DE_LINHA_NEGOCIO": "GERAL",
        "FL_CADASTRO_PROC": 0,
        "FL_NAO_RESIDENTE": 0,
        "FL_GRANDES_FORTUNAS": _to_bool_int(custom.get("FL_GRANDES_FORTUNAS"), 0),
        "DE_PAIS_SEDE": "BRASIL",
        "DE_SIT_CADASTRO": "ATIVO",
        "FL_BLOQUEADO": 0,
        "CD_RISCO_INERENTE": _to_int(custom.get("CD_RISCO_INERENTE"), 1),
        "DT_CONSTITUICAO": dt_constituicao,
        "IP_ELETRONICO": "127.0.0.1",
        "DE_EMAIL": f"contato_{documento[:8]}@teste.com",
        "FL_RELACIONAMENTO_TERCEIROS": 0,
        "FL_ADMIN_CARTOES": 0,
        "FL_EMPRESA_TRUST": 0,
        "FL_FACILITADORA_PAGTO": 0,
        "CD_NAT_JURIDICA": str(nat_juridica)[:5],
        "FL_EMP_REGULADA": 0,
    }

    if versao == "V9":
        record.update({
            "DE_PAIS_DOMICILIO_FISCAL": "BRASIL",
            "DE_PAIS_CONTROLE_ACIONARIO": "BRASIL",
            "CD_ORIGEM_RECURSOS": _to_int(custom.get("CD_ORIGEM_RECURSOS"), 1),
            "ID_TITULARIDADE": _to_int(custom.get("ID_TITULARIDADE"), 1),
            "DS_CANAL": str(custom.get("DS_CANAL") or "AUTOMATICO")[:40],
        })

    return record


def _build_insert_statement(columns: list[str]) -> str:
    cols = ", ".join(columns)
    params = ", ".join(["?" for _ in columns])
    return f"""
        INSERT INTO TAB_CLIENTES_PLD ({cols})
        SELECT {params}
        WHERE NOT EXISTS (
            SELECT 1
            FROM TAB_CLIENTES_PLD WITH (NOLOCK)
            WHERE CD_CLIENTE = ?
        )
    """

def _build_conn_str(servidor, banco, usuario, senha, driver):
    drv = (driver or "ODBC Driver 17 for SQL Server").strip("{}")
    return (
        f"DRIVER={{{drv}}};"
        f"SERVER={servidor};"
        f"DATABASE={banco};"
        f"UID={usuario};"
        f"PWD={senha};"
        f"TrustServerCertificate=yes;"
    )

def _set_job(job_id, status, percent, inserted, message):
    with JOBS_LOCK:
        JOBS[job_id] = {
            "status": status,
            "percent": int(percent),
            "inserted": int(inserted),
            "message": message
        }

def _run_insert(job_id, req):
    try:
        _set_job(job_id, "running", 0, 0, "starting")
        conn_str = _build_conn_str(req.servidor, req.banco, req.usuario, req.senha, req.driver)
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.fast_executemany = True

        custom = {}
        try:
            custom = json.loads(req.customizacao_json or "{}")
            if not isinstance(custom, dict):
                custom = {}
        except Exception:
            custom = {}

        total_solicitado = int(req.quantidade or 0)
        qtd_pf_req = int(req.qtd_pf or 0)
        qtd_pj_req = int(req.qtd_pj or 0)

        forced_type = str(custom.get("CD_TP_CLIENTE") or "").strip()
        if forced_type in {"01", "02"}:
            if forced_type == "01":
                qtd_pf_req = total_solicitado
                qtd_pj_req = 0
            else:
                qtd_pf_req = 0
                qtd_pj_req = total_solicitado

        if qtd_pf_req > 0 or qtd_pj_req > 0:
            limit_pf = max(0, qtd_pf_req)
            limit_pj = max(0, qtd_pj_req)
            total = limit_pf + limit_pj
        else:
            limit_pf = total_solicitado // 2
            limit_pj = total_solicitado - limit_pf
            total = total_solicitado

        available_columns = _fetch_tab_clientes_columns(cursor)
        if "CD_CLIENTE" not in available_columns or "DE_CLIENTE" not in available_columns:
            raise RuntimeError("Tabela TAB_CLIENTES_PLD não possui colunas mínimas CD_CLIENTE e DE_CLIENTE")

        versao_layout = _infer_layout_version(req.versao, available_columns)

        preferred_columns = [
            "CD_CLIENTE", "DE_CLIENTE", "CD_TP_CLIENTE", "DE_ENDERECO", "DE_CIDADE", "DE_ESTADO", "DE_PAIS",
            "CD_CEP", "DE_FONE1", "DE_FONE2", "DT_ABERTURA_REL", "CIC_CPF", "DS_GRUPO_CLIENTE",
            "DE_ENDERECO_RES", "DE_CIDADE_RES", "DE_ESTADO_RES", "DE_PAIS_RES", "CD_CEP_RES",
            "DE_ENDERECO_CML", "DE_CIDADE_CML", "DE_ESTADO_CML", "DE_PAIS_CML", "CD_CEP_CML",
            "DT_DESATIVACAO", "DT_ULT_ALTERACAO", "DS_RAMO_ATV", "FL_FUNDO_INVEST", "FL_CLI_EVENTUAL",
            "DE_RESPONS_CADASTRO", "DE_CONF_CADASTRO", "CD_RISCO", "CD_NAIC", "DE_LINHA_NEGOCIO",
            "FL_CADASTRO_PROC", "FL_NAO_RESIDENTE", "FL_GRANDES_FORTUNAS", "DE_PAIS_SEDE",
            "DE_SIT_CADASTRO", "FL_BLOQUEADO", "CD_RISCO_INERENTE", "DT_CONSTITUICAO",
            "IP_ELETRONICO", "DE_EMAIL", "FL_RELACIONAMENTO_TERCEIROS", "FL_ADMIN_CARTOES",
            "FL_EMPRESA_TRUST", "FL_FACILITADORA_PAGTO", "CD_NAT_JURIDICA", "FL_EMP_REGULADA",
            "DE_PAIS_DOMICILIO_FISCAL", "DE_PAIS_CONTROLE_ACIONARIO", "CD_ORIGEM_RECURSOS", "ID_TITULARIDADE", "DS_CANAL"
        ]

        insert_columns = [column for column in preferred_columns if column in available_columns]
        sql_final = _build_insert_statement(insert_columns)

        batch_size = 2000 if total >= 10000 else 1000
        inserted = 0
        conta_pf = 0
        conta_pj = 0

        while inserted < total:
            current = min(batch_size, total - inserted)
            rows = []

            while len(rows) < current and (conta_pf + conta_pj) < total:
                if conta_pf < limit_pf and (conta_pj >= limit_pj or random.random() > 0.5):
                    tp_cli = "01"
                    conta_pf += 1
                else:
                    tp_cli = "02"
                    conta_pj += 1

                record = _build_cliente_record(tp_cli, custom, versao_layout)
                values = [record.get(column) for column in insert_columns]
                values.append(record["CD_CLIENTE"])  # parâmetro do WHERE NOT EXISTS
                rows.append(tuple(values))

            if not rows:
                break

            try:
                cursor.executemany(sql_final, rows)
                conn.commit()
            except Exception:
                conn.rollback()
                raise

            inserted += len(rows)
            percent = int((inserted / total) * 100) if total > 0 else 100
            _set_job(job_id, "running", percent, inserted, f"inserting ({versao_layout})")
            time.sleep(0.01)

        cursor.close()
        conn.close()
        _set_job(job_id, "done", 100, inserted, f"completed ({versao_layout})")

    except Exception as e:
        _set_job(job_id, "error", 0, 0, str(e))

class DataGeneratorService(gerador_pb2_grpc.DataGeneratorServicer):
    def GenerateClientes(self, request, context):
        job_id = str(uuid.uuid4())[:8]
        _set_job(job_id, "queued", 0, 0, "queued")
        t = threading.Thread(target=_run_insert, args=(job_id, request), daemon=True)
        t.start()

        return gerador_pb2.GenerateClientesResponse(
            status="accepted",
            job_id=job_id,
            message="job queued",
            inserted=0
        )

    def GetJobStatus(self, request, context):
        with JOBS_LOCK:
            data = JOBS.get(request.job_id)
        if not data:
            return gerador_pb2.JobStatusResponse(
                status="not_found",
                percent=0,
                inserted=0,
                message="job not found"
            )
        return gerador_pb2.JobStatusResponse(
            status=data["status"],
            percent=data["percent"],
            inserted=data["inserted"],
            message=data["message"]
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    gerador_pb2_grpc.add_DataGeneratorServicer_to_server(DataGeneratorService(), server)
    server.add_insecure_port("0.0.0.0:50051")
    server.start()
    print("gRPC worker listening on 0.0.0.0:50051")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    serve()
