import uuid
import random
from datetime import datetime
from utils import fake

def executar_carga(cursor, versao, clientes, data_ref, gerar_data_pld, modo_data, qtd_solicitada):
    tabela = "TAB_CLIENTES_MOVFIN_PLD"
    
    # Configuração de performance: Lote de 50.000 registros
    TAMANHO_LOTE_BANCO = 50000 
    
    # Definição das colunas base conforme as listas revisadas
    colunas = [
        "CD_IDENTIFICACAO", "CD_VEIC_LEGAL", "CD_AGENCIA", "CD_AGENCIA_MOVTO",
        "CD_CONTA", "CD_CLIENTE", "DT_MOVIMENTA", "DTHR_MOVIMENTA", "CD_MOEDA",
        "VL_OPERACAO", "TP_DEB_CRED", "CD_FORMA", "DE_CONTRAPARTE", "DE_BANCO_CONTRA",
        "DE_AGENCIA_CONTRA", "CD_CONTA_CONTRA", "CD_PAIS_CONTRA", "DE_ORIGEM_OPE",
        "CD_PRODUTO", "DE_FINALIDADE", "CPF_CNPJ_CONTRA", "DS_CIDADE_CONTRA",
        "DS_COMP_HISTORICO", "VL_RENDIMENTO", "DT_PREV_LIQUIDACAO", "CD_ISPB_EMISSOR",
        "NR_CHEQUE", "DE_TP_DOCTO_CONTRA", "NR_DOCTO_CONTRA", "DE_EXECUTOR",
        "CPF_EXECUTOR", "NR_PASSAPORTE_EXEC", "FL_IOF_CARENCIA", "DE_ORDENANTE",
        "UF_MOVTO"
    ]

    # Ajuste de estrutura e ordem por versão
    if versao == "V8":
        colunas.extend(["NR_POS", "DS_CIDADE_POS", "DS_CANAL", "DS_ORIGEM_RECURSO", 
                        "DS_DESTINO_RECURSO", "CD_PROVISIONAMENTO", "DS_AMBIENTE_NEG", 
                        "CD_NAT_OPERACAO"])
    else:
        colunas.extend(["CD_NAT_OPERACAO", "NR_POS", "DS_CIDADE_POS", "DS_CANAL", 
                        "DS_ORIGEM_RECURSO", "DS_DESTINO_RECURSO", "CD_PROVISIONAMENTO", 
                        "DS_AMBIENTE_NEG", "CD_COMPRA"])

    sql = f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES ({', '.join(['?' for _ in colunas])})"
    
    # Listas de Aleatoriedade solicitadas
    lista_formas = ['Pix', 'TED', 'DOC', 'TEC', 'Boletos', 'Cheques']
    lista_produtos = ['Conta de Depósito', 'Cartão de Crédito', 'Crédito Pessoal', 'Financiamento', 'PIX', 'TED', 'DOC']
    lista_nat_operacao = ['10000', '12407', '40000']
    
    lote = []
    vezes = int(qtd_solicitada) if qtd_solicitada else 1
    
    for cli in clientes:
        id_cliente_real = str(cli[0])[:20]
        for _ in range(vezes):
            for natureza in ['C', 'D']:
                dt_final = gerar_data_pld(modo_data, data_ref)
                dthr = datetime.combine(dt_final, datetime.now().time())
                
                # Dados Base
                dados = [
                    str(uuid.uuid4())[:40], 1, "0001", "0001", "12345-6",
                    id_cliente_real, dt_final, dthr, "BRL",
                    round(random.uniform(100, 5000), 2), natureza,
                    random.choice(lista_formas),            # Aleatório
                    fake.name().upper()[:120], "BANCO X", "0001", "12345",
                    "BRASIL", "SISTEMA", 
                    random.choice(lista_produtos),          # Aleatório
                    "PAGAMENTO", "000.000.000-00", "SAO PAULO",
                    "CARGA ALEATORIA", 0, dt_final, 12345678, "0", "DOC", "0",
                    "EXECUTOR", "000.000.000-00", "0", 0,
                    fake.name().upper()[:120], "SP"
                ]
                
                if versao == "V8":
                    dados.extend(["POS01", "SAO PAULO", "WEB", "RECURSO", "DESTINO", "PROV01", "VIRTUAL", random.choice(lista_nat_operacao)])
                else:
                    dados.extend([random.choice(lista_nat_operacao), "POS01", "SAO PAULO", "WEB", "RECURSO", "DESTINO", "PROV01", "VIRTUAL", f"CMP-{random.randint(100,999)}"])

                lote.append(tuple(dados))

                # Controle de Lote de 50.000
                if len(lote) >= TAMANHO_LOTE_BANCO:
                    cursor.executemany(sql, lote)
                    lote = []
                    print(f"📦 Lote de {TAMANHO_LOTE_BANCO} registros processado.")

    # Envia registros restantes
    if lote: 
        cursor.executemany(sql, lote)
        print(f"📦 Lote final de {len(lote)} registros processado.")