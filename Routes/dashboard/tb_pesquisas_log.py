from flask import Blueprint, request, jsonify
import pypyodbc as pyodbc
from config import Config

log_pesquisas_bp = Blueprint('log_pesquisas', __name__)

def get_db_connection(config):
    return pyodbc.connect(Config.get_connection_string(config), timeout=5)

@log_pesquisas_bp.route("/api/dashboard/log-pesquisas", methods=["POST"])
def get_log_pesquisas_data():
    dados = request.json
    config = dados.get('config')
    
    if not config:
        return jsonify({"status": "erro", "message": "Configuração SQL pendente"}), 400

    conn = None
    try:
        conn = get_db_connection(config)
        cursor = conn.cursor()
        
        tabela = 'TB_LISTA_PESQUISAS_LOG'
        
        # Query otimizada
        sql = f"""
            IF OBJECT_ID('{tabela}', 'U') IS NOT NULL
                SELECT COUNT(1), MIN(DTHR_PESQUISA), MAX(DTHR_PESQUISA) FROM {tabela} WITH (NOLOCK)
            ELSE
                SELECT -1, NULL, NULL
        """
        
        cursor.execute(sql)
        row = cursor.fetchone()

        if not row:
            return jsonify({"status": "ok", "dados": {"total": 0, "data_inicio": "---", "data_fim": "---"}})

        total = row[0]
        
        # Formatação segura das datas
        # Verificamos se row[1] (mín) e row[2] (máx) existem antes de dar .strftime
        dt_inicio = row[1].strftime('%d/%m/%Y %H:%M') if (row[1] and hasattr(row[1], 'strftime')) else "---"
        dt_fim = row[2].strftime('%d/%m/%Y %H:%M') if (row[2] and hasattr(row[2], 'strftime')) else "---"
        
        resultado = {
            "total": total if total != -1 else 0,
            "data_inicio": dt_inicio,
            "data_fim": dt_fim,
            "status": "Ativa" if total != -1 else "Não encontrada"
        }
            
        return jsonify({"status": "ok", "dados": resultado}), 200

    except Exception as e:
        print(f"❌ Erro SQL: {str(e)}")
        return jsonify({"status": "erro", "erro": str(e)}), 500
        
    finally:
        if conn:
            conn.close()