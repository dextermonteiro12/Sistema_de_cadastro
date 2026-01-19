import os
import sys

# Garante que o diretório raiz está no path do Python
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS

# 1. Importação dos Blueprints
from Routes.clientes import clientes_bp
from Routes.movimentacoes import movimentacoes_bp
from Routes.ambiente import ambiente_bp
from Routes.monitoramento import monitoramento_bp
from Routes.auth import auth_bp
from Routes.home import home_bp
from Routes.dashboard.tb_fila_adsvc import fila_adsvc_bp
from Routes.dashboard.tb_performance_workers import perf_workers_bp



# --- NOVA IMPORTAÇÃO DO MÓDULO MODULAR ---
from Routes.dashboard.tb_pesquisas_log import log_pesquisas_bp

# 2. Inicialização do App
app = Flask(__name__, static_folder='static')
CORS(app)

# 3. Registro dos Blueprints no objeto 'app'
app.register_blueprint(clientes_bp)
app.register_blueprint(movimentacoes_bp)
app.register_blueprint(ambiente_bp)
app.register_blueprint(monitoramento_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(home_bp)

# --- REGISTRO DO NOVO MÓDULO ---
app.register_blueprint(log_pesquisas_bp)
app.register_blueprint(fila_adsvc_bp)
app.register_blueprint(perf_workers_bp)

# 4. Configuração de Rotas para o Frontend (React)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)