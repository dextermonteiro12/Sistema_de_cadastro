# Seu código de imports (mantido)
from faker import Faker
from flask import Flask, jsonify
from flask_cors import CORS 
import random
from uuid import uuid4 
# 👇 Você deve garantir que 'ClienteModel' em 'models.py'
#    inclua TODOS os 48 campos do sistema PLD.
from models import ClienteModel 
from datetime import date, datetime 
from typing import Dict, Any 

# Inicializa o Faker para gerar dados em Português do Brasil
fake = Faker("pt_BR")
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def gerar_registro_pld() -> Dict[str, Any]:
    """
    Gera um único registro de cliente PLD, mapeando os 48 campos
    e validando-o com o Pydantic (ClienteModel).
    """

    # --- 1. Geração de Dados Base para Consistência ---
    
    # Dados Geográficos Principais (para usar como Residencial/Comercial também)
    pais_principal = fake.country() if random.random() < 0.2 else 'BRASIL'
    estado_principal = fake.state_abbr()
    cidade_principal = fake.city()
    
    # Datas
    # Usamos datetime.now() para ter uma referência de hora/minuto/segundo
    dt_constituicao = fake.date_time_between(start_date='-20y', end_date='-5y')
    dt_abertura_rel = fake.date_time_between(start_date=dt_constituicao, end_date='-1y')
    dt_ult_alteracao = fake.date_time_between(start_date=dt_abertura_rel, end_date='now')

    # Data de desativação (date_time_between retorna datetime)
    dt_desativacao_obj = fake.date_time_between(start_date=dt_ult_alteracao, end_date='now') \
                         if random.random() < 0.1 else dt_ult_alteracao
    
    # --- 2. Criação do Dicionário de Dados ---
    dados = {
        # --- Identificação e Nome ---
        "CD_CLIENTE": fake.bothify(text='CL????-####'),
        "DE_CLIENTE": fake.name() if random.random() < 0.8 else fake.company(),
        "CD_TP_CLIENTE": 'PF' if random.random() < 0.8 else 'PJ',
        # 👉 Se 'ClienteModel' exigir UUID, você deve incluir um campo com uuid4() aqui
        # Ex: "id_interno": uuid4(),
        
        # --- Documento e Grupo ---
        "CIC_CPF": fake.cpf() if random.random() < 0.8 else fake.cnpj(), # Mais realista para PF/PJ
        "DS_GRUPO_CLIENTE": random.choice(['VAREJO', 'ALTO VALOR', 'CORPORATE', 'GRUPO DE RISCO A']),
        
        # --- Endereço Principal ---
        "DE_ENDERECO": fake.street_address(),
        "DE_CIDADE": cidade_principal,
        "DE_ESTADO": estado_principal,
        "DE_PAIS": pais_principal,
        "CD_CEP": fake.postcode(),
        
        # --- Telefones e E-mail ---
        "DE_FONE1": fake.numerify(text='(##) #####-####'), 
        "DE_FONE2": fake.numerify(text='(##) #####-####'),
        "DE_EMAIL": fake.email(),
        "IP_ELETRONICO": fake.ipv4_public(),
        
        # --- Endereços e CEPs Residencial e Comercial ---
        "DE_ENDERECO_RES": fake.street_address(),
        "DE_CIDADE_RES": fake.city(),
        "DE_ESTADO_RES": fake.state_abbr(),
        "DE_PAIS_RES": pais_principal,
        "CD_CEP_RES": fake.postcode(),
        
        "DE_ENDERECO_CML": fake.street_address(),
        "DE_CIDADE_CML": fake.city(),
        "DE_ESTADO_CML": fake.state_abbr(),
        "DE_PAIS_CML": pais_principal,
        "CD_CEP_CML": fake.postcode(),
        
        # --- Datas (Pydantic deve aceitar objetos 'datetime' nativos) ---
        "DT_ABERTURA_REL": dt_abertura_rel,
        "DT_DESATIVACAO": dt_desativacao_obj,
        "DT_ULT_ALTERACAO": dt_ult_alteracao,
        "DT_CONSTITUICAO": dt_constituicao,

        # --- Profissão/Atividade e Classificação ---
        "DS_RAMO_ATV": fake.job(),
        "DE_LINHA_NEGOCIO": random.choice(['VAREJO', 'INVESTIMENTO', 'PRIVATE', 'PME']),
        "CD_NAIC": fake.bothify(text='NAIC-#####-??'),
        "CD_NAT_JURIDICA": fake.bothify(text='????#'),
        
        # --- Risco e Flags (PLD) ---
        "CD_RISCO": random.randint(1, 5), # smallint
        "CD_RISCO_INERENTE": random.randint(1, 5), # smallint
        "DE_SIT_CADASTRO": random.choice(['ATIVO', 'PENDENTE', 'BLOQUEADO', 'CANCELADO']),
        # Flags (bit) - Pydantic espera Boolean (True/False) ou Inteiro (0/1)
        # Vamos usar 0 e 1, que são compatíveis com o tipo 'bit' do SQL:
        "FL_BLOQUEADO": random.choice([0, 1]), 
        "FL_FUNDO_INVEST": random.choice([0, 1]),
        "FL_CLI_EVENTUAL": random.choice([0, 1]),
        "FL_CADASTRO_PROC": 1,
        "FL_NAO_RESIDENTE": random.choice([0, 0, 0, 1]),
        "FL_GRANDES_FORTUNAS": random.choice([0, 0, 0, 0, 1]),
        "FL_RELACIONAMENTO_TERCEIROS": random.choice([0, 1]),
        "FL_ADMIN_CARTOES": random.choice([0, 1]),
        "FL_EMPRESA_TRUST": random.choice([0, 1]),
        "FL_FACILITADORA_PAGTO": random.choice([0, 1]),
        "FL_EMP_REGULADA": random.choice([0, 1]),
        
        # --- Responsáveis ---
        "DE_RESPONS_CADASTRO": fake.name(),
        "DE_CONF_CADASTRO": fake.name(),
        "DE_PAIS_SEDE": fake.country(),
        
        # --- Dados que estavam no modelo simples, mas talvez não no PLD ---
        # Removidos: "data_nascimento", "profissao", "movimentacao_simulada", "tipo_movimentacao"
        # Mantidos apenas se estiverem no seu ClienteModel PLD.
    }
    
    # --- 3. Cria e valida o modelo ---
    # O Pydantic irá validar se o dicionário 'dados' bate com o 'ClienteModel'
    cliente = ClienteModel(**dados)

    # --- 4. Converte o modelo validado para um dicionário Python (serialização) ---
    # Usando .json() ou .dict() com 'by_alias=True' se usar aliases Pydantic
    return cliente.dict()


# Substitua o nome da função no endpoint
@app.route("/gerar_dados/<int:quantidade>", methods=["GET"])
def gerar_dados(quantidade):
    """Endpoint para gerar 'quantidade' de clientes PLD."""

    if quantidade > 100:
        return (
            jsonify(
                {"erro": "Limite máximo de 100 registros para esta versão de teste."}
            ),
            400,
        )

    # O loop chama a nova função de geração PLD
    dados_gerados = [gerar_registro_pld() for _ in range(quantidade)]

    return jsonify(dados_gerados)

# Mantém a execução principal
if __name__ == "__main__":
    print("Iniciando o Gerador de Dados Fictícios PLD...")
    print("Acesse: http://127.0.0.1:5000/gerar_dados/10 para gerar 10 registros.")
    app.run(debug=True)