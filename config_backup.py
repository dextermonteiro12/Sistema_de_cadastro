import os

class Config:
    # --- DIRETÓRIOS ---
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
    
    # --- BANCO DE DADOS ---
    # Centralizamos o driver para facilitar a troca (ex: se mudar da v17 para v18)
    DB_DRIVER = "{ODBC Driver 17 for SQL Server}"
    
    # --- SEGURANÇA E JWT (Se for usar futuramente) ---
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sua-chave-secreta-muito-segura'
    
    @staticmethod
    def get_connection_string(db_config):
        """
        Transforma o dicionário vindo do frontend em uma string ODBC completa.
        """
        return (
            f"DRIVER={Config.DB_DRIVER};"
            f"SERVER={db_config['servidor']};"
            f"DATABASE={db_config['banco']};"
            f"UID={db_config['usuario']};"
            f"PWD={db_config['senha']};"
            f"ConnectTimeout=300;"
            f"TrustServerCertificate=yes;"
        )

    # --- REGRAS DE NEGÓCIO (Opcional) ---
    # Você pode centralizar os códigos aqui para não "espalhar" números mágicos pelo código
    TP_CLIENTE_PF = "01"
    TP_CLIENTE_PJ = "02"