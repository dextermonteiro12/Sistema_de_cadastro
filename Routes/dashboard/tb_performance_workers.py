from flask import Blueprint, request, jsonify
import pyodbc
from config import Config
from datetime import datetime

perf_workers_bp = Blueprint('perf_workers', __name__)

def get_db_connection(config):
    # Timeout reduzido para não travar o dashboard se o banco estiver sob carga extrema
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
        
        # Mapeamento dos workers conforme sua estrutura
        # Mantive a lógica onde MF5 e LV5 consultam a base da MF4/LV4
        workers_map = [
            ('PRINCIPAL', 'ADSVC_EXECUTANDO'),
            ('MF1', 'ADSVC_EXECUTANDO_MF1'),
            ('MF2', 'ADSVC_EXECUTANDO_MF2'),
            ('MF3', 'ADSVC_EXECUTANDO_MF3'),
            ('MF4', 'ADSVC_EXECUTANDO_MF4'),
            ('MF5', 'ADSVC_EXECUTANDO_MF4'), 
            ('LV1', 'ADSVC_EXECUTANDO_LV1'),
            ('LV2', 'ADSVC_EXECUTANDO_LV2'),
            ('LV3', 'ADSVC_EXECUTANDO_LV3'),
            ('LV4', 'ADSVC_EXECUTANDO_LV4'),
            ('LV5', 'ADSVC_EXECUTANDO_LV4')
        ]
        
        performance_total = []

        for label, table_name in workers_map:
            # SQL otimizado com verificações de existência e NOLOCK
            # Retornamos o TOP 50 de cada worker para não sobrecarregar o JSON
            sql = f"""
            SET NOCOUNT ON;
            IF OBJECT_ID('{table_name}', 'U') IS NOT NULL AND OBJECT_ID('ADSVC_EXECUTADOS_EXCLUIR', 'U') IS NOT NULL
            BEGIN
                SELECT TOP 50
                    B.DTHR_EXCLUSAO as dt, 
                    '{label}' as worker, 
                    LEFT(A.DS_COMANDO1, 30) as comando, 
                    B.QT_TEMPO_EXEC as tempo
                FROM {table_name} A WITH (NOLOCK)
                INNER JOIN ADSVC_EXECUTADOS_EXCLUIR B WITH (NOLOCK) ON A.ID_SVC_EXECUTAR = B.ID_SVC_EXECUTAR
                ORDER BY B.DTHR_EXCLUSAO DESC;
            END
            """
            try:
                cursor.execute(sql)
                
                # Coleta os resultados desta tabela
                rows = cursor.fetchall()
                if rows:
                    for row in rows:
                        performance_total.append({
                            "data_exec": row[0].strftime('%d/%m %H:%M:%S') if row[0] else "",
                            "worker": row[1],
                            "exec": row[2].strip() if row[2] else "---",
                            "qtd_tempo": int(row[3]) if row[3] else 0
                        })
                
                # Importante: consome sets vazios para liberar o cursor para a próxima tabela
                while cursor.nextset():
                    pass

            except Exception as e:
                # Log de erro interno (opcional) sem interromper o loop global
                print(f"Aviso: Tabela {table_name} ignorada ou erro na consulta: {str(e)}")
                continue

        # Ordenação Global: Os mais lentos (latência alta) ficam no topo
        performance_total = sorted(performance_total, key=lambda x: x['qtd_tempo'], reverse=True)

        # Retornamos os dados no formato que o React espera: { status: "ok", dados: [...] }
        return jsonify({
            "status": "ok", 
            "dados": performance_total[:100] # Limitamos aos top 100 totais para performance do Front
        }), 200

    except Exception as e:
        return jsonify({"status": "erro", "erro": str(e)}), 500
    finally:
        if conn: 
            conn.close()