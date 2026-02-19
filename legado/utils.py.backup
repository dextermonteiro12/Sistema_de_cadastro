import random
from faker import Faker
from datetime import datetime, timedelta # Adicionado timedelta

fake = Faker("pt_BR")

def gerar_cpf_limpo():
    n = [random.randint(0, 9) for _ in range(9)]
    for _ in range(2):
        d = sum(x * y for x, y in zip(n, range(len(n) + 1, 1, -1))) % 11
        n.append(11 - d if d > 1 else 0)
    return "".join(map(str, n))

def get_connection_string(config):
    driver = "{ODBC Driver 17 for SQL Server}"
    return (f"DRIVER={driver};SERVER={config['servidor']};DATABASE={config['banco']};"
            f"UID={config['usuario']};PWD={config['senha']};ConnectTimeout=10;TrustServerCertificate=yes;")

# Mova a função para cá
def gerar_data_pld(modo, data_referencia_base):
    hoje = datetime.now().date()
    if modo == 'mes_atual':
        dia = random.randint(1, hoje.day) if hoje.day > 1 else 1
        return hoje.replace(day=dia)
    elif modo == 'mes_anterior':
        primeiro_dia_mes_atual = hoje.replace(day=1)
        ultimo_dia_mes_anterior = primeiro_dia_mes_atual - timedelta(days=1)
        dia = random.randint(1, ultimo_dia_mes_anterior.day)
        return ultimo_dia_mes_anterior.replace(day=dia)
    return data_referencia_base