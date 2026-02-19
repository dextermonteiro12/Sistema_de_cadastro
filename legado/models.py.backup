from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Literal, Annotated
from pydantic.types import StringConstraints, ImportString

# --- Definições de Tipos Auxiliares para Pydantic V2 ---
Char20 = Annotated[str, StringConstraints(min_length=1, max_length=20)]
Varchar120 = Annotated[str, StringConstraints(min_length=1, max_length=120)]
Char2 = Annotated[str, StringConstraints(min_length=1, max_length=2)]
Varchar80 = Annotated[str, StringConstraints(min_length=1, max_length=80)]
Varchar40 = Annotated[str, StringConstraints(min_length=1, max_length=40)]
Varchar10 = Annotated[str, StringConstraints(min_length=1, max_length=10)]
Varchar104 = Annotated[str, StringConstraints(min_length=1, max_length=104)]
Varchar100 = Annotated[str, StringConstraints(min_length=1, max_length=100)]
Varchar5 = Annotated[str, StringConstraints(min_length=1, max_length=5)]
Varchar60 = Annotated[str, StringConstraints(min_length=1, max_length=60)]
Varchar16 = Annotated[str, StringConstraints(min_length=1, max_length=16)]
Varchar50 = Annotated[str, StringConstraints(min_length=1, max_length=50)]

class ClienteModel(BaseModel):
    # Configuração para Pydantic V2
    model_config = ConfigDict(from_attributes=True)

    CD_CLIENTE: Char20
    DE_CLIENTE: Varchar120
    CD_TP_CLIENTE: Literal["PF", "PJ"]
    CIC_CPF: Char20
    DS_GRUPO_CLIENTE: Varchar50
    DE_ENDERECO: Varchar80
    DE_CIDADE: Varchar40
    DE_ESTADO: Char2
    DE_PAIS: Varchar40
    CD_CEP: Varchar10
    DE_FONE1: Varchar16
    DE_FONE2: Varchar16
    DE_EMAIL: Varchar100
    IP_ELETRONICO: Varchar104
    DE_ENDERECO_RES: Varchar80
    DE_CIDADE_RES: Varchar40
    DE_ESTADO_RES: Char2
    DE_PAIS_RES: Varchar40
    CD_CEP_RES: Varchar10
    DE_ENDERECO_CML: Varchar80
    DE_CIDADE_CML: Varchar40
    DE_ESTADO_CML: Char2
    DE_PAIS_CML: Varchar40
    CD_CEP_CML: Varchar10
    DT_ABERTURA_REL: datetime
    DT_DESATIVACAO: datetime
    DT_ULT_ALTERACAO: datetime
    DT_CONSTITUICAO: datetime
    DS_RAMO_ATV: Varchar80
    DE_LINHA_NEGOCIO: Char20
    CD_NAIC: Char20
    CD_NAT_JURIDICA: Varchar5
    CD_RISCO: int = Field(ge=1, le=5)
    CD_RISCO_INERENTE: int = Field(ge=1, le=5)
    DE_SIT_CADASTRO: Varchar40
    FL_BLOQUEADO: int = Field(ge=0, le=1)
    FL_FUNDO_INVEST: int = Field(ge=0, le=1)
    FL_CLI_EVENTUAL: int = Field(ge=0, le=1)
    FL_CADASTRO_PROC: int = Field(ge=0, le=1)
    FL_NAO_RESIDENTE: int = Field(ge=0, le=1)
    FL_GRANDES_FORTUNAS: int = Field(ge=0, le=1)
    FL_RELACIONAMENTO_TERCEIROS: int = Field(ge=0, le=1)
    FL_ADMIN_CARTOES: int = Field(ge=0, le=1)
    FL_EMPRESA_TRUST: int = Field(ge=0, le=1)
    FL_FACILITADORA_PAGTO: int = Field(ge=0, le=1)
    FL_EMP_REGULADA: int = Field(ge=0, le=1)
    DE_RESPONS_CADASTRO: Varchar60
    DE_CONF_CADASTRO: Varchar60
    DE_PAIS_SEDE: Varchar40