import uuid
import random
from datetime import datetime
from utils import fake, gerar_data_pld 

def executar_carga(cursor, versao, clientes, data_ref, gerar_data_pld_func, modo_data, qtd_solicitada):
    tabela = "TAB_CLIENTES_MOVFIN_ME_PLD"
    TAMANHO_LOTE_BANCO = 50000 
    
    # 1. Definição das colunas base (comuns a ambas as versões até DE_ORDENANTE)
    colunas_base = [
        "CD_IDENTIFICACAO", "CD_VEIC_LEGAL", "CD_AGENCIA", "CD_CONTA", "CD_CLIENTE",
        "DT_MOVIMENTA", "DTHR_MOVIMENTA", "CD_MOEDA_ME", "VL_OPERACAO_ME", "TX_COTACAO_ME",
        "VL_OPERACAO_USD", "TP_DEB_CRED", "CD_FORMA", "DE_CONTRAPARTE", "DE_BANCO_CONTRA",
        "DE_AGENCIA_CONTRA", "CD_CONTA_CONTRA", "CD_PAIS_CONTRA", "DE_ORIGEM_OPE", "CD_PRODUTO",
        "DE_FINALIDADE", "CPF_CNPJ_CONTRA", "DS_CIDADE_CONTRA", "DS_COMP_HISTORICO", "DE_TP_DOCTO_CONTRA",
        "NR_DOCTO_CONTRA", "DE_EXECUTOR", "CPF_EXECUTOR", "NR_PASSAPORTE_EXEC", "DE_ORDENANTE"
    ]

    # 2. Ajuste da ordem final conforme a versão (V8 vs V9)
    if versao == 'V9':
        colunas_final = ["CD_NAT_OPERACAO", "UF_MOVTO", "DE_OPERADOR", "TX_PTAX"]
    else: # Default V8
        colunas_final = ["UF_MOVTO", "DE_OPERADOR", "TX_PTAX", "CD_NAT_OPERACAO"]

    colunas = colunas_base + colunas_final
    sql = f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES ({', '.join(['?' for _ in colunas])})"
    
    # Listas de apoio
    lista_formas = ['Pix', 'TED', 'DOC', 'TEC', 'Boletos', 'Cheques']
    lista_produtos = ['CONTA DEPOSITO', 'CARTAO CREDITO', 'CAMBIO', 'TED', 'PIX']
    lista_moedas = ["USD", "EUR", "GBP"]
    lista_nat_operacao = ['10000', '12407', '40000']
    
    lote = []
    vezes = int(qtd_solicitada) if qtd_solicitada else 1
    hora_atual = datetime.now().time()

    for cli in clientes:
        id_cliente_real = str(cli[0])[:20]
        for _ in range(vezes):
            for natureza in ['C', 'D']:
                dt_final = gerar_data_pld_func(modo_data, data_ref)
                dthr = datetime.combine(dt_final, hora_atual)
                
                moeda = random.choice(lista_moedas)
                vl_me = round(random.uniform(500, 10000), 2)
                cotacao = round(random.uniform(5.0, 6.0), 4)
                vl_usd = round(vl_me if moeda == "USD" else (vl_me * 1.1), 2)
                
                # Dados Base (Comum)
                dados_lista = [
                    str(uuid.uuid4())[:40], 1, "0001", "ME-9988-X", id_cliente_real,
                    dt_final, dthr, moeda, vl_me, cotacao, vl_usd, natureza,
                    random.choice(lista_formas), fake.company().upper()[:120],
                    "INTER BANK CORP", "AG-LONDON-01", "ACC-776655", "GBR",
                    "CAMBIO_ONLINE", random.choice(lista_produtos), "PAGAMENTO_INVOICE",
                    id_cliente_real, "LONDRES", "LIQ_CAMBIO_ME", "INVOICE",
                    str(random.randint(5000, 8000)), fake.name().upper()[:120],
                    "00000000000", "N/A", fake.company().upper()[:120]
                ]

                # Dados Finais (Ordem variável)
                val_uf = "SP"
                val_operador = "OPERADOR_AUTO"
                val_ptax = cotacao
                val_nat = random.choice(lista_nat_operacao)

                if versao == 'V9':
                    dados_lista.extend([val_nat, val_uf, val_operador, val_ptax])
                else:
                    dados_lista.extend([val_uf, val_operador, val_ptax, val_nat])

                lote.append(tuple(dados_lista))

                if len(lote) >= TAMANHO_LOTE_BANCO:
                    cursor.executemany(sql, lote)
                    lote = []
                    print(f"📦 Lote ME ({versao}) de {TAMANHO_LOTE_BANCO} registros processado.")

    if lote:
        cursor.executemany(sql, lote)
        print(f"📦 Lote final ME ({versao}) de {len(lote)} registros processado.")