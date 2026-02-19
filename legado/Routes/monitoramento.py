from flask import Blueprint, request, jsonify
import pyodbc
from utils import get_connection_string

monitoramento_bp = Blueprint('monitoramento', __name__)

@monitoramento_bp.route("/status_dashboard", methods=["POST"])
def status_dashboard():
    dados = request.json
    config = dados.get('config')
    
    if not config:
        return jsonify({"status": "erro", "message": "Configuração SQL não fornecida"}), 400

    try:
        # Usando a função utilitária para obter a string de conexão padronizada
        conn = pyodbc.connect(get_connection_string(config), timeout=10)
        cursor = conn.cursor()
        
        # --- 1. RESUMO DE LOGS (TB_LISTA_PESQUISAS_LOG) ---
        # Verificamos se a tabela existe antes de consultar para evitar erro 500
        log_resumo = {"total_registros": 0, "data_antiga": "N/A", "data_recente": "N/A"}
        try:
            cursor.execute("""
                SELECT COUNT(1), MIN(DTHR_PESQUISA), MAX(DTHR_PESQUISA) 
                FROM TB_LISTA_PESQUISAS_LOG WITH (NOLOCK)
            """)
            row_log = cursor.fetchone()
            if row_log and row_log[0] > 0:
                log_resumo = {
                    "tabela": "TB_LISTA_PESQUISAS_LOG",
                    "total_registros": row_log[0],
                    "data_antiga": row_log[1].strftime('%d/%m/%Y %H:%M') if row_log[1] else "N/A",
                    "data_recente": row_log[2].strftime('%d/%m/%Y %H:%M') if row_log[2] else "N/A"
                }
        except:
            log_resumo["status"] = "Tabela de Log não encontrada"

        # --- 2. FILA PENDENTE E PROCESSADOS ---
        cursor.execute("SELECT COUNT(1) FROM ADSVC_EXECUTAR WITH (NOLOCK)")
        qtd_pendente = cursor.fetchone()[0]
        
        # Tentativa de ler processados (excluir)
        try:
            cursor.execute("SELECT COUNT(1) FROM ADSVC_EXECUTADOS_EXCLUIR WITH (NOLOCK)")
            qtd_processados = cursor.fetchone()[0]
        except:
            qtd_processados = 0

        # --- 3. FILA POR REGRA (Agrupamento) ---
        cursor.execute("""
            SELECT TOP 10 LEFT(DS_COMANDO1, 20) as Regra, COUNT(1) as Total
            FROM ADSVC_EXECUTAR WITH (NOLOCK) 
            GROUP BY LEFT(DS_COMANDO1, 20) 
            ORDER BY Total DESC
        """)
        regras = [{"regra": row[0].strip(), "qtd": row[1]} for row in cursor.fetchall()]

        # --- 4. PERFORMANCE DOS WORKERS (ADSVC_EXECUTANDO_...) ---
        tabelas_exec = [
            'ADSVC_EXECUTANDO', 'ADSVC_EXECUTANDO_MF1', 'ADSVC_EXECUTANDO_MF2', 
            'ADSVC_EXECUTANDO_MF3', 'ADSVC_EXECUTANDO_MF4', 'ADSVC_EXECUTANDO_MF5',
            'ADSVC_EXECUTANDO_LV1', 'ADSVC_EXECUTANDO_LV2', 'ADSVC_EXECUTANDO_LV3', 
            'ADSVC_EXECUTANDO_LV4', 'ADSVC_EXECUTANDO_LV5'
        ]
        
        performance_workers = []
        for t in tabelas_exec:
            # Query ajustada para buscar o maior tempo de execução atual
            sql_perf = f"""
                SELECT TOP 1 LEFT(DS_COMANDO1, 20), QT_TEMPO_EXEC 
                FROM {t} WITH (NOLOCK) 
                ORDER BY QT_TEMPO_EXEC DESC
            """
            try:
                cursor.execute(sql_perf)
                res = cursor.fetchone()
                if res:
                    performance_workers.append({
                        "worker": t.replace('ADSVC_EXECUTANDO_', '').replace('ADSVC_EXECUTANDO', 'PRINCIPAL'),
                        "regra": res[0].strip(),
                        "tempo": res[1]
                    })
            except:
                continue 

        cursor.close()
        conn.close()

        return jsonify({
            "status": "ok",
            "servidor": config.get('servidor'),
            "banco": config.get('banco'),
            "log_pesquisas": log_resumo,
            "fila_geral": {
                "pendente": qtd_pendente,
                "processados": qtd_processados
            },
            "regras": regras,
            "performance": performance_workers
        }), 200

    except Exception as e:
        return jsonify({"status": "erro", "erro": str(e)}), 500