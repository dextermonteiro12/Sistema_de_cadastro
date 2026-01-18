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
        
        # Lista das tabelas que queremos monitorar
        tabelas = [
            'TAB_CLIENTES_PLD', 
            'TAB_CLIENTES_MOVFIN_PLD', 
            'TAB_CLIENTES_MOVFIN_ME_PLD', 
            'TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD'
        ]
        
        resumo = []
        
        for t in tabelas:
            # Query que verifica se a tabela existe e conta os registros
            sql = f"""
                IF OBJECT_ID('{t}', 'U') IS NOT NULL 
                    SELECT COUNT(*) FROM {t}
                ELSE 
                    SELECT -1
            """
            cursor.execute(sql)
            total = cursor.fetchone()[0]
            
            resumo.append({
                "tabela": t,
                "status": "Ativa" if total != -1 else "Não Criada",
                "total_registros": total if total != -1 else 0
            })
            
        conn.close()
        return jsonify({
            "status": "ok", 
            "servidor": config.get('servidor'),
            "banco": config.get('banco'),
            "dados": resumo
        }), 200

    except Exception as e:
        return jsonify({"status": "erro", "erro": str(e)}), 500