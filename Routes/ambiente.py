from flask import Blueprint, request, jsonify
import pyodbc
from config import Config

ambiente_bp = Blueprint('ambiente', __name__)

def detectar_versao_sistema(cursor):
    """
    Identifica se a base é V8 ou V9 consultando a tabela AD_SISTEMAS_VERSOES.
    """
    try:
        cursor.execute("SELECT TOP 1 CD_VERSAO FROM AD_SISTEMAS_VERSOES WITH (NOLOCK) ORDER BY 1 DESC")
        row = cursor.fetchone()
        if row:
            cd_versao = str(row[0])
            return "V9" if "009" in cd_versao else "V8"
        return "V8"
    except Exception:
        return "V8"

@ambiente_bp.route("/check_ambiente", methods=["POST"])
def check_ambiente():
    config = request.json.get('config')
    try:
        conn = pyodbc.connect(Config.get_connection_string(config), timeout=10)
        cursor = conn.cursor()
        
        versao_sistema = detectar_versao_sistema(cursor)
        
        # Nomes PADRONIZADOS (Unificados para ambas as versões)
        tabelas_alvo = [
            'TAB_CLIENTES_PLD', 
            'TAB_CLIENTES_MOVFIN_PLD', 
            'TAB_CLIENTES_MOVFIN_ME_PLD', 
            'TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD',
            "TAB_CLIENTES_CO_TIT_PLD"
        ]
        
        status_tabs = {}
        for t in tabelas_alvo:
            cursor.execute(f"SELECT COUNT(*) FROM sys.tables WITH (NOLOCK) WHERE name = '{t}'")
            status_tabs[t] = "Criada" if cursor.fetchone()[0] == 1 else "Ausente"
            
        cursor.close()
        conn.close()
        
        return jsonify({
            "status": "ok", 
            "tabelas": status_tabs, 
            "versao": versao_sistema
        }), 200
    except Exception as e:
        return jsonify({"status": "erro", "erro": str(e)}), 500

@ambiente_bp.route("/setup_ambiente", methods=["POST"])
def setup_ambiente():
    dados = request.json
    config = dados.get('config')
    versao = dados.get('versao') 
    
    # --- SCRIPTS V8 (Nomes Padrão) ---
    scripts_v8 = {
        "CLIENTES": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_PLD' AND xtype='U')
            CREATE TABLE TAB_CLIENTES_PLD (
                CD_CLIENTE char(20) PRIMARY KEY, DE_CLIENTE varchar(120), CD_TP_CLIENTE char(2), DE_ENDERECO varchar(80), 
                DE_CIDADE varchar(40), DE_ESTADO char(2), DE_PAIS varchar(40), CD_CEP varchar(10), DE_ENDERECO_RES varchar(80), 
                DE_CIDADE_RES varchar(40), DE_ESTADO_RES char(2), DE_PAIS_RES varchar(40), CD_CEP_RES varchar(10), 
                DE_ENDERECO_CML varchar(80), DE_CIDADE_CML varchar(40), DE_ESTADO_CML char(2), DE_PAIS_CML varchar(40), 
                CD_CEP_CML varchar(10), DE_FONE1 varchar(14), DE_FONE2 varchar(14), DT_ABERTURA_REL datetime, CIC_CPF varchar(20), 
                DS_GRUPO_CLIENTE varchar(50), DT_DESATIVACAO datetime, DT_ULT_ALTERACAO datetime, DS_RAMO_ATV varchar(80), 
                FL_FUNDO_INVEST bit, FL_CLI_EVENTUAL bit, DE_RESPONS_CADASTRO varchar(60), DE_CONF_CADASTRO varchar(60), 
                CD_RISCO smallint, CD_NAIC varchar(20), DE_LINHA_NEGOCIO varchar(20), FL_CADASTRO_PROC bit, 
                FL_NAO_RESIDENTE bit, FL_GRANDES_FORTUNAS bit, DT_CONSTITUICAO datetime, DE_PAIS_SEDE varchar(40), 
                DE_SIT_CADASTRO varchar(40), FL_BLOQUEADO bit, CD_RISCO_INERENTE smallint, IP_ELETRONICO varchar(104), 
                DE_EMAIL varchar(100), FL_RELACIONAMENTO_TERCEIROS bit, FL_ADMIN_CARTOES bit, FL_EMPRESA_TRUST bit, 
                FL_FACILITADORA_PAGTO bit, CD_NAT_JURIDICA varchar(5), FL_EMP_REGULADA bit
            )""",
        "MOVFIN": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_MOVFIN_PLD' AND xtype='U')
            CREATE TABLE TAB_CLIENTES_MOVFIN_PLD (CD_IDENTIFICACAO varchar(40) PRIMARY KEY, CD_VEIC_LEGAL smallint, CD_AGENCIA char(10), CD_AGENCIA_MOVTO char(10), CD_CONTA varchar(50), CD_CLIENTE varchar(20), DT_MOVIMENTA datetime, DTHR_MOVIMENTA datetime, CD_MOEDA varchar(10), VL_OPERACAO money, TP_DEB_CRED char(1), CD_FORMA varchar(20), DE_CONTRAPARTE varchar(120), DE_BANCO_CONTRA varchar(60), DE_AGENCIA_CONTRA varchar(60), CD_CONTA_CONTRA varchar(50), CD_PAIS_CONTRA varchar(40), DE_ORIGEM_OPE varchar(40), CD_PRODUTO varchar(20), DE_FINALIDADE varchar(400), CPF_CNPJ_CONTRA varchar(20), DS_CIDADE_CONTRA varchar(60), DS_COMP_HISTORICO varchar(50), VL_RENDIMENTO money, DT_PREV_LIQUIDACAO datetime, CD_ISPB_EMISSOR int, NR_CHEQUE varchar(20), DE_TP_DOCTO_CONTRA varchar(40), NR_DOCTO_CONTRA varchar(50), DE_EXECUTOR varchar(60), CPF_EXECUTOR varchar(20), NR_PASSAPORTE_EXEC varchar(20), FL_IOF_CARENCIA bit, CD_NAT_OPERACAO varchar(20), DE_ORDENANTE varchar(120), UF_MOVTO char(2), NR_POS varchar(20), DS_CIDADE_POS varchar(60), DS_CANAL varchar(15), DS_ORIGEM_RECURSO varchar(40), DS_DESTINO_RECURSO varchar(40), CD_PROVISIONAMENTO varchar(40), DS_AMBIENTE_NEG varchar(20))""",
        "MOVFIN_ME": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_MOVFIN_ME_PLD' AND xtype='U')
            CREATE TABLE TAB_CLIENTES_MOVFIN_ME_PLD (CD_IDENTIFICACAO varchar(40) PRIMARY KEY, CD_VEIC_LEGAL smallint, CD_AGENCIA char(10), CD_CONTA varchar(50), CD_CLIENTE varchar(20), DT_MOVIMENTA datetime, DTHR_MOVIMENTA datetime, CD_MOEDA_ME varchar(10), VL_OPERACAO_ME money, TX_COTACAO_ME money, VL_OPERACAO_USD money, TP_DEB_CRED char(1), CD_FORMA varchar(20), DE_CONTRAPARTE varchar(120), CD_BIC_BANCO_CONTRA varchar(20), DE_BANCO_CONTRA varchar(60), DE_AGENCIA_CONTRA varchar(60), CD_CONTA_CONTRA varchar(50), CD_PAIS_CONTRA varchar(40), DE_ORIGEM_OPE varchar(40), CD_PRODUTO char(20), DE_FINALIDADE varchar(60), CPF_CNPJ_CONTRA varchar(20), DS_CIDADE_CONTRA varchar(60), DS_COMP_HISTORICO varchar(50), DE_TP_DOCTO_CONTRA varchar(40), NR_DOCTO_CONTRA varchar(50), DE_EXECUTOR varchar(60), CPF_EXECUTOR varchar(20), NR_PASSAPORTE_EXEC varchar(20), CD_NAT_OPERACAO varchar(20), DE_ORDENANTE varchar(120), UF_MOVTO char(2), DE_OPERADOR varchar(60), TX_PTAX float)""",
        "MOVFIN_INT": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD' AND xtype='U')
            CREATE TABLE TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD (CD_IDENTIFICACAO char(40) PRIMARY KEY, CD_CLIENTE varchar(20), DT_MOVIMENTA datetime, NR_ORDEMPAGAMENTO varchar(10), DT_PAGAMENTO datetime, CPF_CNPJ char(20), DE_CLIENTE varchar(120), TP_DOC varchar(20), DE_MOEDA varchar(50), VL_ME money, VL_USD money, VL_CONTABIL_MN money, VL_FECHAMENTOVENDA_MN money, VL_GIRO money, DS_SITUACAO varchar(40), TP_MOVIMENTACAO varchar(40), DE_ORIGINADOR varchar(120), TP_DOCUMENTOORIGINADOR varchar(40), CPF_CNPJ_ORIGINADOR varchar(20), DE_PAISORIGINADOR varchar(50), DE_FAVORECIDO varchar(120), TP_DOCUMENTOFAVORECIDO varchar(40), CPF_CNPJ_FAVORECIDO varchar(20), DE_PAISFAVORECIDO varchar(50), DE_DETALHESPAGAMENTO varchar(1000), TP_CONTACORRENTE varchar(40), DE_ORIGEM smallint)""",
        "CO_TIT": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_CO_TIT_PLD' AND xtype='U')
            CREATE TABLE TAB_CLIENTES_CO_TIT_PLD (CD_CLIENTE CHAR(20) NOT NULL,DE_NOME_CO VARCHAR(120) NOT NULL,DE_END_CO VARCHAR(80) NOT NULL, DE_CID_CO VARCHAR(40) NOT NULL, CD_UF VARCHAR(2) NOT NULL, DE_PAIS_CO VARCHAR(40) NOT NULL, CD_CEP_CO VARCHAR(10) NOT NULL, DE_FONE1_CO VARCHAR(14) NOT NULL, DE_FONE2_CO VARCHAR(14) NOT NULL, RG VARCHAR(15) NOT NULL, RG_EMISSOR VARCHAR(20) NOT NULL, CPF VARCHAR(15) NOT NULL, NM_PAI VARCHAR(60) NOT NULL, NM_MAE VARCHAR(60) NOT NULL, NM_CONJUGE VARCHAR(60) NOT NULL, NACIONALIDADE VARCHAR(20) NOT NULL,    DT_NASCIMENTO DATETIME NOT NULL, SEXO CHAR(1) NOT NULL, DS_PROFISSAO VARCHAR(80) NOT NULL, CD_TP_CLIENTE CHAR(2) NOT NULL, CNPJ VARCHAR(20) NOT NULL, DS_RAMO_ATV VARCHAR(80) NOT NULL, DS_CARGO VARCHAR(80) NOT NULL, FL_EST_CIVIL CHAR(1) NOT NULL, DE_ATV_PRINCIPAL VARCHAR(80) NOT NULL, DE_FORMA_CONSTITUICAO VARCHAR(50) NOT NULL, DT_CONSTITUICAO DATETIME NOT NULL, FL_PEP BIT NOT NULL, FL_CO_TIT_FINAL BIT NOT NULL, TX_PARTICIPACAO FLOAT NOT NULL, DE_PAIS_DOMICILIO VARCHAR(40) NOT NULL, DE_PAIS_NASCIMENTO VARCHAR(40) NOT NULL, DE_NATUREZA VARCHAR(40) NOT NULL, DE_SIT_CADASTRO VARCHAR(40) NOT NULL, DT_INICIO_RELACIONAMENTO DATETIME NOT NULL, DT_FIM_RELACIONAMENTO DATETIME NOT NULL, FL_SERVIDOR_PUBLICO BIT NOT NULL)"""
    }

    # --- SCRIPTS V9 (Nomes Padronizados da V8 + Campos da V9) ---
    scripts_v9 = {
        "CLIENTES": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_PLD' AND xtype='U')
            CREATE TABLE TAB_CLIENTES_PLD (
                CD_CLIENTE char(20) PRIMARY KEY, DE_CLIENTE varchar(120), CD_TP_CLIENTE char(2), DE_ENDERECO varchar(80), 
                DE_CIDADE varchar(40), DE_ESTADO char(2), DE_PAIS varchar(40), CD_CEP varchar(10), DE_FONE1 varchar(14), 
                DE_FONE2 varchar(14), DT_ABERTURA_REL datetime, CIC_CPF varchar(20), DS_GRUPO_CLIENTE varchar(50), 
                DE_ENDERECO_RES varchar(80), DE_CIDADE_RES varchar(40), DE_ESTADO_RES char(2), DE_PAIS_RES varchar(40), 
                CD_CEP_RES varchar(10), DE_ENDERECO_CML varchar(80), DE_CIDADE_CML varchar(40), DE_ESTADO_CML char(2), 
                DE_PAIS_CML varchar(40), CD_CEP_CML varchar(10), DT_DESATIVACAO datetime, DT_ULT_ALTERACAO datetime, 
                DS_RAMO_ATV varchar(80), FL_FUNDO_INVEST bit, FL_CLI_EVENTUAL bit, DE_RESPONS_CADASTRO varchar(60), 
                DE_CONF_CADASTRO varchar(60), CD_RISCO smallint, CD_NAIC varchar(20), DE_LINHA_NEGOCIO varchar(20), 
                FL_CADASTRO_PROC bit, FL_NAO_RESIDENTE bit, FL_GRANDES_FORTUNAS bit, DE_PAIS_SEDE varchar(40), 
                DE_SIT_CADASTRO varchar(40), FL_BLOQUEADO bit, CD_RISCO_INERENTE smallint, DT_CONSTITUICAO datetime, 
                IP_ELETRONICO varchar(104), DE_EMAIL varchar(100), FL_RELACIONAMENTO_TERCEIROS bit, FL_ADMIN_CARTOES bit, 
                FL_EMPRESA_TRUST bit, FL_FACILITADORA_PAGTO bit, CD_NAT_JURIDICA varchar(5), FL_EMP_REGULADA bit, 
                DE_PAIS_DOMICILIO_FISCAL varchar(40), DE_PAIS_CONTROLE_ACIONARIO varchar(40), CD_ORIGEM_RECURSOS smallint, 
                ID_TITULARIDADE int, DS_CANAL varchar(25)
            )""",
        "MOVFIN": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_MOVFIN_PLD' AND xtype='U')
            CREATE TABLE TAB_CLIENTES_MOVFIN_PLD (
                CD_IDENTIFICACAO varchar(40) PRIMARY KEY, CD_VEIC_LEGAL smallint, CD_AGENCIA char(10), CD_AGENCIA_MOVTO char(10), 
                CD_CONTA varchar(50), CD_CLIENTE varchar(20), DT_MOVIMENTA datetime, DTHR_MOVIMENTA datetime, CD_MOEDA varchar(10), 
                VL_OPERACAO money, TP_DEB_CRED char(1), CD_FORMA varchar(20), DE_CONTRAPARTE varchar(120), DE_BANCO_CONTRA varchar(60), 
                DE_AGENCIA_CONTRA varchar(60), CD_CONTA_CONTRA varchar(50), CD_PAIS_CONTRA varchar(40), DE_ORIGEM_OPE varchar(40), 
                CD_PRODUTO varchar(20), DE_FINALIDADE varchar(400), CPF_CNPJ_CONTRA varchar(20), DS_CIDADE_CONTRA varchar(60), 
                DS_COMP_HISTORICO varchar(300), VL_RENDIMENTO money, DT_PREV_LIQUIDACAO datetime, CD_ISPB_EMISSOR int, 
                NR_CHEQUE varchar(20), DE_TP_DOCTO_CONTRA varchar(40), NR_DOCTO_CONTRA varchar(50), DE_EXECUTOR varchar(60), 
                CPF_EXECUTOR varchar(20), NR_PASSAPORTE_EXEC varchar(20), FL_IOF_CARENCIA bit, CD_NAT_OPERACAO varchar(20), 
                DE_ORDENANTE varchar(120), UF_MOVTO char(2), NR_POS varchar(20), DS_CIDADE_POS varchar(60), DS_CANAL varchar(15), 
                DS_ORIGEM_RECURSO varchar(40), DS_DESTINO_RECURSO varchar(40), CD_PROVISIONAMENTO varchar(40), DS_AMBIENTE_NEG varchar(20), 
                CD_COMPRA varchar(50) -- CAMPO EXCLUSIVO V9
            )""",
        "MOVFIN_ME": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_MOVFIN_ME_PLD' AND xtype='U')
            CREATE TABLE TAB_CLIENTES_MOVFIN_ME_PLD (CD_IDENTIFICACAO varchar(40) PRIMARY KEY, CD_VEIC_LEGAL smallint, CD_AGENCIA char(10), CD_CONTA varchar(50), CD_CLIENTE varchar(20), DT_MOVIMENTA datetime, DTHR_MOVIMENTA datetime, CD_MOEDA_ME varchar(10), VL_OPERACAO_ME money, TX_COTACAO_ME money, VL_OPERACAO_USD money, TP_DEB_CRED char(1), CD_FORMA varchar(20), DE_CONTRAPARTE varchar(120), CD_BIC_BANCO_CONTRA varchar(20), DE_BANCO_CONTRA varchar(60), DE_AGENCIA_CONTRA varchar(60), CD_CONTA_CONTRA varchar(50), CD_PAIS_CONTRA varchar(40), DE_ORIGEM_OPE varchar(40), CD_PRODUTO char(20), DE_FINALIDADE varchar(60), CPF_CNPJ_CONTRA varchar(20), DS_CIDADE_CONTRA varchar(60), DS_COMP_HISTORICO varchar(50), DE_TP_DOCTO_CONTRA varchar(40), NR_DOCTO_CONTRA varchar(50), DE_EXECUTOR varchar(60), CPF_EXECUTOR varchar(20), NR_PASSAPORTE_EXEC varchar(20), CD_NAT_OPERACAO varchar(20), DE_ORDENANTE varchar(120), UF_MOVTO char(2), DE_OPERADOR varchar(60), TX_PTAX float)""",
        "MOVFIN_INT": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD' AND xtype='U')
            CREATE TABLE TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD (CD_IDENTIFICACAO char(40) PRIMARY KEY, CD_CLIENTE varchar(20), DT_MOVIMENTA datetime, NR_ORDEMPAGAMENTO varchar(10), DT_PAGAMENTO datetime, CPF_CNPJ char(20), DE_CLIENTE varchar(120), TP_DOC varchar(20), DE_MOEDA varchar(50), VL_ME money, VL_USD money, VL_CONTABIL_MN money, VL_FECHAMENTOVENDA_MN money, VL_GIRO money, DS_SITUACAO varchar(40), TP_MOVIMENTACAO varchar(40), DE_ORIGINADOR varchar(120), TP_DOCUMENTOORIGINADOR varchar(40), CPF_CNPJ_ORIGINADOR varchar(20), DE_PAISORIGINADOR varchar(50), DE_FAVORECIDO varchar(120), TP_DOCUMENTOFAVORECIDO varchar(40), CPF_CNPJ_FAVORECIDO varchar(20), DE_PAISFAVORECIDO varchar(50), DE_DETALHESPAGAMENTO varchar(1000), TP_CONTACORRENTE varchar(40), DE_ORIGEM smallint)""",
        "CO_TIT": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_CO_TIT_PLD' AND xtype='U')
            CREATE TABLE TAB_CLIENTES_CO_TIT_PLD (CD_CLIENTE CHAR(20) NOT NULL,DE_NOME_CO VARCHAR(120) NOT NULL,DE_END_CO VARCHAR(80) NOT NULL, DE_CID_CO VARCHAR(40) NOT NULL, CD_UF VARCHAR(2) NOT NULL, DE_PAIS_CO VARCHAR(40) NOT NULL, CD_CEP_CO VARCHAR(10) NOT NULL, DE_FONE1_CO VARCHAR(14) NOT NULL, DE_FONE2_CO VARCHAR(14) NOT NULL, RG VARCHAR(15) NOT NULL, RG_EMISSOR VARCHAR(20) NOT NULL, CPF VARCHAR(15) NOT NULL, NM_PAI VARCHAR(60) NOT NULL, NM_MAE VARCHAR(60) NOT NULL, NM_CONJUGE VARCHAR(60) NOT NULL, NACIONALIDADE VARCHAR(20) NOT NULL,    DT_NASCIMENTO DATETIME NOT NULL, SEXO CHAR(1) NOT NULL, DS_PROFISSAO VARCHAR(80) NOT NULL, CD_TP_CLIENTE CHAR(2) NOT NULL, CNPJ VARCHAR(20) NOT NULL, DS_RAMO_ATV VARCHAR(80) NOT NULL, DS_CARGO VARCHAR(80) NOT NULL, FL_EST_CIVIL CHAR(1) NOT NULL, DE_ATV_PRINCIPAL VARCHAR(80) NOT NULL, DE_FORMA_CONSTITUICAO VARCHAR(50) NOT NULL, DT_CONSTITUICAO DATETIME NOT NULL, FL_PEP BIT NOT NULL, FL_CO_TIT_FINAL BIT NOT NULL, TX_PARTICIPACAO FLOAT NOT NULL, DE_PAIS_DOMICILIO VARCHAR(40) NOT NULL, DE_PAIS_NASCIMENTO VARCHAR(40) NOT NULL, DE_NATUREZA VARCHAR(40) NOT NULL, DE_SIT_CADASTRO VARCHAR(40) NOT NULL, DT_INICIO_RELACIONAMENTO DATETIME NOT NULL, DT_FIM_RELACIONAMENTO DATETIME NOT NULL, FL_SERVIDOR_PUBLICO BIT NOT NULL,DE_PAIS_DOMICILIO_FISCAL VARCHAR(40) NOT NULL, DE_PAIS_CONTROLE_ACIONARIO VARCHAR(40) NOT NULL, DE_PAIS_SEDE VARCHAR(40) NOT NULL,CD_RISCO SMALLINT NOT NULL)"""
    }

    try:
        conn = pyodbc.connect(Config.get_connection_string(config))
        cursor = conn.cursor()
        
        if not versao:
            versao = detectar_versao_sistema(cursor)

        selected_scripts = scripts_v9 if versao == "V9" else scripts_v8

        for nome, sql in selected_scripts.items():
            cursor.execute(sql)
            conn.commit()
                
        cursor.close()
        conn.close()
        return jsonify({"status": "ok", "message": f"Estrutura {versao} configurada com nomes padronizados!"}), 200
    except Exception as e:
        return jsonify({"status": "erro", "erro": str(e)}), 500