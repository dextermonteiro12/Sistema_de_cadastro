from flask import Blueprint, request, jsonify
import pyodbc
from config import Config

fila_adsvc_bp = Blueprint('fila_adsvc', __name__)

def get_db_connection(config):
    return pyodbc.connect(Config.get_connection_string(config), timeout=5)

@fila_adsvc_bp.route("/api/dashboard/fila-adsvc", methods=["POST"])
def get_fila_data():
    dados = request.json
    config = dados.get('config')
    
    if not config:
        return jsonify({"status": "erro", "message": "Configuração pendente"}), 400

    conn = None
    try:
        conn = get_db_connection(config)
        cursor = conn.cursor()
        
        # Script para Pendentes e Processados
        # Unificamos em um bloco para evitar múltiplas chamadas ao banco
        sql = """
            SELECT 
                (SELECT COUNT(1) FROM ADSVC_EXECUTAR WITH (NOLOCK)) as pendentes,
                (SELECT COUNT(1) FROM ADSVC_EXECUTADOS_EXCLUIR WITH (NOLOCK)) as processados
        """
        
        cursor.execute(sql)
        row = cursor.fetchone()
        
        resultado = {
            "pendentes": row[0] if row[0] is not None else 0,
            "processados": row[1] if row[1] is not None else 0
        }
            
        return jsonify({"status": "ok", "dados": resultado}), 200

    except Exception as e:
        return jsonify({"status": "erro", "erro": str(e)}), 500
    finally:
        if conn:
            conn.close()