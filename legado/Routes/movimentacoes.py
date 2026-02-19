from flask import Blueprint, request, jsonify
import pyodbc 
import threading
from datetime import datetime
import random

from ambiente import detectar_versao_sistema 
from utils import gerar_data_pld 
from cargas import nacional, moeda_estrangeira, intermediador

movimentacoes_bp = Blueprint('movimentacoes', __name__)

@movimentacoes_bp.route("/gerar_movimentacoes", methods=["POST"])
def gerar_movimentacoes():
    dados = request.json
    config = dados.get('config')
    data_str = dados.get('data_referencia')
    tipo = dados.get('tipo', 'MOVFIN') 
    modo_data = dados.get('modo_data', 'fixa')
    busca = dados.get('busca')
    quantidade = dados.get('quantidade', 1)

    try:
        data_ref = datetime.strptime(data_str, '%Y-%m-%d').date()
    except:
        data_ref = datetime.now().date()

    def worker(cfg, dt_base, tp_carga, modo, termo_busca, qtd_total):
        conn = None 
        try:
            conn_str = Config.get_connection_string(cfg)
            conn = pyodbc.connect(conn_str, timeout=600) 
            conn.autocommit = True 
            cursor = conn.cursor()
            cursor.fast_executemany = True 
            
            versao = detectar_versao_sistema(cursor)
            
            # --- AJUSTE AQUI: Busca das 3 colunas necessárias para o Intermediador ---
            sql_clientes = "SELECT CD_CLIENTE, DE_CLIENTE, CD_TP_CLIENTE FROM TAB_CLIENTES_PLD"
            params = []
            
            if termo_busca:
                sql_clientes += " WHERE CD_CLIENTE = ? OR CIC_CPF = ? OR DE_CLIENTE LIKE ?"
                params = [termo_busca, termo_busca, f"%{termo_busca}%"]
            
            cursor.execute(sql_clientes, params)
            clientes = cursor.fetchall()
            
            if not clientes:
                print(f"⚠️ Aviso: Nenhum cliente encontrado na TAB_CLIENTES_PLD.")
                return

            print(f"🚀 Iniciando carga {tp_carga} para {len(clientes)} clientes encontrados...")
            
            if tp_carga == 'MOVFIN':
                nacional.executar_carga(cursor, versao, clientes, dt_base, gerar_data_pld, modo, qtd_total)
            elif tp_carga == 'MOVFIN_ME':
                moeda_estrangeira.executar_carga(cursor, versao, clientes, dt_base, gerar_data_pld, modo, qtd_total)
            elif tp_carga == 'MOVFIN_INTERMEDIADOR':
                # Agora 'clientes' contém [CD_CLIENTE, DE_CLIENTE, CD_TP_CLIENTE], resolvendo o erro de index
                intermediador.executar_carga(cursor, versao, clientes, dt_base, gerar_data_pld, modo, qtd_total)
            
            print(f"✅ Sucesso: Carga {tp_carga} finalizada.")
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"❌ Erro Crítico em {tp_carga}: {str(e)}")
            
        finally:
            if conn:
                conn.close()
                print("🔌 Conexão encerrada com segurança.")

    threading.Thread(target=worker, args=(config, data_ref, tipo, modo_data, busca, quantidade)).start()
    
    return jsonify({
        "status": "ok", 
        "message": f"Processamento de {tipo} iniciado.",
        "detalhes": f"Lote: 50.000 | Usando TAB_CLIENTES_PLD como base."
    }), 200