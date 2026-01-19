from flask import Blueprint, request, jsonify
import pypyodbc as pyodbc
from config import Config

monitoramento_bp = Blueprint('monitoramento', __name__)

@monitoramento_bp.route("/status_dashboard", methods=["POST"])
def status_dashboard():
    dados = request.json
    config = dados.get('config')
    
    if not config:
        return jsonify({"status": "erro", "message": "Configuração SQL não fornecida"}), 400

    try:
        conn = pyodbc.connect(Config.get_connection_string(config))
        cursor = conn.cursor()
        
        # --- 1. TB_LISTA_PESQUISAS_LOG ---
        cursor.execute("""
            SELECT COUNT(1), MIN(DTHR_PESQUISA), MAX(DTHR_PESQUISA) 
            FROM TB_LISTA_PESQUISAS_LOG WITH (NOLOCK)
        """)
        row_log = cursor.fetchone()
        log_resumo = {
            "tabela": "TB_LISTA_PESQUISAS_LOG",
            "total_registros": row_log[0] if row_log[0] else 0,
            "data_antiga": row_log[1].strftime('%d/%m/%Y %H:%M') if row_log[1] else "N/A",
            "data_recente": row_log[2].strftime('%d/%m/%Y %H:%M') if row_log[2] else "N/A"
        }

        # --- 2. FILA PENDENTE (Script 1) E PROCESSADOS (Script 4) ---
        cursor.execute("SELECT COUNT(1) FROM ADSVC_EXECUTAR WITH (NOLOCK)")
        qtd_pendente = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(1) FROM ADSVC_EXECUTADOS_EXCLUIR WITH (NOLOCK)")
        qtd_processados = cursor.fetchone()[0]

        # --- 3. FILA POR REGRA (Script 3) ---
        cursor.execute("""
            SELECT LEFT(DS_COMANDO1, 15), COUNT(1) 
            FROM ADSVC_EXECUTAR WITH (NOLOCK) 
            GROUP BY LEFT(DS_COMANDO1, 15) 
            ORDER BY COUNT(1) DESC
        """)
        regras = [{"regra": row[0], "qtd": row[1]} for row in cursor.fetchall()]

        # --- 4. PERFORMANCE DOS WORKERS (Scripts 5 ao 15) ---
        # Lista das tabelas de execução para monitorar tempo
        tabelas_exec = [
            'ADSVC_EXECUTANDO', 'ADSVC_EXECUTANDO_MF1', 'ADSVC_EXECUTANDO_MF2', 
            'ADSVC_EXECUTANDO_MF3', 'ADSVC_EXECUTANDO_MF4', 'ADSVC_EXECUTANDO_MF5',
            'ADSVC_EXECUTANDO_LV1', 'ADSVC_EXECUTANDO_LV2', 'ADSVC_EXECUTANDO_LV3', 
            'ADSVC_EXECUTANDO_LV4', 'ADSVC_EXECUTANDO_LV5'
        ]
        
        performance_workers = []
        for t in tabelas_exec:
            # Query que busca o tempo de execução cruzando com os excluídos (conforme scripts 5-15)
            sql_perf = f"""
                SELECT TOP 1 LEFT(DS_COMANDO1, 15), QT_TEMPO_EXEC 
                FROM {t} A WITH (NOLOCK) 
                INNER JOIN ADSVC_EXECUTADOS_EXCLUIR B WITH (NOLOCK) ON A.ID_SVC_EXECUTAR = B.ID_SVC_EXECUTAR 
                ORDER BY QT_TEMPO_EXEC DESC
            """
            try:
                cursor.execute(sql_perf)
                res = cursor.fetchone()
                if res:
                    performance_workers.append({
                        "worker": t.replace('ADSVC_EXECUTANDO_', ''),
                        "regra": res[0],
                        "tempo": res[1]
                    })
            except:
                continue # Pula caso a tabela não exista ou esteja vazia

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