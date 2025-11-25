from faker import Faker
from flask import Flask, jsonify
from flask_cors import CORS # 👈 IMPORTAÇÃO NECESSÁRIA
import random

# Inicializa o Faker para gerar dados em Português do Brasil
fake = Faker('pt_BR')
app = Flask(__name__)

# 👈 HABILITA O CORS PARA PERMITIR REQUISIÇÕES DO FRONTEND
# O parâmetro resources={r"/*": {"origins": "*"}} permite qualquer origem, 
# o que é ideal para desenvolvimento local.
CORS(app, resources={r"/*": {"origins": "*"}})

def gerar_cadastro_ficticio():
    """Gera um único registro de cliente fictício."""
    cliente = {
        "id_cliente": fake.uuid4(),
        "nome": fake.name(),
        "cpf": fake.cpf(), # CPF com estrutura válida, mas fictício
        "data_nascimento": fake.date_of_birth(minimum_age=18, maximum_age=65).isoformat(),
        "profissao": fake.job(),
        "endereco": f"{fake.street_address()}, {fake.city()} - {fake.state_abbr()}",
        "movimentacao_simulada": round(random.uniform(100.0, 50000.0), 2),
        "tipo_movimentacao": random.choice(["Depósito", "Saque", "Transferência", "Pagamento de Boleto"])
    }
    return cliente

@app.route('/gerar_dados/<int:quantidade>', methods=['GET'])
def gerar_dados(quantidade):
    """Endpoint para gerar 'quantidade' de clientes e movimentações."""
    if quantidade > 100:
        return jsonify({"erro": "Limite máximo de 100 registros para esta versão de teste."}), 400
        
    dados_gerados = [gerar_cadastro_ficticio() for _ in range(quantidade)]
    
    return jsonify(dados_gerados)

if __name__ == '__main__':
    print("Iniciando o Gerador de Dados Fictícios...")
    print("Acesse: http://127.0.0.1:5000/gerar_dados/10 para gerar 10 registros.")
    app.run(debug=True)