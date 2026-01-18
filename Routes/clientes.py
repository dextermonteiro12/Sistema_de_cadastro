from flask import Blueprint, request, jsonify
import pypyodbc as pyodbc
import threading
import random
import re
import math
import string
from datetime import datetime, timedelta
from utils import get_connection_string, fake

clientes_bp = Blueprint('clientes', __name__)

def gerar_doc_aleatorio(tamanho):
    """Gera uma string numérica aleatória de tamanho fixo."""
    return ''.join(random.choices(string.digits, k=tamanho))

@clientes_bp.route("/gerar_clientes", methods=["POST"])
def gerar_clientes():
    dados = request.json
    config = dados.get('config')
    total_solicitado = int(dados.get('quantidade', 1))
    custom = dados.get('customizacao', {}) 
    
    # 1. Definição da Proporção (Manual ou Automática 50/50)
    qtd_pf = dados.get('qtd_pf')
    qtd_pj = dados.get('qtd_pj')

    if qtd_pf is not None and qtd_pj is not None:
        limit_pf = int(qtd_pf)
        limit_pj = int(qtd_pj)
        total_final = limit_pf + limit_pj
    else:
        limit_pf = total_solicitado // 2
        limit_pj = total_solicitado - limit_pf
        total_final = total_solicitado

    def worker(cfg, total, p_custom, max_pf, max_pj):
        try:
            conn = pyodbc.connect(get_connection_string(cfg))
            cursor = conn.cursor()
            cursor.fast_executemany = True
            
            TAMANHO_LOTE = 5000 
            ramos_pj = ['Arquitetura', 'Engenharia', 'TI', 'Varejo', 'Industria', 'Consultoria']
            origens_pj = ['REC', 'MAT', 'EXC', 'LEG']
            hoje = datetime.now()
            trinta_dias_atras = hoje - timedelta(days=30)
            data_padrao = datetime(1900, 1, 1)

            documentos_gerados = set()
            conta_pf = 0
            conta_pj = 0

            for i in range(math.ceil(total / TAMANHO_LOTE)):
                lote = []
                while len(lote) < TAMANHO_LOTE and (conta_pf + conta_pj) < total:
                    
                    # Determina se gera PF ou PJ baseado nos limites restantes
                    if conta_pf < max_pf and (conta_pj >= max_pj or random.random() > 0.5):
                        tp_cli = "01"
                        eh_pf = True
                        conta_pf += 1
                    else:
                        tp_cli = "02"
                        eh_pf = False
                        conta_pj += 1

                    # Gerar documento único e aleatório
                    while True:
                        tamanho = 11 if eh_pf else 14
                        doc = gerar_doc_aleatorio(tamanho)
                        if doc not in documentos_gerados:
                            documentos_gerados.add(doc)
                            break

                    # Dados Geográficos e Nomes
                    nome = p_custom.get('DE_CLIENTE') or (fake.name().upper() if eh_pf else (fake.company().upper() + " LTDA"))
                    rua = fake.street_name().upper()
                    cidade = fake.city().upper()
                    estado = fake.state_abbr().upper()
                    cep = re.sub(r'\D', '', fake.postcode())[:8]

                    # Regras de Negócio por Tipo
                    if eh_pf:
                        ds_ramo, dt_constituicao, nat_juridica = "", data_padrao, ""
                    else:
                        ds_ramo = p_custom.get('DS_RAMO_ATV') or random.choice(ramos_pj)
                        dt_constituicao = p_custom.get('DT_CONSTITUICAO') or trinta_dias_atras
                        nat_juridica = p_custom.get('CD_NAT_JURIDICA') or random.choice(origens_pj)

                    registro = (
                        doc, nome[:120], tp_cli, rua[:80], cidade[:40], estado[:2], 'BRASIL',
                        cep, fake.msisdn()[:14], fake.msisdn()[:14], hoje, doc,
                        "PF" if eh_pf else "PJ", rua[:80], cidade[:40], estado[:2], 'BRASIL',
                        cep, rua[:80], cidade[:40], estado[:2], 'BRASIL', cep,
                        p_custom.get('DT_DESATIVACAO', '1900-01-01'),
                        p_custom.get('DT_ULT_ALTERACAO', '1900-01-01'),
                        ds_ramo[:50], int(p_custom.get('FL_FUNDO_INVEST', 0)),
                        int(p_custom.get('FL_CLI_EVENTUAL', 0)),
                        str(p_custom.get('DE_RESPONS_CADASTRO', ''))[:50],
                        str(p_custom.get('DE_CONF_CADASTRO', ''))[:50],
                        int(p_custom.get('CD_RISCO', 0)), str(p_custom.get('CD_NAIC', ''))[:10],
                        str(p_custom.get('DE_LINHA_NEGOCIO', ''))[:50],
                        int(p_custom.get('FL_CADASTRO_PROC', 0)), int(p_custom.get('FL_NAO_RESIDENTE', 1)),
                        int(p_custom.get('FL_GRANDES_FORTUNAS', 1)), 'BRASIL',
                        str(p_custom.get('DE_SIT_CADASTRO', ''))[:20], int(p_custom.get('FL_BLOQUEADO', 0)),
                        int(p_custom.get('CD_RISCO_INERENTE', 3)), dt_constituicao,
                        str(p_custom.get('IP_ELETRONICO', ''))[:15], str(p_custom.get('DE_EMAIL', ''))[:100],
                        int(p_custom.get('FL_RELACIONAMENTO_TERCEIROS', 0)),
                        int(p_custom.get('FL_ADMIN_CARTOES', 0)),
                        int(p_custom.get('FL_EMPRESA_TRUST', 0)),
                        int(p_custom.get('FL_FACILITADORA_PAGTO', 0)),
                        nat_juridica[:5], int(p_custom.get('FL_EMP_REGULADA', 0))
                    )
                    lote.append(registro)

                if lote:
                    sql = f"INSERT INTO TAB_CLIENTES_PLD VALUES ({','.join(['?' for _ in range(49)])})"
                    cursor.executemany(sql, lote)
                    conn.commit()

            documentos_gerados.clear()
            conn.close()
        except Exception as e:
            print(f"Erro na Geração Massiva: {e}")

    threading.Thread(target=worker, args=(config, total_final, custom, limit_pf, limit_pj)).start()
    return jsonify({
        "status": "ok", 
        "message": f"Iniciada geração de {total_final} registros ({limit_pf} PF / {limit_pj} PJ)."
    }), 200