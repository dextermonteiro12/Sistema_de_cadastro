import os
import random
from datetime import datetime 
from typing import Dict, Any 

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS 
from faker import Faker

from models import ClienteModel 

# Configuração absoluta do caminho da pasta static para evitar erros no Docker
base_dir = os.path.abspath(os.path.dirname(__file__))
static_folder = os.path.join(base_dir, 'static')

app = Flask(__name__, static_folder=static_folder)
CORS(app)
fake = Faker("pt_BR")

def gerar_registro_pld() -> Dict[str, Any]:
    pais_principal = 'BRASIL' if random.random() > 0.2 else fake.country().upper()[:40]
    estado = fake.state_abbr()
    cidade = fake.city()[:40]

    # Ajuste: garantindo que as datas sejam objetos datetime puros
    dt_const = fake.date_time_between(start_date='-20y', end_date='-5y')
    dt_rel = fake.date_time_between(start_date=dt_const, end_date='-1y')
    
    dados = {
        "CD_CLIENTE": fake.bothify(text='CL????-####').upper(),
        "DE_CLIENTE": fake.name().upper()[:120],
        "CD_TP_CLIENTE": random.choice(["PF", "PJ"]),
        "CIC_CPF": fake.cpf() if random.random() > 0.5 else fake.cnpj(),
        "DS_GRUPO_CLIENTE": random.choice(['VAREJO', 'ALTO VALOR', 'CORPORATE'])[:50],
        "DE_ENDERECO": fake.street_address()[:80],
        "DE_CIDADE": cidade,
        "DE_ESTADO": estado,
        "DE_PAIS": pais_principal,
        "CD_CEP": fake.postcode()[:10],
        "DE_FONE1": fake.numerify(text='###########')[:16],
        "DE_FONE2": fake.numerify(text='###########')[:16],
        "DE_EMAIL": fake.email()[:100],
        "IP_ELETRONICO": fake.ipv4_public()[:104],
        "DE_ENDERECO_RES": fake.street_address()[:80],
        "DE_CIDADE_RES": fake.city()[:40],
        "DE_ESTADO_RES": fake.state_abbr(),
        "DE_PAIS_RES": pais_principal,
        "CD_CEP_RES": fake.postcode()[:10],
        "DE_ENDERECO_CML": fake.street_address()[:80],
        "DE_CIDADE_CML": fake.city()[:40],
        "DE_ESTADO_CML": fake.state_abbr(),
        "DE_PAIS_CML": pais_principal,
        "CD_CEP_CML": fake.postcode()[:10],
        "DT_ABERTURA_REL": dt_rel,
        "DT_DESATIVACAO": datetime.now(),
        "DT_ULT_ALTERACAO": datetime.now(),
        "DT_CONSTITUICAO": dt_const,
        "DS_RAMO_ATV": fake.job()[:80],
        "DE_LINHA_NEGOCIO": random.choice(['VAREJO', 'PME'])[:20],
        "CD_NAIC": fake.bothify(text='NAIC-#####').upper(),
        "CD_NAT_JURIDICA": fake.bothify(text='####'),
        "CD_RISCO": random.randint(1, 5),
        "CD_RISCO_INERENTE": random.randint(1, 5),
        "DE_SIT_CADASTRO": "ATIVO",
        "FL_BLOQUEADO": 0, 
        "FL_FUNDO_INVEST": 0,
        "FL_CLI_EVENTUAL": 0,
        "FL_CADASTRO_PROC": 1,
        "FL_NAO_RESIDENTE": 0,
        "FL_GRANDES_FORTUNAS": 0,
        "FL_RELACIONAMENTO_TERCEIROS": 0,
        "FL_ADMIN_CARTOES": 0,
        "FL_EMPRESA_TRUST": 0,
        "FL_FACILITADORA_PAGTO": 0,
        "FL_EMP_REGULADA": 1,
        "DE_RESPONS_CADASTRO": fake.name()[:60],
        "DE_CONF_CADASTRO": fake.name()[:60],
        "DE_PAIS_SEDE": pais_principal,
    }
    
    # Validação via Pydantic (ClienteModel)
    cliente = ClienteModel(**dados)
    return cliente.model_dump()

# --- ROTAS DE API ---

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "online", "service": "backend-python"}), 200

@app.route("/gerar_dados/<int:quantidade>", methods=["GET"])
def gerar_dados(quantidade):
    if quantidade > 1000: # Aumentei um pouco o limite para teste
        return jsonify({"erro": "Máximo 1000 registros por vez"}), 400
    try:
        dados_gerados = [gerar_registro_pld() for _ in range(quantidade)]
        return jsonify(dados_gerados)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# --- SERVIR FRONTEND ---

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # Tenta servir o arquivo da pasta static
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    # Se não encontrar (ou for a raiz), entrega o index.html do React
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == "__main__":
    # Debug=False para produção (Docker)
    app.run(host='0.0.0.0', port=5000, debug=False)