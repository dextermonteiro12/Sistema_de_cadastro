from flask import Blueprint, request, jsonify
import pypyodbc as pyodbc
from config import Config
from datetime import datetime

perf_workers_bp = Blueprint('perf_workers', __name__)

def get_db_connection(config):
    return pyodbc.connect(Config.get_connection_string(config), timeout=5)

@perf_workers_bp.route("/api/dashboard/performance-workers", methods=["POST"])
def get_performance_data():
    dados = request.json
    config = dados.get('config')
    
    if not config:
        return jsonify({"status": "erro", "message": "Configuração pendente"}), 400

    conn = None
    try:
        conn = get_db_connection(config)
        cursor = conn.cursor()
        
        # Lista de tabelas de Workers conforme sua solicitação
        # Note que para MF5 e LV5 usei a lógica do seu exemplo (consultando MF4 e LV4 respectivamente)
        workers_map = [
            ('ADSVC_EXECUTANDO', 'ADSVC_EXECUTANDO'),
            ('ADSVC_EXECUTANDO_MF1', 'ADSVC_EXECUTANDO_MF1'),
            ('ADSVC_EXECUTANDO_MF2', 'ADSVC_EXECUTANDO_MF2'),
            ('ADSVC_EXECUTANDO_MF3', 'ADSVC_EXECUTANDO_MF3'),
            ('ADSVC_EXECUTANDO_MF4', 'ADSVC_EXECUTANDO_MF4'),
            ('ADSVC_EXECUTANDO_MF5', 'ADSVC_EXECUTANDO_MF4'), # Conforme seu exemplo
            ('ADSVC_EXECUTANDO_LV1', 'ADSVC_EXECUTANDO_LV1'),
            ('ADSVC_EXECUTANDO_LV2', 'ADSVC_EXECUTANDO_LV2'),
            ('ADSVC_EXECUTANDO_LV3', 'ADSVC_EXECUTANDO_LV3'),
            ('ADSVC_EXECUTANDO_LV4', 'ADSVC_EXECUTANDO_LV4'),
            ('ADSVC_EXECUTANDO_LV5', 'ADSVC_EXECUTANDO_LV4')  # Conforme seu exemplo
        ]
        
        performance_total = []

        for label, table_name in workers_map:
            # Query construída para seguir exatamente sua estrutura de INNER JOIN
            # DS_COMANDO1 vem da tabela A (Worker)
            # QT_TEMPO_EXEC vem da tabela B (Excluir)
            sql = f"""
            SET NOCOUNT ON;
            IF OBJECT_ID('{table_name}', 'U') IS NOT NULL AND OBJECT_ID('ADSVC_EXECUTADOS_EXCLUIR', 'U') IS NOT NULL
            BEGIN
                DECLARE @Sql NVARCHAR(MAX) = '
                SELECT TOP 100 
                    GETDATE() as dt, 
                    ''EXECUTADOS {label}'' as worker, 
                    LEFT(A.DS_COMANDO1, 15) as comando, 
                    B.QT_TEMPO_EXEC as tempo
                FROM {table_name} A WITH (NOLOCK)
                INNER JOIN ADSVC_EXECUTADOS_EXCLUIR B WITH (NOLOCK) ON A.ID_SVC_EXECUTAR = B.ID_SVC_EXECUTAR
                ORDER BY B.QT_TEMPO_EXEC DESC';
                
                EXEC sp_executesql @Sql;
            END
            """
            try:
                cursor.execute(sql)
                if cursor.description:
                    rows = cursor.fetchall()
                    for row in rows:
                        performance_total.append({
                            "data_exec": row[0].strftime('%d/%m/%Y %H:%M:%S') if row[0] else "",
                            "worker": row[1],
                            "exec": row[2],
                            "qtd_tempo": int(row[3]) if row[3] else 0
                        })
                
                # Limpa o cursor para a próxima iteração do loop
                while cursor.nextset():
                    pass
            except Exception as e:
                print(f"Erro ao processar {label}: {str(e)}")
                continue

        # Ordenação global pelo tempo mais lento no topo
        performance_total = sorted(performance_total, key=lambda x: x['qtd_tempo'], reverse=True)

        return jsonify({"status": "ok", "dados": performance_total}), 200

    except Exception as e:
        print(f"ERRO CRÍTICO NO BACKEND: {str(e)}")
        return jsonify({"status": "erro", "erro": str(e)}), 500
    finally:
        if conn: conn.close()