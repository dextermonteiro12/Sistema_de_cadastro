"""
Gerenciador de Pool de Conexões com configuração dinâmica
Suporta múltiplas conexões do frontend
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from urllib.parse import quote_plus
from contextlib import contextmanager
from typing import Generator, Dict, Optional
import os
import logging
from threading import Lock

logger = logging.getLogger(__name__)

# ===== GERENCIADOR DE ENGINES DINÂMICOS =====
class DynamicConnectionManager:
    """
    Gerencia múltiplas engines de banco de dados
    Permite que cada cliente (front) conecte ao seu próprio servidor SQL
    """
    
    def __init__(self):
        self.engines: Dict[str, any] = {}
        self.session_makers: Dict[str, sessionmaker] = {}
        self.configs: Dict[str, dict] = {}
        self.lock = Lock()
    
    def criar_engine(
        self,
        config_key: str,
        servidor: str,
        banco: str,
        usuario: str,
        senha: str,
        driver: str = "{ODBC Driver 17 for SQL Server}",
        pool_size: int = 10,
        max_overflow: int = 20
    ):
        """
        Cria um novo engine com pool de conexões
        
        Args:
            config_key: Identificador único (ex: "user_123")
            servidor: Servidor SQL Server
            banco: Nome do banco de dados
            usuario: Usuário SQL
            senha: Senha SQL
            driver: Driver ODBC
            pool_size: Tamanho do pool
            max_overflow: Máximo overflow
        
        Returns:
            bool: True se sucesso, False se erro
        """
        with self.lock:
            try:
                # URL-encodar o driver para evitar erros de sintaxe
                encoded_driver = quote_plus(driver.replace('{', '').replace('}', ''))
                
                # Construir URL de conexão
                connection_url = (
                    f"mssql+pyodbc://{usuario}:{senha}@"
                    f"{servidor}/{banco}"
                    f"?driver={encoded_driver}&TrustServerCertificate=yes"
                )
                
                # Criar engine
                engine = create_engine(
                    connection_url,
                    poolclass=QueuePool,
                    pool_size=pool_size,
                    max_overflow=max_overflow,
                    pool_recycle=3600,
                    pool_pre_ping=True,
                    connect_args={
                        'timeout': 30,
                        'isolation_level': 'READ COMMITTED',
                        'TrustServerCertificate': 'yes',
                        'ConnectTimeout': 300,
                    },
                    echo=False
                )
                
                # Testar conexão
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                
                # Armazenar
                self.engines[config_key] = engine
                self.session_makers[config_key] = sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=engine
                )
                self.configs[config_key] = {
                    "servidor": servidor,
                    "banco": banco,
                    "usuario": usuario,
                    "senha": senha,
                    "driver": driver
                }
                
                logger.info(f"✓ Engine criado: {config_key}")
                logger.info(f"  Servidor: {servidor}")
                logger.info(f"  Banco: {banco}")
                logger.info(f"  Pool: {pool_size} + {max_overflow}")
                
                return True
                
            except Exception as e:
                logger.error(f"✗ Erro ao criar engine {config_key}: {str(e)}")
                return False
    
    def obter_engine(self, config_key: str):
        """Obtém engine existente"""
        if config_key not in self.engines:
            logger.error(f"Engine não encontrado: {config_key}")
            return None
        return self.engines[config_key]
    
    def obter_session_maker(self, config_key: str):
        """Obtém session maker do engine"""
        if config_key not in self.session_makers:
            logger.error(f"Session maker não encontrado: {config_key}")
            return None
        return self.session_makers[config_key]
    
    def listar_engines(self):
        """Lista todos os engines ativos"""
        return list(self.engines.keys())

    def get_config(self, config_key: str):
        return self.configs.get(config_key)
    
    def fechar_engine(self, config_key: str):
        """Fecha engine específico"""
        with self.lock:
            if config_key in self.engines:
                self.engines[config_key].dispose()
                del self.engines[config_key]
                del self.session_makers[config_key]
                self.configs.pop(config_key, None)
                logger.info(f"✓ Engine fechado: {config_key}")
    
    def fechar_todos(self):
        """Fecha todos os engines"""
        with self.lock:
            for config_key in list(self.engines.keys()):
                self.engines[config_key].dispose()
            self.engines.clear()
            self.session_makers.clear()
            logger.info("✓ Todos os engines fechados")

# ===== INSTÂNCIA GLOBAL =====
db_manager = DynamicConnectionManager()

# ===== CONTEXT MANAGER PARA SESSÕES =====
@contextmanager
def get_db_session(config_key: str) -> Generator[Session, None, None]:
    """
    Context manager para usar sessão com engine específico
    
    Usage:
        with get_db_session("user_123") as session:
            session.execute(text("SELECT * FROM tabela"))
    """
    session_maker = db_manager.obter_session_maker(config_key)
    
    if session_maker is None:
        raise ValueError(f"Configuração não encontrada: {config_key}")
    
    session = session_maker()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        session.close()

# ===== FUNÇÃO PARA VALIDAR CONEXÃO =====
async def validar_conexao(
    servidor: str,
    banco: str,
    usuario: str,
    senha: str,
    driver: str = "{ODBC Driver 17 for SQL Server}"
) -> dict:
    """
    Valida conexão com SQL Server
    
    Returns:
        {
            "status": "ok" | "erro",
            "mensagem": "...",
            "versao": "V8" ou "V9" (se OK),
            "detalhes": {...}
        }
    """
    try:
        # URL-encodar o driver para evitar erros de sintaxe
        encoded_driver = quote_plus(driver.replace('{', '').replace('}', ''))
        # Remover chaves do driver se existirem
        encoded_driver = encoded_driver.replace("%7B", "").replace("%7D", "")
        
        # Criar engine temporário
        connection_url = (
            f"mssql+pyodbc://{usuario}:{senha}@"
            f"{servidor}/{banco}"
            f"?driver={encoded_driver}&TrustServerCertificate=yes"
        )
        
        temp_engine = create_engine(
            connection_url,
            connect_args={
                'timeout': 10,
                'TrustServerCertificate': 'yes'
            }
        )
        
        # Testar conexão
        with temp_engine.connect() as conn:
            # Verificar versão do sistema
            try:
                result = conn.execute(
                    text("SELECT TOP 1 CD_VERSAO FROM AD_SISTEMAS_VERSOES WITH (NOLOCK) ORDER BY 1 DESC")
                )
                row = result.fetchone()
                versao = "V9" if row and "009" in str(row[0]) else "V8"
            except:
                versao = "V8"
            
            # Verificar tabelas
            result = conn.execute(
                text("SELECT COUNT(*) FROM sys.tables WHERE name LIKE 'TAB_CLIENTES%'")
            )
            qtd_tabelas = result.scalar() or 0
        
        temp_engine.dispose()
        
        return {
            "status": "ok",
            "mensagem": "✓ Conexão validada com sucesso",
            "versao": versao,
            "detalhes": {
                "servidor": servidor,
                "banco": banco,
                "versao_sistema": versao,
                "tabelas_pld": qtd_tabelas
            }
        }
        
    except Exception as e:
        error_msg = str(e)
        
        # Mensagens de erro mais claras
        if "login failed" in error_msg.lower():
            erro = "Usuário ou senha incorretos"
        elif "cannot open database" in error_msg.lower():
            erro = "Banco de dados não encontrado"
        elif "connection timeout" in error_msg.lower():
            erro = "Timeout - Servidor não responde"
        elif "named instance not found" in error_msg.lower():
            erro = "Instância SQL não encontrada"
        else:
            erro = error_msg
        
        return {
            "status": "erro",
            "mensagem": f"✗ Erro ao conectar: {erro}",
            "detalhes": {
                "servidor": servidor,
                "banco": banco,
                "erro_completo": error_msg
            }
        }

# ===== HEALTH CHECK =====
async def check_db_health(config_key: str) -> dict:
    """Verifica saúde da conexão específica"""
    try:
        with get_db_session(config_key) as session:
            session.execute(text("SELECT 1"))
        
        engine = db_manager.obter_engine(config_key)
        return {
            "status": "healthy",
            "message": "✓ Banco respondendo",
            "pool_size": engine.pool.size(),
            "pool_checked_out": engine.pool.checkedout()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "✗ Erro ao conectar"
        }

# ===== ENGINE DEFAULT (para compatibilidade) =====
# Se houver .env, criar engine padrão
DEFAULT_CONFIG_KEY = "default"

default_db_url = os.getenv('DATABASE_URL', None)
if default_db_url:
    try:
        default_engine = create_engine(
            default_db_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            pool_pre_ping=True
        )
        db_manager.engines[DEFAULT_CONFIG_KEY] = default_engine
        db_manager.session_makers[DEFAULT_CONFIG_KEY] = sessionmaker(
            bind=default_engine
        )
        logger.info(f"✓ Engine padrão carregado do .env")
    except Exception as e:
        logger.warning(f"⚠️  Sem engine padrão: {e}")

def close_db():
    """Fecha todos os engines"""
    db_manager.fechar_todos()
