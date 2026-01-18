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
from Routes.auth import auth_bp  # <--- Nova importação para o Login


# 2. Inicialização do App
app = Flask(__name__, static_folder='static')
CORS(app)

# 3. Registro dos Blueprints no objeto 'app'
app.register_blueprint(clientes_bp)
app.register_blueprint(movimentacoes_bp)
app.register_blueprint(ambiente_bp)
app.register_blueprint(monitoramento_bp)
app.register_blueprint(auth_bp) # <--- Registro da rota de Login


# 4. Configuração de Rotas para o Frontend (React)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # Verifica se o arquivo existe na pasta static (css, js, imagens)
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    # Caso contrário, serve o index.html para o React Router
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
    