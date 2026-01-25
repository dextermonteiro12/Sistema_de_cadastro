import uuid
import random
from datetime import datetime
from utils import fake, gerar_data_pld 

def executar_carga(cursor, versao, clientes, data_ref, gerar_data_pld_func, modo_data, qtd_solicitada):
    tabela_destino = "TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD"
    TAMANHO_LOTE_BANCO = 50000 
    
    print(f"--- DEBUG INTERMEDIADOR ({versao}) ---")
    
    if not clientes:
        print("❌ Erro: A lista 'clientes' está vazia.")
        return

    if len(clientes[0]) < 3:
        print("❌ Erro: Query incompleta. Requer CD_CLIENTE, DE_CLIENTE, CD_TP_CLIENTE.")
        return

    clientes_pj = [c for c in clientes if str(c[2]).strip() == "02"]
    print(f"🔍 Clientes Tipo '02' encontrados: {len(clientes_pj)}")

    if not clientes_pj:
        print("⚠️ Abortando: Nenhum cliente PJ encontrado.")
        return

    colunas = [
        "CD_IDENTIFICACAO", "CD_CLIENTE", "DT_MOVIMENTA", "NR_ORDEMPAGAMENTO",
        "DT_PAGAMENTO", "CPF_CNPJ", "DE_CLIENTE", "TP_DOC", "DE_MOEDA",
        "VL_ME", "VL_USD", "VL_CONTABIL_MN", "VL_FECHAMENTOVENDA_MN", "VL_GIRO",
        "DS_SITUACAO", "TP_MOVIMENTACAO", "DE_ORIGINADOR", "TP_DOCUMENTOORIGINADOR",
        "CPF_CNPJ_ORIGINADOR", "DE_PAISORIGINADOR", "DE_FAVORECIDO", "TP_DOCUMENTOFAVORECIDO",
        "CPF_CNPJ_FAVORECIDO", "DE_PAISFAVORECIDO", "DE_DETALHESPAGAMENTO", "TP_CONTACORRENTE", "DE_ORIGEM"
    ]

    sql = f"INSERT INTO {tabela_destino} ({', '.join(colunas)}) VALUES ({', '.join(['?' for _ in colunas])})"
    
    lote = []
    # Definimos os tipos fixos para garantir a duplicidade por cliente
    tipos_obrigatorios = ['DebitoRemessa', 'OrdemDePagamento']
    opcoes_favorecido = ['Netflix', 'Microsoft', 'Spotify']
    opcoes_pais_fav = ['USA', 'Canada', 'Italia']

    print(f"🚀 Iniciando inserção (Regra: 2 transações por cliente)...")

    try:
        for cli in clientes_pj:
            cd_cliente_atual = str(cli[0]).strip()
            de_cliente_atual = str(cli[1]).strip()
            
            # Criamos uma transação para cada tipo na lista tipos_obrigatorios
            for tipo_mov in tipos_obrigatorios:
                dt_mov = gerar_data_pld_func(modo_data, data_ref)
                vl_brl = round(random.uniform(1000, 5000), 2)
                
                dados = (
                    str(uuid.uuid4())[:40],               # CD_IDENTIFICACAO
                    cd_cliente_atual,                     # CD_CLIENTE
                    dt_mov,                               # DT_MOVIMENTA
                    str(random.randint(100000, 999999)),  # NR_ORDEMPAGAMENTO
                    dt_mov,                               # DT_PAGAMENTO
                    cd_cliente_atual,                     # CPF_CNPJ
                    de_cliente_atual,                     # DE_CLIENTE
                    "CNPJ",                               # TP_DOC
                    "DOLAR AMERICANO",                    # DE_MOEDA
                    round(vl_brl/5.3, 2),                 # VL_ME
                    round(vl_brl/5.3, 2),                 # VL_USD
                    vl_brl,                               # VL_CONTABIL_MN
                    vl_brl,                               # VL_FECHAMENTOVENDA_MN
                    0.0,                                  # VL_GIRO
                    "LIQUIDADA",                          # DS_SITUACAO
                    tipo_mov,                             # TP_MOVIMENTACAO (Garante um de cada)
                    fake.name().upper()[:120],            # DE_ORIGINADOR
                    "CPF",                                # TP_DOCUMENTOORIGINADOR
                    fake.cpf(),                           # CPF_CNPJ_ORIGINADOR
                    "Brasil",                             # DE_PAISORIGINADOR
                    random.choice(opcoes_favorecido),     # DE_FAVORECIDO
                    "CNPJ",                               # TP_DOCUMENTOFAVORECIDO
                    "",                                   # CPF_CNPJ_FAVORECIDO
                    random.choice(opcoes_pais_fav),       # DE_PAISFAVORECIDO
                    "PAGTO SERVICOS",                     # DE_DETALHESPAGAMENTO
                    "CONTA CORRENTE",                     # TP_CONTACORRENTE
                    1                                     # DE_ORIGEM
                )
                lote.append(dados)

                if len(lote) >= TAMANHO_LOTE_BANCO:
                    cursor.executemany(sql, lote)
                    lote = []
                    print(f"✔️ Lote de {TAMANHO_LOTE_BANCO} enviado.")

        if lote:
            cursor.executemany(sql, lote)
            print(f"✅ Finalizado! Total de {len(clientes_pj) * 2} registros processados.")
            
    except Exception as e:
        print(f"❌ Erro durante o INSERT: {e}")