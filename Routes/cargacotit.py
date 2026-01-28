from flask import Blueprint, request, jsonify
import pyodbc
import threading
import random
import re
from datetime import datetime, timedelta
from utils import get_connection_string, fake 

cargacotit_bp = Blueprint('cargacotit', __name__)

def gerar_cpf_fake():
    return re.sub(r'\D', '', fake.cpf())[:11]

def gerar_rg_fake():
    return ''.join(random.choices("0123456789", k=9))

@cargacotit_bp.route("/executar_carga_cotit", methods=["POST"])
def executar_carga_cotit():
    dados = request.json
    config = dados.get('config')
    versao_sistema = config.get('versao', 'V8')

    def worker_carga(cfg, versao):
        try:
            conn = pyodbc.connect(get_connection_string(cfg))
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM TAB_CLIENTES_CO_TIT_PLD")
            conn.commit()

            # Busca Titulares e o Tipo (01 ou 02)
            cursor.execute("SELECT CD_CLIENTE, DE_CLIENTE, CD_TP_CLIENTE FROM TAB_CLIENTES_PLD")
            clientes = cursor.fetchall()

            hoje = datetime.now()
            
            colunas = [
                "CD_CLIENTE", "DE_NOME_CO", "DE_END_CO", "DE_CID_CO", "CD_UF", "DE_PAIS_CO",
                "CD_CEP_CO", "DE_FONE1_CO", "DE_FONE2_CO", "RG", "RG_EMISSOR", "CPF",
                "NM_PAI", "NM_MAE", "NM_CONJUGE", "NACIONALIDADE", "DT_NASCIMENTO", "SEXO",
                "DS_PROFISSAO", "CD_TP_CLIENTE", "CNPJ", "DS_RAMO_ATV", "DS_CARGO", "FL_EST_CIVIL",
                "DE_ATV_PRINCIPAL", "DE_FORMA_CONSTITUICAO", "DT_CONSTITUICAO", "FL_PEP",
                "FL_CO_TIT_FINAL", "TX_PARTICIPACAO", "DE_PAIS_DOMICILIO", "DE_PAIS_NASCIMENTO",
                "DE_NATUREZA", "DE_SIT_CADASTRO", "DT_INICIO_RELACIONAMENTO", "DT_FIM_RELACIONAMENTO",
                "FL_SERVIDOR_PUBLICO"
            ]

            if versao == "V9":
                colunas.extend(["DE_PAIS_DOMICILIO_FISCAL", "DE_PAIS_CONTROLE_ACIONARIO", "DE_PAIS_SEDE", "CD_RISCO"])

            sql_insert = f"INSERT INTO TAB_CLIENTES_CO_TIT_PLD ({', '.join(colunas)}) VALUES ({', '.join(['?' for _ in colunas])})"

            lote = []
            for cli in clientes:
                cd_titular_original = str(cli.CD_CLIENTE).strip() 
                nome_titular_original = cli.DE_CLIENTE
                tp_cliente = str(cli.CD_TP_CLIENTE).strip()

                # Define a quantidade de loops baseada no tipo de cliente
                # PF (01) -> 1 registro | PJ (02) -> 3 registros
                iteracoes = 1 if tp_cliente == '01' else 3

                for i in range(iteracoes):
                    # Se for PF, o único registro é o real. Se for PJ, todos são fictícios.
                    is_real_titular = (tp_cliente == '01')
                    
                    sexo = random.choice(['M', 'F'])
                    cpf_final = cd_titular_original if is_real_titular else gerar_cpf_fake()
                    
                    # DE_NOME_CO: Nome real do titular (PF) ou Nome Fictício Real (PJ) sem títulos
                    nome_final = nome_titular_original if is_real_titular else fake.name().upper()

                    registro = [
                        cd_titular_original,
                        nome_final[:120],
                        fake.street_name().upper()[:80],
                        fake.city().upper()[:40],
                        fake.state_abbr().upper(),
                        'BRASIL',
                        re.sub(r'\D', '', fake.postcode())[:8],
                        fake.msisdn()[:14],
                        fake.msisdn()[:14],
                        gerar_rg_fake(),
                        "SSP",
                        cpf_final,
                        fake.name_male().upper()[:60],
                        fake.name_female().upper()[:60],
                        fake.name().upper() if random.random() > 0.5 else "",
                        "BRASILEIRA",
                        hoje - timedelta(days=random.randint(7000, 20000)),
                        sexo,
                        "EMPRESARIO" if tp_cliente == '02' else "ANALISTA",
                        "01", # Co-titular/Sócio sempre entra como PF
                        "", 
                        "OUTROS",
                        "SOCIO" if tp_cliente == '02' else "TITULAR",
                        random.choice(['S', 'C', 'D']),
                        "ATIVIDADE PRINCIPAL",
                        "OUTROS",
                        hoje - timedelta(days=3650),
                        0,
                        1 if is_real_titular else 0, # FL_CO_TIT_FINAL (1 para o titular PF real)
                        100.0 if is_real_titular else 0.0,
                        "BRASIL", "BRASIL", "PESSOA FISICA", "ATIVO",
                        hoje - timedelta(days=180),
                        hoje + timedelta(days=365),
                        0
                    ]

                    if versao == "V9":
                        registro.extend(["BRASIL", "BRASIL", "BRASIL", 1])

                    lote.append(tuple(registro))

                    if len(lote) >= 1000:
                        cursor.executemany(sql_insert, lote)
                        conn.commit()
                        lote = []

            if lote:
                cursor.executemany(sql_insert, lote)
                conn.commit()

            conn.close()
        except Exception as e:
            print(f"Erro Crítico Carga: {e}")

    threading.Thread(target=worker_carga, args=(config, versao_sistema)).start()
    return jsonify({"status": "ok", "message": "Carga CO_TIT iniciada com sucesso."}), 200