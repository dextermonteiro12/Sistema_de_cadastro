import os
import sys

# Garante que o diretório raiz está no path do Python para evitar erros de importação
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS

# ---------------------------------------------------------
# 1. Importação dos Blueprints
# ---------------------------------------------------------
from Routes.clientes import clientes_bp
from Routes.movimentacoes import movimentacoes_bp
from Routes.ambiente import ambiente_bp
from Routes.monitoramento import monitoramento_bp
from Routes.auth import auth_bp
from Routes.home import home_bp

# Módulos de Dashboard e Monitoramento Detalhado
from Routes.dashboard.tb_fila_adsvc import fila_adsvc_bp
from Routes.dashboard.tb_performance_workers import perf_workers_bp
from Routes.dashboard.tb_pesquisas_log import log_pesquisas_bp

# ---------------------------------------------------------
# 2. Inicialização do App
# ---------------------------------------------------------
app = Flask(__name__, static_folder='static')
CORS(app) # Habilita acesso do Frontend React

# ---------------------------------------------------------
# 3. Registro dos Blueprints
# ---------------------------------------------------------
# Rotas principais de funcionalidade
app.register_blueprint(clientes_bp)
app.register_blueprint(movimentacoes_bp)
app.register_blueprint(ambiente_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(home_bp)

# Rotas de monitoramento e análise de dados
app.register_blueprint(monitoramento_bp) # Rota geral (/status_dashboard)
app.register_blueprint(log_pesquisas_bp)  # Logs detalhados
app.register_blueprint(fila_adsvc_bp)     # Monitoramento da fila ADSVC
app.register_blueprint(perf_workers_bp)   # Gráficos de performance

# ---------------------------------------------------------
# 4. Configuração de Roteamento para Single Page Application (SPA)
# ---------------------------------------------------------
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """
    Esta função serve o Frontend React. Se o arquivo solicitado existir 
    (como .js ou .css), ele o entrega. Caso contrário, retorna o index.html 
    para o React Router assumir o controle.
    """
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

# ---------------------------------------------------------
# 5. Execução do Servidor
# ---------------------------------------------------------
if __name__ == "__main__":
    # Escuta em todas as interfaces na porta 5000
    app.run(host='0.0.0.0', port=5000, debug=True)