import os
import uuid
import random
import sqlite3
import threading
import pypyodbc as pyodbc 
from datetime import datetime 
from typing import Dict, Any 
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS 
from faker import Faker

# --- CONFIGURAÇÕES ---
base_dir = os.path.abspath(os.path.dirname(__file__))
static_folder = os.path.join(base_dir, 'static')
db_path = os.path.join(base_dir, 'database.db')

app = Flask(__name__, static_folder=static_folder)
CORS(app) 
fake = Faker("pt_BR")

# --- APOIO ---
def gerar_cpf_limpo():
    n = [random.randint(0, 9) for _ in range(9)]
    for _ in range(2):
        d = sum(x * y for x, y in zip(n, range(len(n) + 1, 1, -1))) % 11
        n.append(11 - d if d > 1 else 0)
    return "".join(map(str, n))

def gerar_cnpj_limpo():
    n = [random.randint(0, 9) for _ in range(8)] + [0, 0, 0, 1]
    for _ in range(2):
        pesos = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2] if len(n) == 12 else [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        d = sum(x * y for x, y in zip(n, pesos)) % 11
        n.append(11 - d if d > 1 else 0)
    return "".join(map(str, n))

def get_connection_string(config):
    driver = "{ODBC Driver 17 for SQL Server}"
    return (f"DRIVER={driver};SERVER={config['servidor']};DATABASE={config['banco']};"
            f"UID={config['usuario']};PWD={config['senha']};ConnectTimeout=15;TrustServerCertificate=yes;")

# --- GERADORES COM SUPORTE A DATA ---
def gerar_movfin_pld(data_ref) -> Dict[str, Any]:
    dthr = datetime.combine(data_ref, datetime.now().time())
    return {
        "CD_IDENTIFICACAO": str(uuid.uuid4())[:40], "CD_VEIC_LEGAL": 1,
        "CD_AGENCIA": "0001", "CD_AGENCIA_MOVTO": "0001", "CD_CONTA": "12345-6",
        "CD_CLIENTE": "CLI123", "DT_MOVIMENTA": data_ref, "DTHR_MOVIMENTA": dthr,
        "CD_MOEDA": "BRL", "VL_OPERACAO": round(random.uniform(100, 5000), 2),
        "TP_DEB_CRED": random.choice(['D', 'C']), "CD_FORMA": "TED",
        "DE_CONTRAPARTE": fake.name().upper(), "DE_BANCO_CONTRA": "BANCO",
        "DE_AGENCIA_CONTRA": "0001", "CD_CONTA_CONTRA": "1", "CD_PAIS_CONTRA": "BRASIL",
        "DE_ORIGEM_OPE": "SISTEMA", "CD_PRODUTO": "1", "DE_FINALIDADE": "PAGTO",
        "CPF_CNPJ_CONTRA": gerar_cpf_limpo(), "DS_CIDADE_CONTRA": "SP", "DS_COMP_HISTORICO": "TRANSF",
        "VL_RENDIMENTO": 0, "DT_PREV_LIQUIDACAO": data_ref, "CD_ISPB_EMISSOR": 0,
        "NR_CHEQUE": "0", "DE_TP_DOCTO_CONTRA": "CPF", "NR_DOCTO_CONTRA": "0",
        "DE_EXECUTOR": "ADMIN", "CPF_EXECUTOR": "0", "NR_PASSAPORTE_EXEC": "0",
        "FL_IOF_CARENCIA": 0, "CD_NAT_OPERACAO": "1", "DE_ORDENANTE": "CLI",
        "UF_MOVTO": "SP", "NR_POS": "0", "DS_CIDADE_POS": "SP", "DS_CANAL": "WEB",
        "DS_ORIGEM_RECURSO": "SALDO", "DS_DESTINO_RECURSO": "PAGTO", "CD_PROVISIONAMENTO": "0", "DS_AMBIENTE_NEG": "PROD"
    }

def gerar_lote_movfin_me_pld(set_clientes, data_escolhida):
    registros = []
    cd_cliente = random.choice(list(set_clientes))
    dthr_combinada = datetime.combine(data_escolhida, datetime.now().time())
    for tipo in ['D', 'C']:
        registro = {
            "CD_IDENTIFICACAO": f"ME-{uuid.uuid4().hex[:20].upper()}",
            "CD_VEIC_LEGAL": 1, "CD_AGENCIA": "0001", "CD_CONTA": "12345", "CD_CLIENTE": cd_cliente,
            "DT_MOVIMENTA": data_escolhida, "DTHR_MOVIMENTA": dthr_combinada,
            "CD_MOEDA_ME": "BRL", "VL_OPERACAO_ME": round(random.uniform(1000, 5000), 2),
            "TX_COTACAO_ME": 1.0, "VL_OPERACAO_USD": 500, "TP_DEB_CRED": tipo,
            "CD_FORMA": "101", "DE_CONTRAPARTE": fake.company().upper(),
            "CD_BIC_BANCO_CONTRA": "BICBR", "DE_BANCO_CONTRA": "BANCO", "DE_AGENCIA_CONTRA": "1",
            "CD_CONTA_CONTRA": "1", "CD_PAIS_CONTRA": "EUA", "DE_ORIGEM_OPE": "WEB",
            "CD_PRODUTO": "1", "DE_FINALIDADE": "PAGTO", "CPF_CNPJ_CONTRA": "0",
            "DS_CIDADE_CONTRA": "NY", "DS_COMP_HISTORICO": "LIQ", "DE_TP_DOCTO_CONTRA": "FAT",
            "NR_DOCTO_CONTRA": "0", "DE_EXECUTOR": "ADM", "CPF_EXECUTOR": "0",
            "NR_PASSAPORTE_EXEC": "0", "CD_NAT_OPERACAO": "1", "DE_ORDENANTE": cd_cliente,
            "UF_MOVTO": "SP", "DE_OPERADOR": "SIS", "TX_PTAX": 5.25
        }
        registros.append(registro)
    return registros

def gerar_movfin_inter_pld(data_ref) -> Dict[str, Any]:
    return {
        "CD_IDENTIFICACAO": str(uuid.uuid4())[:40], "CD_CLIENTE": "CLI123",
        "DT_MOVIMENTA": data_ref, "NR_ORDEMPAGAMENTO": "OP123",
        "DT_PAGAMENTO": data_ref, "CPF_CNPJ": gerar_cnpj_limpo(), "DE_CLIENTE": "EMPRESA",
        "TP_DOC": "CNPJ", "DE_MOEDA": "BRL", "VL_ME": 1000, "VL_USD": 200, "VL_CONTABIL_MN": 1000,
        "VL_FECHAMENTOVENDA_MN": 1000, "VL_GIRO": 0, "DS_SITUACAO": "LIQ",
        "TP_MOVIMENTACAO": "REMESSA", "DE_ORIGINADOR": "ORIG", "TP_DOCUMENTOORIGINADOR": "CPF",
        "CPF_CNPJ_ORIGINADOR": "0", "DE_PAISORIGINADOR": "BRASIL", "DE_FAVORECIDO": "FAV",
        "TP_DOCUMENTOFAVORECIDO": "ID", "CPF_CNPJ_FAVORECIDO": "0", "DE_PAISFAVORECIDO": "PORTUGAL",
        "DE_DETALHESPAGAMENTO": "SERV", "TP_CONTACORRENTE": "CORRENTE", "DE_ORIGEM": 1
    }

# --- ROTAS API ---
@app.route("/setup_ambiente", methods=["POST"])
def setup_ambiente():
    config = request.json.get('config')
    scripts = {
        "TAB_CLIENTES_PLD": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_PLD' AND xtype='U')
            CREATE TABLE [dbo].[TAB_CLIENTES_PLD]([CD_CLIENTE] [char](20) NOT NULL PRIMARY KEY, [DE_CLIENTE] [varchar](120) NULL, [CD_TP_CLIENTE] [char](2) NOT NULL, [DE_ENDERECO] [varchar](80) NOT NULL, [DE_CIDADE] [varchar](40) NOT NULL, [DE_ESTADO] [char](2) NOT NULL, [DE_PAIS] [varchar](40) NOT NULL, [CD_CEP] [varchar](10) NOT NULL, [DE_FONE1] [varchar](14) NOT NULL, [DE_FONE2] [varchar](14) NOT NULL, [DT_ABERTURA_REL] [datetime] NOT NULL, [CIC_CPF] [varchar](20) NOT NULL, [DS_GRUPO_CLIENTE] [varchar](50) NOT NULL, [DE_ENDERECO_RES] [varchar](80) NOT NULL, [DE_CIDADE_RES] [varchar](40) NOT NULL, [DE_ESTADO_RES] [char](2) NOT NULL, [DE_PAIS_RES] [varchar](40) NOT NULL, [CD_CEP_RES] [varchar](10) NOT NULL, [DE_ENDERECO_CML] [varchar](80) NOT NULL, [DE_CIDADE_CML] [varchar](40) NOT NULL, [DE_ESTADO_CML] [char](2) NOT NULL, [DE_PAIS_CML] [varchar](40) NOT NULL, [CD_CEP_CML] [varchar](10) NOT NULL, [DT_DESATIVACAO] [datetime] NOT NULL, [DT_ULT_ALTERACAO] [datetime] NOT NULL, [DS_RAMO_ATV] [varchar](80) NOT NULL, [FL_FUNDO_INVEST] [bit] NOT NULL, [FL_CLI_EVENTUAL] [bit] NOT NULL, [DE_RESPONS_CADASTRO] [varchar](60) NOT NULL, [DE_CONF_CADASTRO] [varchar](60) NOT NULL, [CD_RISCO] [smallint] NOT NULL, [CD_NAIC] [varchar](20) NOT NULL, [DE_LINHA_NEGOCIO] [varchar](20) NOT NULL, [FL_CADASTRO_PROC] [bit] NOT NULL, [FL_NAO_RESIDENTE] [bit] NOT NULL, [FL_GRANDES_FORTUNAS] [bit] NOT NULL, [DE_PAIS_SEDE] [varchar](40) NOT NULL, [DE_SIT_CADASTRO] [varchar](40) NOT NULL, [FL_BLOQUEADO] [bit] NOT NULL, [CD_RISCO_INERENTE] [smallint] NOT NULL, [DT_CONSTITUICAO] [datetime] NOT NULL, [IP_ELETRONICO] [varchar](104) NOT NULL, [DE_EMAIL] [varchar](100) NOT NULL, [FL_RELACIONAMENTO_TERCEIROS] [bit] NOT NULL, [FL_ADMIN_CARTOES] [bit] NOT NULL, [FL_EMPRESA_TRUST] [bit] NOT NULL, [FL_FACILITADORA_PAGTO] [bit] NOT NULL, [CD_NAT_JURIDICA] [varchar](5) NOT NULL, [FL_EMP_REGULADA] [bit] NOT NULL)""",
        
        "TAB_CLIENTES_MOVFIN_PLD": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_MOVFIN_PLD' AND xtype='U')
            CREATE TABLE [dbo].[TAB_CLIENTES_MOVFIN_PLD]([CD_IDENTIFICACAO] [varchar](40) NOT NULL PRIMARY KEY, [CD_VEIC_LEGAL] [smallint] NOT NULL, [CD_AGENCIA] [char](10) NOT NULL, [CD_AGENCIA_MOVTO] [char](10) NOT NULL, [CD_CONTA] [varchar](50) NOT NULL, [CD_CLIENTE] [varchar](20) NOT NULL, [DT_MOVIMENTA] [datetime] NOT NULL, [DTHR_MOVIMENTA] [datetime] NOT NULL, [CD_MOEDA] [varchar](10) NOT NULL, [VL_OPERACAO] [money] NOT NULL, [TP_DEB_CRED] [char](1) NOT NULL, [CD_FORMA] [varchar](20) NOT NULL, [DE_CONTRAPARTE] [varchar](120) NOT NULL, [DE_BANCO_CONTRA] [varchar](60) NOT NULL, [DE_AGENCIA_CONTRA] [varchar](60) NOT NULL, [CD_CONTA_CONTRA] [varchar](50) NOT NULL, [CD_PAIS_CONTRA] [varchar](40) NOT NULL, [DE_ORIGEM_OPE] [varchar](40) NOT NULL, [CD_PRODUTO] [varchar](20) NOT NULL, [DE_FINALIDADE] [varchar](400) NOT NULL, [CPF_CNPJ_CONTRA] [varchar](20) NOT NULL, [DS_CIDADE_CONTRA] [varchar](60) NOT NULL, [DS_COMP_HISTORICO] [varchar](50) NOT NULL, [VL_RENDIMENTO] [money] NOT NULL, [DT_PREV_LIQUIDACAO] [datetime] NOT NULL, [CD_ISPB_EMISSOR] [int] NOT NULL, [NR_CHEQUE] [varchar](20) NOT NULL, [DE_TP_DOCTO_CONTRA] [varchar](40) NOT NULL, [NR_DOCTO_CONTRA] [varchar](50) NOT NULL, [DE_EXECUTOR] [varchar](60) NOT NULL, [CPF_EXECUTOR] [varchar](20) NOT NULL, [NR_PASSAPORTE_EXEC] [varchar](20) NOT NULL, [FL_IOF_CARENCIA] [bit] NOT NULL, [CD_NAT_OPERACAO] [varchar](20) NOT NULL, [DE_ORDENANTE] [varchar](120) NOT NULL, [UF_MOVTO] [char](2) NOT NULL, [NR_POS] [varchar](20) NOT NULL, [DS_CIDADE_POS] [varchar](60) NOT NULL, [DS_CANAL] [varchar](15) NOT NULL, [DS_ORIGEM_RECURSO] [varchar](40) NOT NULL, [DS_DESTINO_RECURSO] [varchar](40) NOT NULL, [CD_PROVISIONAMENTO] [varchar](40) NOT NULL, [DS_AMBIENTE_NEG] [varchar](20) NOT NULL)""",

        "TAB_CLIENTES_MOVFIN_ME_PLD": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_MOVFIN_ME_PLD' AND xtype='U')
            CREATE TABLE [dbo].[TAB_CLIENTES_MOVFIN_ME_PLD]([CD_IDENTIFICACAO] [varchar](40) NOT NULL PRIMARY KEY, [CD_VEIC_LEGAL] [smallint] NOT NULL, [CD_AGENCIA] [char](10) NOT NULL, [CD_CONTA] [varchar](50) NOT NULL, [CD_CLIENTE] [varchar](20) NOT NULL, [DT_MOVIMENTA] [datetime] NOT NULL, [DTHR_MOVIMENTA] [datetime] NOT NULL, [CD_MOEDA_ME] [varchar](10) NOT NULL, [VL_OPERACAO_ME] [money] NOT NULL, [TX_COTACAO_ME] [money] NOT NULL, [VL_OPERACAO_USD] [money] NOT NULL, [TP_DEB_CRED] [char](1) NOT NULL, [CD_FORMA] [varchar](20) NOT NULL, [DE_CONTRAPARTE] [varchar](120) NOT NULL, [CD_BIC_BANCO_CONTRA] [varchar](20) NOT NULL, [DE_BANCO_CONTRA] [varchar](60) NOT NULL, [DE_AGENCIA_CONTRA] [varchar](60) NOT NULL, [CD_CONTA_CONTRA] [varchar](50) NOT NULL, [CD_PAIS_CONTRA] [varchar](40) NOT NULL, [DE_ORIGEM_OPE] [varchar](40) NOT NULL, [CD_PRODUTO] [varchar](20) NOT NULL, [DE_FINALIDADE] [varchar](400) NOT NULL, [CPF_CNPJ_CONTRA] [varchar](20) NOT NULL, [DS_CIDADE_CONTRA] [varchar](60) NOT NULL, [DS_COMP_HISTORICO] [varchar](50) NOT NULL, [DE_TP_DOCTO_CONTRA] [varchar](40) NOT NULL, [NR_DOCTO_CONTRA] [varchar](50) NOT NULL, [DE_EXECUTOR] [varchar](60) NOT NULL, [CPF_EXECUTOR] [varchar](20) NOT NULL, [NR_PASSAPORTE_EXEC] [varchar](20) NOT NULL, [CD_NAT_OPERACAO] [varchar](20) NOT NULL, [DE_ORDENANTE] [varchar](120) NOT NULL, [UF_MOVTO] [char](2) NOT NULL, [DE_OPERADOR] [varchar](60) NOT NULL, [TX_PTAX] [money] NOT NULL)""",

        "TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD' AND xtype='U')
            CREATE TABLE [dbo].[TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD]([CD_IDENTIFICACAO] [varchar](40) NOT NULL PRIMARY KEY, [CD_CLIENTE] [varchar](20) NOT NULL, [DT_MOVIMENTA] [datetime] NOT NULL, [NR_ORDEMPAGAMENTO] [varchar](20) NOT NULL, [DT_PAGAMENTO] [datetime] NOT NULL, [CPF_CNPJ] [char](20) NOT NULL, [DE_CLIENTE] [varchar](120) NOT NULL, [TP_DOC] [varchar](20) NOT NULL, [DE_MOEDA] [varchar](20) NOT NULL, [VL_ME] [money] NOT NULL, [VL_USD] [money] NOT NULL, [VL_CONTABIL_MN] [money] NOT NULL, [VL_FECHAMENTOVENDA_MN] [money] NOT NULL, [VL_GIRO] [money] NOT NULL, [DS_SITUACAO] [varchar](20) NOT NULL, [TP_MOVIMENTACAO] [varchar](20) NOT NULL, [DE_ORIGINADOR] [varchar](120) NOT NULL, [TP_DOCUMENTOORIGINADOR] [varchar](20) NOT NULL, [CPF_CNPJ_ORIGINADOR] [varchar](20) NOT NULL, [DE_PAISORIGINADOR] [varchar](40) NOT NULL, [DE_FAVORECIDO] [varchar](120) NOT NULL, [TP_DOCUMENTOFAVORECIDO] [varchar](20) NOT NULL, [CPF_CNPJ_FAVORECIDO] [varchar](20) NOT NULL, [DE_PAISFAVORECIDO] [varchar](40) NOT NULL, [DE_DETALHESPAGAMENTO] [varchar](400) NOT NULL, [TP_CONTACORRENTE] [varchar](20) NOT NULL, [DE_ORIGEM] [int] NOT NULL)"""
    }
    try:
        conn = pyodbc.connect(get_connection_string(config))
        cursor = conn.cursor()
        for sql in scripts.values():
            cursor.execute(sql)
            conn.commit()
        conn.close()
        return jsonify({"message": "Estrutura pronta.", "status": "ok"}), 200
    except Exception as e: return jsonify({"erro": str(e)}), 500

@app.route("/gerar_e_injetar", methods=["POST"])
def gerar_e_injetar():
    dados = request.json
    config = dados.get('config')
    qtd = int(dados.get('quantidade', 1))
    tipo = dados.get('tipo', 'CLIENTES')
    data_str = dados.get('data_referencia')
    data_ref = datetime.strptime(data_str, '%Y-%m-%d').date() if data_str else datetime.now().date()

    def worker(cfg, total, tp, dt_esc):
        try:
            conn = pyodbc.connect(get_connection_string(cfg))
            cursor = conn.cursor()
            cursor.fast_executemany = True
            lote = []
            exemplo = None

            if tp == "CLIENTES":
                for _ in range(total):
                    cd = gerar_cpf_limpo()
                    dt_reg = datetime.combine(dt_esc, datetime.now().time())
                    reg = (cd, fake.name().upper()[:120], '01', 'RUA A', 'SP', 'SP', 'BRASIL', '01000', '11', '11', dt_reg, cd, 'GRP', 'RES', 'CID', 'SP', 'BR', '01', 'COM', 'CID', 'SP', 'BR', '01', datetime(1900,1,1), dt_reg, 'TI', 0, 0, 'SIS', 'SIS', 1, '0', 'V', 1, 0, 0, 'BR', 'ATIVO', 0, 0, datetime(1900,1,1), '127.0.0.1', 'a@a.com', 0, 0, 0, 0, '1', 0)
                    lote.append(reg)
                cursor.executemany("INSERT INTO TAB_CLIENTES_PLD VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", lote)

            elif tp == "MOVFIN_ME":
                cursor.execute("SELECT CD_CLIENTE FROM TAB_CLIENTES_PLD")
                clis = [row[0].strip() for row in cursor.fetchall()]
                if not clis: return
                for _ in range(max(1, total // 2)):
                    for d in gerar_lote_movfin_me_pld(clis, dt_esc):
                        if exemplo is None: exemplo = d
                        lote.append(tuple(d.values()))
                
                cols = ', '.join(exemplo.keys())
                params = ', '.join(['?' for _ in exemplo])
                cursor.executemany(f"INSERT INTO TAB_CLIENTES_MOVFIN_ME_PLD ({cols}) VALUES ({params})", lote)

            else:
                mapa = {"MOVFIN": (gerar_movfin_pld, "TAB_CLIENTES_MOVFIN_PLD"), "MOVFIN_INTERMEDIADOR": (gerar_movfin_inter_pld, "TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD")}
                func, tab = mapa[tp]
                for _ in range(total):
                    d = func(dt_esc)
                    if exemplo is None: exemplo = d
                    lote.append(tuple(d.values()))
                
                cols = ', '.join(exemplo.keys())
                params = ', '.join(['?' for _ in exemplo])
                cursor.executemany(f"INSERT INTO {tab} ({cols}) VALUES ({params})", lote)

            conn.commit()
            conn.close()
        except Exception as e: print(f"Erro Background: {e}")

    threading.Thread(target=worker, args=(config, qtd, tipo, data_ref)).start()
    return jsonify({"message": f"Carga {tipo} para {data_ref} iniciada!", "status": "ok"}), 200

# --- SAÚDE E LOGIN ---
@app.route('/login', methods=['POST'])
def login():
    d = request.json
    if d.get('username') == 'admin' and d.get('password') == '1234':
        return jsonify({"status": "ok", "user": "admin", "tipo": "ADMIN"}), 200
    return jsonify({"message": "Erro"}), 401

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)