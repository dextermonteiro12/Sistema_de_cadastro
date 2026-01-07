# models.py
from pydantic import BaseModel, Field, conint, constr
from datetime import datetime
from typing import Literal

# --- Definições de Tipos Auxiliares (Constraints de Tamanho) ---
# Usamos 'constr' para simular os limites de tamanho de varchar/char do SQL
Char20 = constr(min_length=1, max_length=20)
Varchar120 = constr(min_length=1, max_length=120)
Char2 = constr(min_length=1, max_length=2)
Varchar80 = constr(min_length=1, max_length=80)
Varchar40 = constr(min_length=1, max_length=40)
Varchar10 = constr(min_length=1, max_length=10)
Varchar14 = constr(min_length=1, max_length=14)
Varchar50 = constr(min_length=1, max_length=50)
Varchar60 = constr(min_length=1, max_length=60)
Varchar104 = constr(min_length=1, max_length=104)
Varchar100 = constr(min_length=1, max_length=100)
Varchar5 = constr(min_length=1, max_length=5)
Varchar16 = constr(min_length=1, max_length=16)

# --- Modelo Principal do Cliente PLD ---

class ClienteModel(BaseModel):
    """Modelo de dados completo para o Cadastro de Cliente PLD."""
    
    # --- Identificação e Nome ---
    CD_CLIENTE: Char20 = Field(description="Código de identificação do cliente (char 20).")
    DE_CLIENTE: Varchar120 = Field(description="Nome ou Razão Social do cliente (varchar 120).")
    CD_TP_CLIENTE: Literal["PF", "PJ"] = Field(description="Tipo de Cliente: Pessoa Física ou Jurídica.")
    CIC_CPF: Char20 = Field(description="CPF ou CNPJ do cliente (varchar 20).")
    DS_GRUPO_CLIENTE: Varchar50 = Field(description="Grupo de Classificação do Cliente (varchar 50).")
    
    # --- Endereço Principal ---
    DE_ENDERECO: Varchar80 = Field(description="Endereço Principal.")
    DE_CIDADE: Varchar40 = Field(description="Cidade Principal.")
    DE_ESTADO: Char2 = Field(description="Estado Principal (UF).")
    DE_PAIS: Varchar40 = Field(description="País Principal.")
    CD_CEP: Varchar10 = Field(description="CEP Principal.")
    
    # --- Contato ---
    DE_FONE1: Varchar16 = Field(description="Telefone Principal.")
    DE_FONE2: Varchar16 = Field(description="Telefone Secundário.")
    DE_EMAIL: Varchar100 = Field(description="E-mail (varchar 100).")
    IP_ELETRONICO: Varchar104 = Field(description="IP Eletrônico de Cadastro ou Acesso (varchar 104).")
    
    # --- Endereço Residencial ---
    DE_ENDERECO_RES: Varchar80 = Field(description="Endereço Residencial.")
    DE_CIDADE_RES: Varchar40 = Field(description="Cidade Residencial.")
    DE_ESTADO_RES: Char2 = Field(description="Estado Residencial (UF).")
    DE_PAIS_RES: Varchar40 = Field(description="País Residencial.")
    CD_CEP_RES: Varchar10 = Field(description="CEP Residencial.")
    
    # --- Endereço Comercial ---
    DE_ENDERECO_CML: Varchar80 = Field(description="Endereço Comercial.")
    DE_CIDADE_CML: Varchar40 = Field(description="Cidade Comercial.")
    DE_ESTADO_CML: Char2 = Field(description="Estado Comercial (UF).")
    DE_PAIS_CML: Varchar40 = Field(description="País Comercial.")
    CD_CEP_CML: Varchar10 = Field(description="CEP Comercial.")
    
    # --- Datas (Datetime) ---
    DT_ABERTURA_REL: datetime = Field(description="Data de Abertura do Relacionamento.")
    DT_DESATIVACAO: datetime = Field(description="Data de Desativação do Cliente.")
    DT_ULT_ALTERACAO: datetime = Field(description="Data da Última Alteração Cadastral.")
    DT_CONSTITUICAO: datetime = Field(description="Data de Constituição (PJ) ou Nasc. (PF).")
    
    # --- Atividade e Classificação ---
    DS_RAMO_ATV: Varchar80 = Field(description="Ramo de Atividade (varchar 80).")
    DE_LINHA_NEGOCIO: Char20 = Field(description="Linha de Negócio.")
    CD_NAIC: Char20 = Field(description="Código NAIC (Padrão internacional).")
    CD_NAT_JURIDICA: Varchar5 = Field(description="Código de Natureza Jurídica.")
    
    # --- Risco e Flags (smallint e bit) ---
    CD_RISCO: conint(ge=1, le=5) = Field(description="Código de Risco (smallint, Nível 1 a 5).")
    CD_RISCO_INERENTE: conint(ge=1, le=5) = Field(description="Código de Risco Inerente (smallint, Nível 1 a 5).")
    DE_SIT_CADASTRO: Varchar40 = Field(description="Situação do Cadastro (Ex: ATIVO, BLOQUEADO).")
    
    # Flags (bit) - Usamos int com restrição para 0 ou 1
    FL_BLOQUEADO: int = Field(ge=0, le=1, description="Flag: 1 se o cliente estiver bloqueado.")
    FL_FUNDO_INVEST: int = Field(ge=0, le=1, description="Flag: 1 se for Fundo de Investimento.")
    FL_CLI_EVENTUAL: int = Field(ge=0, le=1, description="Flag: 1 se for Cliente Eventual.")
    FL_CADASTRO_PROC: int = Field(ge=0, le=1, description="Flag: 1 se o Cadastro foi Processado.")
    FL_NAO_RESIDENTE: int = Field(ge=0, le=1, description="Flag: 1 se for Não Residente.")
    FL_GRANDES_FORTUNAS: int = Field(ge=0, le=1, description="Flag: 1 se for Grandes Fortunas.")
    FL_RELACIONAMENTO_TERCEIROS: int = Field(ge=0, le=1, description="Flag: 1 se houver Relacionamento com Terceiros.")
    FL_ADMIN_CARTOES: int = Field(ge=0, le=1, description="Flag: 1 se Administra Cartões.")
    FL_EMPRESA_TRUST: int = Field(ge=0, le=1, description="Flag: 1 se for Empresa Trust.")
    FL_FACILITADORA_PAGTO: int = Field(ge=0, le=1, description="Flag: 1 se for Facilitadora de Pagamento.")
    FL_EMP_REGULADA: int = Field(ge=0, le=1, description="Flag: 1 se for Empresa Regulada.")
    
    # --- Responsáveis e Sede ---
    DE_RESPONS_CADASTRO: Varchar60 = Field(description="Nome do Responsável pelo Cadastro.")
    DE_CONF_CADASTRO: Varchar60 = Field(description="Nome do Confirmador do Cadastro.")
    DE_PAIS_SEDE: Varchar40 = Field(description="País Sede da Empresa/Cliente.")
    
    # --- Configuração de Serialização ---
    class Config:
        # Permite que os modelos sejam criados a partir de ORM (se necessário)
        orm_mode = True
        # Garante que objetos datetime sejam serializados corretamente para JSON
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }