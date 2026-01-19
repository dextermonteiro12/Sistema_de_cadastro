from flask import Blueprint, request, jsonify
import pypyodbc as pyodbc
import threading
import uuid
import random
from datetime import datetime, timedelta
from utils import get_connection_string, fake
from config import Config

movimentacoes_bp = Blueprint('movimentacoes', __name__)

# --- FUNÇÃO AUXILIAR DE INTELIGÊNCIA TEMPORAL ---
def gerar_data_pld(modo, data_referencia_base):
    hoje = datetime.now().date()
    
    if modo == 'mes_atual':
        dia = random.randint(1, hoje.day)
        return hoje.replace(day=dia)
    
    elif modo == 'mes_anterior':
        primeiro_dia_mes_atual = hoje.replace(day=1)
        ultimo_dia_mes_anterior = primeiro_dia_mes_atual - timedelta(days=1)
        dia = random.randint(1, ultimo_dia_mes_anterior.day)
        return ultimo_dia_mes_anterior.replace(day=dia)
    
    return data_referencia_base

# --- CENÁRIO 1: NACIONAL (TAB_CLIENTES_MOVFIN_PLD) ---
def executar_carga_nacional(cursor, clientes, data_ref, modo_data, qtd_solicitada):
    tabela = "TAB_CLIENTES_MOVFIN_PLD"
    num_campos = 43
    lote = []
    sql = f"INSERT INTO {tabela} VALUES ({', '.join(['?' for _ in range(num_campos)])})"
    
    # Define quantas vezes repetir o par C/D
    vezes = int(qtd_solicitada) if qtd_solicitada else 1
    
    for cli in clientes:
        id_cliente_real = cli[0]
        for _ in range(vezes):
            for natureza in ['C', 'D']:
                dt_final = gerar_data_pld(modo_data, data_ref)
                dthr = datetime.combine(dt_final, datetime.now().time())
                
                lote.append((
                    str(uuid.uuid4())[:40], 1, "0001", "0001", "12345-6",
                    id_cliente_real, dt_final, dthr, "BRL", 
                    round(random.uniform(100, 5000), 2), natureza, "TED", 
                    fake.name().upper()[:120], "BANCO", "0001", "1", "BRASIL", 
                    "SISTEMA", "1", "PAGTO", id_cliente_real, "SP", "TRANSF", 
                    0, dt_final, 0, "0", "CPF", "0", "ADMIN", "0", "0",
                    0, "1", "CLI", "SP", "0", "SP", "WEB",
                    "SALDO", "PAGTO", "0", "PROD"
                ))
                if len(lote) >= 1000:
                    cursor.executemany(sql, lote)
                    lote = []
    if lote: cursor.executemany(sql, lote)

# --- CENÁRIO 2: MOEDA ESTRANGEIRA (TAB_CLIENTES_MOVFIN_ME_PLD) ---
def executar_carga_me(cursor, clientes, data_ref, modo_data, qtd_solicitada):
    tabela = "TAB_CLIENTES_MOVFIN_ME_PLD"
    num_campos = 35
    lote = []
    sql = f"INSERT INTO {tabela} VALUES ({', '.join(['?' for _ in range(num_campos)])})"
    
    vezes = int(qtd_solicitada) if qtd_solicitada else 1
    
    for cli in clientes:
        id_cliente_real = cli[0]
        for _ in range(vezes):
            for natureza in ['C', 'D']:
                dt_final = gerar_data_pld(modo_data, data_ref)
                dthr = datetime.combine(dt_final, datetime.now().time())
                vl_me = round(random.uniform(500, 10000), 2)
                
                lote.append((
                    str(uuid.uuid4())[:40], 1, "0001", "554433-2",
                    id_cliente_real, dt_final, dthr,
                    "USD", vl_me, 5.15, round(vl_me * 5.15, 2),
                    natureza, "ORDEM PGTO", fake.company().upper()[:120],
                    "SWIFT123", "CITIBANK NY", "MANHATTAN", "ACC-998877", "USA",
                    "SISTEMA_CAMBIO", "CAMBIO_EXPORT", "PAGAMENTO SERVICOS",
                    id_cliente_real, "NEW YORK", "LIQUIDACAO CAMBIO", "INVOICE",
                    str(random.randint(1000, 9999)), fake.name().upper()[:60],
                    id_cliente_real, "N/A", "10005", fake.name().upper()[:120],
                    "SP", "OPERADOR_01", 5.12
                ))
                if len(lote) >= 1000:
                    cursor.executemany(sql, lote)
                    lote = []
    if lote: cursor.executemany(sql, lote)

# --- CENÁRIO 3: INTERMEDIADOR (TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD) ---
def executar_carga_intermediador(cursor, clientes, data_ref, modo_data, qtd_solicitada):
    tabela = "TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD"
    num_campos = 27
    lote = []
    sql = f"INSERT INTO {tabela} VALUES ({', '.join(['?' for _ in range(num_campos)])})"
    
    vezes = int(qtd_solicitada) if qtd_solicitada else 1
    
    for cli in clientes:
        id_cliente_real = cli[0]
        for _ in range(vezes):
            dt_final = gerar_data_pld(modo_data, data_ref)
            vl_base = round(random.uniform(1000, 50000), 2)
            
            lote.append((
                str(uuid.uuid4())[:40], id_cliente_real,
                dt_final, str(random.randint(10000, 99999)), dt_final,
                id_cliente_real, fake.name().upper()[:120], "FATURA",
                "DOLAR AMERICANO", vl_base, vl_base, round(vl_base * 5.15, 2),
                round(vl_base * 5.18, 2), 0, "LIQUIDADA", "DISPONIBILIDADE",
                fake.company().upper()[:120], "CNPJ", "00.000.000/0001-91",
                "ESTADOS UNIDOS", fake.name().upper()[:120], "CPF",
                id_cliente_real, "BRASIL", "PAGTO TI", "CONTA CORRENTE", 1
            ))
            if len(lote) >= 1000:
                cursor.executemany(sql, lote)
                lote = []
    if lote: cursor.executemany(sql, lote)

# --- ROTA PRINCIPAL ---
@movimentacoes_bp.route("/gerar_movimentacoes", methods=["POST"])
def gerar_movimentacoes():
    dados = request.json
    config = dados.get('config')
    data_str = dados.get('data_referencia')
    tipo = dados.get('tipo', 'MOVFIN') 
    modo_data = dados.get('modo_data', 'fixa')
    busca = dados.get('busca')
    quantidade = dados.get('quantidade', 1) # Captura a quantidade vinda do JS

    try:
        data_ref = datetime.strptime(data_str, '%Y-%m-%d').date()
    except:
        data_ref = datetime.now().date()

    def worker(cfg, dt_base, tp_carga, modo, termo_busca, qtd_total):
        try:
            conn = pyodbc.connect(Config.get_connection_string(cfg))
            cursor = conn.cursor()
            cursor.fast_executemany = True
            
            # --- BUSCA FILTRADA ---
            sql_clientes = "SELECT CD_CLIENTE FROM TAB_CLIENTES_PLD"
            params = []
            
            if termo_busca:
                sql_clientes += " WHERE CD_CLIENTE = ? OR CIC_CPF = ? OR DE_CLIENTE LIKE ?"
                params = [termo_busca, termo_busca, f"%{termo_busca}%"]
            
            cursor.execute(sql_clientes, params)
            clientes = cursor.fetchall()
            
            if not clientes:
                print(f"⚠️ Nenhum cliente encontrado para: {termo_busca}")
                return

            print(f"🚀 Iniciando carga {tp_carga} para {len(clientes)} clientes. Qtd por cliente: {qtd_total}")

            if tp_carga == 'MOVFIN':
                executar_carga_nacional(cursor, clientes, dt_base, modo, qtd_total)
            elif tp_carga == 'MOVFIN_ME':
                executar_carga_me(cursor, clientes, dt_base, modo, qtd_total)
            elif tp_carga == 'MOVFIN_INTERMEDIADOR':
                executar_carga_intermediador(cursor, clientes, dt_base, modo, qtd_total)
            
            conn.commit()
            conn.close()
            print(f"✅ Carga {tp_carga} finalizada com sucesso.")
        except Exception as e:
            print(f"❌ Erro em {tp_carga}: {e}")

    # Passa a quantidade capturada para o worker
    threading.Thread(target=worker, args=(config, data_ref, tipo, modo_data, busca, quantidade)).start()
    
    return jsonify({
        "status": "ok", 
        "message": f"Processamento de {tipo} iniciado. Quantidade: {quantidade}x por cliente."
    }), 200