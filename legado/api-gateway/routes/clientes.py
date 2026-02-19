from flask import Blueprint, request, jsonify
import pyodbc
import threading
import random
import re
import math
import string
import time
from datetime import datetime, timedelta
from utils import get_connection_string, fake

clientes_bp = Blueprint('clientes', __name__)

def gerar_doc_aleatorio(tamanho):
    return ''.join(random.choices(string.digits, k=tamanho))

@clientes_bp.route("/gerar_clientes", methods=["POST"])
def gerar_clientes():
    dados = request.json
    config = dados.get('config', {})
    versao_sistema = config.get('versao', 'V8')
    
    total_solicitado = int(dados.get('quantidade', 1))
    custom = dados.get('customizacao', {}) 
    
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

    def worker(cfg, total, p_custom, max_pf, max_pj, versao):
        try:
            conn = pyodbc.connect(get_connection_string(cfg))
            cursor = conn.cursor()
            
            # TAMANHO_LOTE reduzido para 2000 em cargas massivas para evitar estouro de timeout/lock
            TAMANHO_LOTE = 2000 
            ramos_pj = ['Arquitetura', 'Engenharia', 'TI', 'Varejo', 'Industria', 'Consultoria']
            origens_pj = ['REC', 'MAT', 'EXC', 'LEG']
            hoje = datetime.now()
            data_padrao = datetime(1900, 1, 1)

            conta_pf = 0
            conta_pj = 0

            # Definição das colunas base (Comuns V8 e V9)
            colunas_base = [
                "CD_CLIENTE", "DE_CLIENTE", "CD_TP_CLIENTE", "DE_ENDERECO", "DE_CIDADE", "DE_ESTADO", "DE_PAIS",
                "CD_CEP", "DE_FONE1", "DE_FONE2", "DT_ABERTURA_REL", "CIC_CPF", "DS_GRUPO_CLIENTE", 
                "DE_ENDERECO_RES", "DE_CIDADE_RES", "DE_ESTADO_RES", "DE_PAIS_RES", "CD_CEP_RES", 
                "DE_ENDERECO_CML", "DE_CIDADE_CML", "DE_ESTADO_CML", "DE_PAIS_CML", "CD_CEP_CML",
                "DT_DESATIVACAO", "DT_ULT_ALTERACAO", "DS_RAMO_ATV", "FL_FUNDO_INVEST", "FL_CLI_EVENTUAL",
                "DE_RESPONS_CADASTRO", "DE_CONF_CADASTRO", "CD_RISCO", "CD_NAIC", "DE_LINHA_NEGOCIO",
                "FL_CADASTRO_PROC", "FL_NAO_RESIDENTE", "FL_GRANDES_FORTUNAS", "DE_PAIS_SEDE",
                "DE_SIT_CADASTRO", "FL_BLOQUEADO", "CD_RISCO_INERENTE", "DT_CONSTITUICAO",
                "IP_ELETRONICO", "DE_EMAIL", "FL_RELACIONAMENTO_TERCEIROS", "FL_ADMIN_CARTOES",
                "FL_EMPRESA_TRUST", "FL_FACILITADORA_PAGTO", "CD_NAT_JURIDICA", "FL_EMP_REGULADA"
            ]

            if versao == "V9":
                colunas_base.extend([
                    "DE_PAIS_DOMICILIO_FISCAL", "DE_PAIS_CONTROLE_ACIONARIO", 
                    "CD_ORIGEM_RECURSOS", "ID_TITULARIDADE", "DS_CANAL"
                ])

            # Construção do SQL Seguro (Anti-Duplicidade)
            cols_str = ", ".join(colunas_base)
            params_str = ", ".join(["?" for _ in colunas_base])
            sql_final = f"""
                INSERT INTO TAB_CLIENTES_PLD ({cols_str})
                SELECT {params_str}
                WHERE NOT EXISTS (SELECT 1 FROM TAB_CLIENTES_PLD WITH (NOLOCK) WHERE CD_CLIENTE = ?)
            """

            for i in range(math.ceil(total / TAMANHO_LOTE)):
                lote = []
                while len(lote) < TAMANHO_LOTE and (conta_pf + conta_pj) < total:
                    
                    if conta_pf < max_pf and (conta_pj >= max_pj or random.random() > 0.5):
                        tp_cli, eh_pf = "01", True
                        conta_pf += 1
                    else:
                        tp_cli, eh_pf = "02", False
                        conta_pj += 1

                    doc = gerar_doc_aleatorio(11 if eh_pf else 14)
                    nome = p_custom.get('DE_CLIENTE') or (fake.name().upper() if eh_pf else (fake.company().upper() + " LTDA"))
                    
                    # Lógica de Ramo/Data baseada no tipo
                    ds_ramo = p_custom.get('DS_RAMO_ATV') or (random.choice(ramos_pj) if not eh_pf else "")
                    dt_constituicao = p_custom.get('DT_CONSTITUICAO') or (hoje - timedelta(days=random.randint(365, 3650)))
                    nat_juridica = p_custom.get('CD_NAT_JURIDICA') or (random.choice(origens_pj) if not eh_pf else "0000")

                    # Registro Base
                    registro = [
                        doc, nome[:120], tp_cli, fake.street_name().upper()[:80], fake.city().upper()[:40], 
                        fake.state_abbr().upper()[:2], 'BRASIL', re.sub(r'\D', '', fake.postcode())[:8],
                        fake.msisdn()[:14], fake.msisdn()[:14], hoje, doc, "PF" if eh_pf else "PJ",
                        "RUA TESTE"[:80], "CIDADE TESTE"[:40], "SP", "BRASIL", "00000000",
                        "RUA CML"[:80], "CIDADE CML"[:40], "SP", "BRASIL", "00000000",
                        data_padrao, data_padrao, ds_ramo[:80], 
                        int(p_custom.get('FL_FUNDO_INVEST', 0)), int(p_custom.get('FL_CLI_EVENTUAL', 0)),
                        "SISTEMA", "SISTEMA", int(p_custom.get('CD_RISCO', 1)), "0000", "GERAL",
                        0, 0, 0, 'BRASIL', 'ATIVO', 0, 1, dt_constituicao,
                        "127.0.0.1", f"contato{doc}@teste.com", 0, 0, 0, 0, nat_juridica[:5], 0
                    ]

                    if versao == "V9":
                        registro.extend(['BRASIL', 'BRASIL', 1, 1, 'AUTOMATICO'])

                    # Adiciona o parâmetro extra para o WHERE NOT EXISTS (CD_CLIENTE)
                    registro.append(doc)
                    lote.append(tuple(registro))

                if lote:
                    try:
                        cursor.executemany(sql_final, lote)
                        conn.commit()
                        # Pequeno alívio para o processador em cargas massivas
                        time.sleep(0.01) 
                    except Exception as e_lote:
                        print(f"Erro no lote: {e_lote}")
                        conn.rollback()

            conn.close()
        except Exception as e:
            print(f"Erro Crítico na Geração: {e}")

    threading.Thread(target=worker, args=(config, total_final, custom, limit_pf, limit_pj, versao_sistema)).start()
    return jsonify({
        "status": "ok", 
        "message": f"Processo iniciado: {total_final} registros no layout {versao_sistema}."
    }), 200