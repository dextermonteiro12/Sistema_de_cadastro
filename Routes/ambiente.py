from flask import Blueprint, request, jsonify
import pypyodbc as pyodbc
from config import Config

ambiente_bp = Blueprint('ambiente', __name__)

@ambiente_bp.route("/check_ambiente", methods=["POST"])
def check_ambiente():
    config = request.json.get('config')
    try:
        conn = pyodbc.connect(Config.get_connection_string(config))
        cursor = conn.cursor()
        
        tabelas = [
            'TAB_CLIENTES_PLD', 
            'TAB_CLIENTES_MOVFIN_PLD', 
            'TAB_CLIENTES_MOVFIN_ME_PLD', 
            'TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD'
        ]
        
        status_tabs = {}
        for t in tabelas:
            cursor.execute(f"SELECT CASE WHEN OBJECT_ID('{t}', 'U') IS NOT NULL THEN 1 ELSE 0 END")
            status_tabs[t] = "Criada" if cursor.fetchone()[0] == 1 else "Ausente"
            
        conn.close()
        return jsonify({"status": "ok", "tabelas": status_tabs}), 200
    except Exception as e:
        return jsonify({"status": "erro", "erro": str(e)}), 500

@ambiente_bp.route("/setup_ambiente", methods=["POST"])
def setup_ambiente():
    config = request.json.get('config')
    
    # Scripts SQL centralizados
    # Scripts SQL completos para garantir a integridade dos dados
    scripts = {
        "CLIENTES": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_PLD' AND xtype='U')
            CREATE TABLE TAB_CLIENTES_PLD (CD_CLIENTE char(20) PRIMARY KEY, DE_CLIENTE varchar(120), CD_TP_CLIENTE char(2), DE_ENDERECO varchar(80), DE_CIDADE varchar(40), DE_ESTADO char(2), DE_PAIS varchar(40), CD_CEP varchar(10), DE_FONE1 varchar(14), DE_FONE2 varchar(14), DT_ABERTURA_REL datetime, CIC_CPF varchar(20), DS_GRUPO_CLIENTE varchar(50), DE_ENDERECO_RES varchar(80), DE_CIDADE_RES varchar(40), DE_ESTADO_RES char(2), DE_PAIS_RES varchar(40), CD_CEP_RES varchar(10), DE_ENDERECO_CML varchar(80), DE_CIDADE_CML varchar(40), DE_ESTADO_CML char(2), DE_PAIS_CML varchar(40), CD_CEP_CML varchar(10), DT_DESATIVACAO datetime, DT_ULT_ALTERACAO datetime, DS_RAMO_ATV varchar(80), FL_FUNDO_INVEST bit, FL_CLI_EVENTUAL bit, DE_RESPONS_CADASTRO varchar(60), DE_CONF_CADASTRO varchar(60), CD_RISCO smallint, CD_NAIC varchar(20), DE_LINHA_NEGOCIO varchar(20), FL_CADASTRO_PROC bit, FL_NAO_RESIDENTE bit, FL_GRANDES_FORTUNAS bit, DE_PAIS_SEDE varchar(40), DE_SIT_CADASTRO varchar(40), FL_BLOQUEADO bit, CD_RISCO_INERENTE smallint, DT_CONSTITUICAO datetime, IP_ELETRONICO varchar(104), DE_EMAIL varchar(100), FL_RELACIONAMENTO_TERCEIROS bit, FL_ADMIN_CARTOES bit, FL_EMPRESA_TRUST bit, FL_FACILITADORA_PAGTO bit, CD_NAT_JURIDICA varchar(5), FL_EMP_REGULADA bit)""",
        
        "MOVFIN": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_MOVFIN_PLD' AND xtype='U')
            CREATE TABLE TAB_CLIENTES_MOVFIN_PLD (CD_IDENTIFICACAO varchar(40) PRIMARY KEY, CD_VEIC_LEGAL smallint, CD_AGENCIA char(10), CD_AGENCIA_MOVTO char(10), CD_CONTA varchar(50), CD_CLIENTE varchar(20), DT_MOVIMENTA datetime, DTHR_MOVIMENTA datetime, CD_MOEDA varchar(10), VL_OPERACAO money, TP_DEB_CRED char(1), CD_FORMA varchar(20), DE_CONTRAPARTE varchar(120), DE_BANCO_CONTRA varchar(60), DE_AGENCIA_CONTRA varchar(60), CD_CONTA_CONTRA varchar(50), CD_PAIS_CONTRA varchar(40), DE_ORIGEM_OPE varchar(40), CD_PRODUTO varchar(20), DE_FINALIDADE varchar(400), CPF_CNPJ_CONTRA varchar(20), DS_CIDADE_CONTRA varchar(60), DS_COMP_HISTORICO varchar(50), VL_RENDIMENTO money, DT_PREV_LIQUIDACAO datetime, CD_ISPB_EMISSOR int, NR_CHEQUE varchar(20), DE_TP_DOCTO_CONTRA varchar(40), NR_DOCTO_CONTRA varchar(50), DE_EXECUTOR varchar(60), CPF_EXECUTOR varchar(20), NR_PASSAPORTE_EXEC varchar(20), FL_IOF_CARENCIA bit, CD_NAT_OPERACAO varchar(20), DE_ORDENANTE varchar(120), UF_MOVTO char(2), NR_POS varchar(20), DS_CIDADE_POS varchar(60), DS_CANAL varchar(15), DS_ORIGEM_RECURSO varchar(40), DS_DESTINO_RECURSO varchar(40), CD_PROVISIONAMENTO varchar(40), DS_AMBIENTE_NEG varchar(20))""",
        
        "MOVFIN_ME": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_MOVFIN_ME_PLD' AND xtype='U')
            CREATE TABLE [dbo].[TAB_CLIENTES_MOVFIN_ME_PLD](
                [CD_IDENTIFICACAO] [varchar](40) NOT NULL,
                [CD_VEIC_LEGAL] [smallint] NOT NULL,
                [CD_AGENCIA] [char](10) NOT NULL,
                [CD_CONTA] [varchar](50) NOT NULL,
                [CD_CLIENTE] [varchar](20) NOT NULL,
                [DT_MOVIMENTA] [datetime] NOT NULL,
                [DTHR_MOVIMENTA] [datetime] NOT NULL,
                [CD_MOEDA_ME] [varchar](10) NOT NULL,
                [VL_OPERACAO_ME] [money] NOT NULL,
                [TX_COTACAO_ME] [money] NOT NULL,
                [VL_OPERACAO_USD] [money] NOT NULL,
                [TP_DEB_CRED] [char](1) NOT NULL,
                [CD_FORMA] [varchar](20) NOT NULL,
                [DE_CONTRAPARTE] [varchar](120) NOT NULL,
                [CD_BIC_BANCO_CONTRA] [varchar](20) NOT NULL,
                [DE_BANCO_CONTRA] [varchar](60) NOT NULL,
                [DE_AGENCIA_CONTRA] [varchar](60) NOT NULL,
                [CD_CONTA_CONTRA] [varchar](50) NOT NULL,
                [CD_PAIS_CONTRA] [varchar](40) NOT NULL,
                [DE_ORIGEM_OPE] [varchar](40) NOT NULL,
                [CD_PRODUTO] [char](20) NOT NULL,
                [DE_FINALIDADE] [varchar](60) NOT NULL,
                [CPF_CNPJ_CONTRA] [varchar](20) NOT NULL,
                [DS_CIDADE_CONTRA] [varchar](60) NOT NULL,
                [DS_COMP_HISTORICO] [varchar](50) NOT NULL,
                [DE_TP_DOCTO_CONTRA] [varchar](40) NOT NULL,
                [NR_DOCTO_CONTRA] [varchar](50) NOT NULL,
                [DE_EXECUTOR] [varchar](60) NOT NULL,
                [CPF_EXECUTOR] [varchar](20) NOT NULL,
                [NR_PASSAPORTE_EXEC] [varchar](20) NOT NULL,
                [CD_NAT_OPERACAO] [varchar](20) NOT NULL,
                [DE_ORDENANTE] [varchar](120) NOT NULL,
                [UF_MOVTO] [char](2) NOT NULL,
                [DE_OPERADOR] [varchar](60) NOT NULL,
                [TX_PTAX] [float] NOT NULL,
                CONSTRAINT [PK_TAB_CLIENTES_MOVFIN_ME_PLD] PRIMARY KEY NONCLUSTERED ([CD_IDENTIFICACAO] ASC)
            )""",
    
        
        "MOVFIN_INT": """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD' AND xtype='U')
        CREATE TABLE [dbo].[TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD](
            [CD_IDENTIFICACAO] [char](40) NOT NULL,
            [CD_CLIENTE] [varchar](20) NOT NULL,
            [DT_MOVIMENTA] [datetime] NOT NULL,
            [NR_ORDEMPAGAMENTO] [varchar](10) NOT NULL,
            [DT_PAGAMENTO] [datetime] NOT NULL,
            [CPF_CNPJ] [char](20) NOT NULL,
            [DE_CLIENTE] [varchar](120) NOT NULL,
            [TP_DOC] [varchar](20) NOT NULL,
            [DE_MOEDA] [varchar](50) NOT NULL,
            [VL_ME] [money] NOT NULL,
            [VL_USD] [money] NOT NULL,
            [VL_CONTABIL_MN] [money] NOT NULL,
            [VL_FECHAMENTOVENDA_MN] [money] NOT NULL,
            [VL_GIRO] [money] NOT NULL,
            [DS_SITUACAO] [varchar](40) NOT NULL,
            [TP_MOVIMENTACAO] [varchar](40) NOT NULL,
            [DE_ORIGINADOR] [varchar](120) NOT NULL,
            [TP_DOCUMENTOORIGINADOR] [varchar](40) NOT NULL,
            [CPF_CNPJ_ORIGINADOR] [varchar](20) NOT NULL,
            [DE_PAISORIGINADOR] [varchar](50) NOT NULL,
            [DE_FAVORECIDO] [varchar](120) NOT NULL,
            [TP_DOCUMENTOFAVORECIDO] [varchar](40) NOT NULL,
            [CPF_CNPJ_FAVORECIDO] [varchar](20) NOT NULL,
            [DE_PAISFAVORECIDO] [varchar](50) NOT NULL,
            [DE_DETALHESPAGAMENTO] [varchar](1000) NOT NULL,
            [TP_CONTACORRENTE] [varchar](40) NOT NULL,
            [DE_ORIGEM] [smallint] NOT NULL,
            CONSTRAINT [PK_TAB_CLIENTES_MOVFIN_INTERMEDIADOR_PLD] PRIMARY KEY CLUSTERED ([CD_IDENTIFICACAO] ASC)
        )"""
    }
    
    try:
        conn = pyodbc.connect(Config.get_connection_string(config))
        cursor = conn.cursor()
        for sql in scripts.values():
            cursor.execute(sql)
            conn.commit()
        conn.close()
        return jsonify({"status": "ok", "message": "Estrutura do banco de dados verificada/criada com sucesso!"}), 200
    except Exception as e:
        return jsonify({"status": "erro", "erro": str(e)}), 500
    

    