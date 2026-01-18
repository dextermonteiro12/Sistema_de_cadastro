from flask import Blueprint, request, jsonify
import pypyodbc as pyodbc
import threading
import uuid
import random
from datetime import datetime
from utils import get_connection_string, fake
from config import Config

movimentacoes_bp = Blueprint('movimentacoes', __name__)

# --- CENÁRIO 1: NACIONAL (TAB_CLIENTES_MOVFIN_PLD) ---
def executar_carga_nacional(cursor, clientes, data_ref):
    tabela = "TAB_CLIENTES_MOVFIN_PLD"
    num_campos = 43
    lote = []
    sql = f"INSERT INTO {tabela} VALUES ({', '.join(['?' for _ in range(num_campos)])})"
    
    for cli in clientes:
        cpf_real = cli[0]
        for natureza in ['C', 'D']:
            dthr = datetime.combine(data_ref, datetime.now().time())
            registro = (
                str(uuid.uuid4())[:40], 1, "0001", "0001", "12345-6",
                f"CLI{random.randint(100, 999)}", data_ref, dthr,
                "BRL", round(random.uniform(100, 5000), 2),
                natureza, "TED", fake.name().upper()[:120], "BANCO",
                "0001", "1", "BRASIL", "SISTEMA", "1", "PAGTO",
                cpf_real, "SP", "TRANSF", 0, data_ref, 0,
                "0", "CPF", "0", "ADMIN", "0", "0",
                0, "1", "CLI", "SP", "0", "SP", "WEB",
                "SALDO", "PAGTO", "0", "PROD"
            )
            lote.append(registro)
            
            if len(lote) >= 5000:
                cursor.executemany(sql, lote)
                lote = []
    if lote:
        cursor.executemany(sql, lote)

# --- CENÁRIO 2: MOEDA ESTRANGEIRA (TAB_CLIENTES_MOVFIN_ME_PLD) ---
def executar_carga_me(cursor, clientes, data_ref):
    tabela = "TAB_CLIENTES_MOVFIN_ME_PLD"
    num_campos = 35
    lote = []
    sql = f"INSERT INTO {tabela} VALUES ({', '.join(['?' for _ in range(num_campos)])})"
    
    for cli in clientes:
        cpf_real = cli[0]
        for natureza in ['C', 'D']:
            dthr = datetime.combine(data_ref, datetime.now().time())
            moeda = random.choice(['USD', 'EUR', 'GBP'])
            vl_me = round(random.uniform(500, 10000), 2)
            cotacao = 5.15
            
            registro = (
                str(uuid.uuid4())[:40], 1, "0001", "554433-2",
                f"CLI{random.randint(100, 999)}", data_ref, dthr,
                moeda, vl_me, cotacao, round(vl_me * cotacao, 2),
                natureza, "ORDEM PGTO", fake.company().upper()[:120],
                "SWIFT123", "CITIBANK NY", "MANHATTAN", "ACC-998877", "USA",
                "SISTEMA_CAMBIO", "CAMBIO_EXPORT", "PAGAMENTO SERVICOS",
                cpf_real, "NEW YORK", "LIQUIDACAO CAMBIO", "INVOICE",
                str(random.randint(1000, 9999)), fake.name().upper()[:60],
                cpf_real, "N/A", "10005", fake.name().upper()[:120],
                "SP", "OPERADOR_01", 5.1234
            )
            lote.append(registro)
            
            if len(lote) >= 5000:
                cursor.executemany(sql, lote)
                lote = []
    if lote:
        cursor.executemany(sql, lote)

# --- CENÁRIO 3: INTERMEDIADOR (TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD) ---
def executar_carga_intermediador(cursor, clientes, data_ref):
    tabela = "TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD"
    num_campos = 27
    lote = []
    sql = f"INSERT INTO {tabela} VALUES ({', '.join(['?' for _ in range(num_campos)])})"
    
    for cli in clientes:
        cpf_real = cli[0]
        vl_base = round(random.uniform(1000, 50000), 2)
        registro = (
            str(uuid.uuid4())[:40], f"CLI{random.randint(100, 999)}",
            data_ref, str(random.randint(10000, 99999)), data_ref,
            cpf_real, fake.name().upper()[:120], "FATURA",
            "DOLAR AMERICANO", vl_base, vl_base, round(vl_base * 5.15, 2),
            round(vl_base * 5.18, 2), 0, "LIQUIDADA", "DISPONIBILIDADE",
            fake.company().upper()[:120], "CNPJ", "00.000.000/0001-91",
            "ESTADOS UNIDOS", fake.name().upper()[:120], "CPF",
            cpf_real, "BRASIL", "PAGTO TI", "CONTA CORRENTE", 1
        )
        lote.append(registro)
        
        if len(lote) >= 5000:
            cursor.executemany(sql, lote)
            lote = []
    if lote:
        cursor.executemany(sql, lote)

@movimentacoes_bp.route("/gerar_movimentacoes", methods=["POST"])
def gerar_movimentacoes():
    dados = request.json
    config = dados.get('config')
    data_str = dados.get('data_referencia')
    tipo = dados.get('tipo', 'MOVFIN') 
    
    try:
        data_ref = datetime.strptime(data_str, '%Y-%m-%d').date()
    except:
        data_ref = datetime.now().date()

    def worker(cfg, dt_esc, tp_carga):
        try:
            conn = pyodbc.connect(Config.get_connection_string(cfg))
            cursor = conn.cursor()
            cursor.fast_executemany = True
            
            # Busca clientes reais
            cursor.execute("SELECT CIC_CPF FROM TAB_CLIENTES_PLD")
            clientes = cursor.fetchall()
            
            if not clientes:
                print("Nenhum cliente encontrado para movimentar.")
                return

            # DIRECIOMANENTO SEGREGADO POR TIPO
            if tp_carga == 'MOVFIN':
                executar_carga_nacional(cursor, clientes, dt_esc)
            elif tp_carga == 'MOVFIN_ME':
                executar_carga_me(cursor, clientes, dt_esc)
            elif tp_carga == 'MOVFIN_INTERMEDIADOR':
                executar_carga_intermediador(cursor, clientes, dt_esc)
            
            conn.commit()
            conn.close()
            print(f"Sucesso: Carga {tp_carga} concluída.")
        except Exception as e:
            print(f"Erro em {tp_carga}: {e}")

    threading.Thread(target=worker, args=(config, data_ref, tipo)).start()
    return jsonify({"status": "ok", "message": f"Injeção isolada de {tipo} iniciada"}), 200