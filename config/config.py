"""
Configurações centralizadas da aplicação
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class DatabaseConfig:
    """Configurações de banco de dados"""
    driver: str = os.getenv('DB_DRIVER', '{ODBC Driver 17 for SQL Server}')
    server: str = os.getenv('DB_SERVER', 'localhost')
    database: str = os.getenv('DB_NAME', 'PLD')
    user: str = os.getenv('DB_USER', 'sa')
    password: str = os.getenv('DB_PASSWORD', '')
    pool_size: int = int(os.getenv('DB_POOL_SIZE', '10'))
    max_overflow: int = int(os.getenv('DB_MAX_OVERFLOW', '20'))
    
    @property
    def connection_url(self) -> str:
        """Gera URL de conexão do pool"""
        return (
            f"mssql+pyodbc://{self.user}:{self.password}@"
            f"{self.server}/{self.database}"
            f"?driver={self.driver}&TrustServerCertificate=yes"
        )

@dataclass
class GRPCConfig:
    """Configurações de gRPC (futuro)"""
    host: str = os.getenv('GRPC_HOST', 'localhost')
    port: int = int(os.getenv('GRPC_PORT', '50051'))
    max_workers: int = int(os.getenv('GRPC_WORKERS', '10'))

@dataclass
class AppConfig:
    """Configurações gerais da aplicação"""
    environment: str = os.getenv('ENVIRONMENT', 'development')
    debug: bool = os.getenv('DEBUG', 'true').lower() == 'true'
    api_title: str = "PLD Data Generator API v2.0"
    api_version: str = "2.0.0"
    
    # CORS
    cors_origins: list = [
        "http://localhost:3000",
        "http://localhost:5000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5000"
    ]
    
    # Database
    db: DatabaseConfig = DatabaseConfig()
    
    # gRPC
    grpc: GRPCConfig = GRPCConfig()
    
    @property
    def is_production(self) -> bool:
        """Verifica se está em produção"""
        return self.environment == 'production'

# Singleton global
config = AppConfig()
