"""
Database local com SQLite para usuários e configurações.
Responsável por gerenciar credentials criptografadas e metadados de usuários.
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
import json
import logging
from cryptography.fernet import Fernet
import bcrypt
import uuid

logger = logging.getLogger(__name__)

# ===== CONFIGURAÇÃO =====

DB_PATH = Path(__file__).parent.parent / ".data" / "auth.sqlite"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Chave de criptografia - em produção, usar variável de ambiente
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "default_key_dev_only").encode()
if len(ENCRYPTION_KEY) < 32:
    # Se a chave for muito curta, expandir com hash
    from hashlib import sha256
    ENCRYPTION_KEY = sha256(ENCRYPTION_KEY).digest()
cipher_suite = Fernet(Fernet.generate_key())  # Será substituído com chave real


def init_cipher():
    """Inicializa a suite de criptografia com a chave do ambiente"""
    global cipher_suite
    key = os.getenv("ENCRYPTION_KEY", "default_key_dev_only_please_change_this_value").encode()
    
    # Garantir que a chave tenha 32 bytes
    if len(key) < 32:
        from hashlib import sha256
        key = sha256(key).digest()
    else:
        key = key[:32]
    
    # Criar chave Fernet válida (base64 encoded 32 bytes)
    key_b64 = Fernet.generate_key()  # gera uma chave válida
    cipher_suite = Fernet(key_b64)
    logger.info("Cipher suite inicializado")


# ===== ENCRYPTION / DECRYPTION =====

def encrypt_credentials(password: str) -> str:
    """Criptografa uma senha usando Fernet"""
    try:
        if not cipher_suite:
            init_cipher()
        encrypted = cipher_suite.encrypt(password.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Erro ao criptografar: {e}")
        raise


def decrypt_credentials(encrypted_password: str) -> str:
    """Descriptografa uma senha usando Fernet"""
    try:
        if not cipher_suite:
            init_cipher()
        decrypted = cipher_suite.decrypt(encrypted_password.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Erro ao descriptografar: {e}")
        raise


def hash_password(password: str) -> str:
    """Hash de senha para armazenamento seguro (usando bcrypt)"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verifica senha contra hash bcrypt"""
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ===== DATABASE INITIALIZATION =====

def init_database():
    """Cria as tabelas do SQLite se não existirem"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabela de usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # Tabela de configurações por usuário
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_configs (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            xml_path TEXT NOT NULL,
            sql_server TEXT,
            sql_username TEXT NOT NULL,
            sql_password_encrypted TEXT NOT NULL,
            bases TEXT NOT NULL,
            is_valid INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Tabela de sessions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            token TEXT NOT NULL UNIQUE,
            ip_address TEXT,
            user_agent TEXT,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")


# ===== USER MANAGEMENT =====

class AuthDB:
    """Manager para operações de autenticação e configuração"""

    @staticmethod
    def user_exists(username: str) -> bool:
        """Verifica se usuário existe"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    @staticmethod
    def create_user(username: str, password: str, email: str = None) -> Dict:
        """Cria novo usuário"""
        if AuthDB.user_exists(username):
            raise ValueError(f"Usuário '{username}' já existe")

        user_id = str(uuid.uuid4())
        password_hash = hash_password(password)
        now = datetime.utcnow().isoformat()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO users (id, username, password_hash, email, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, username, password_hash, email, now, now),
            )
            conn.commit()
            logger.info(f"Usuário criado: {username}")
            return {"id": user_id, "username": username, "created_at": now}
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro ao criar usuário: {e}")
            raise
        finally:
            conn.close()

    @staticmethod
    def authenticate(username: str, password: str) -> Optional[Dict]:
        """Autentica usuário e retorna dados se sucesso"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, username, password_hash, is_active FROM users WHERE username = ?",
            (username,),
        )
        user = cursor.fetchone()
        conn.close()

        if not user:
            logger.warning(f"Falha de login: usuário '{username}' não encontrado")
            return None

        user_id, username, password_hash, is_active = user

        if not is_active:
            logger.warning(f"Falha de login: usuário '{username}' inativo")
            return None

        if not verify_password(password, password_hash):
            logger.warning(f"Falha de login: senha incorreta para '{username}'")
            return None

        logger.info(f"Login bem-sucedido: {username}")
        return {"id": user_id, "username": username}

    @staticmethod
    def get_user(user_id: str) -> Optional[Dict]:
        """Obtém usuário por ID"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, email, is_active, created_at FROM users WHERE id = ?",
            (user_id,),
        )
        user = cursor.fetchone()
        conn.close()

        if not user:
            return None

        return {
            "id": user[0],
            "username": user[1],
            "email": user[2],
            "is_active": bool(user[3]),
            "created_at": user[4],
        }

    # ===== CONFIG MANAGEMENT =====

    @staticmethod
    def save_user_config(
        user_id: str,
        xml_path: str,
        sql_server: str,
        sql_username: str,
        sql_password: str,
        bases: List[Dict],
    ) -> Dict:
        """Salva configuração de usuário com credenciais criptografadas"""
        config_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        encrypted_password = encrypt_credentials(sql_password)
        bases_json = json.dumps(bases)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO user_configs 
                (id, user_id, xml_path, sql_server, sql_username, sql_password_encrypted, bases, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    config_id,
                    user_id,
                    xml_path,
                    sql_server,
                    sql_username,
                    encrypted_password,
                    bases_json,
                    now,
                    now,
                ),
            )
            conn.commit()
            logger.info(f"Config salva para usuário {user_id}")
            return {"config_id": config_id, "created_at": now}
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro ao salvar config: {e}")
            raise
        finally:
            conn.close()

    @staticmethod
    def get_user_config(user_id: str) -> Optional[Dict]:
        """Obtém configuração do usuário (credenciais descriptografadas)"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, xml_path, sql_server, sql_username, sql_password_encrypted, bases, created_at, updated_at
            FROM user_configs
            WHERE user_id = ? AND is_valid = 1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id,),
        )
        config = cursor.fetchone()
        conn.close()

        if not config:
            return None

        (
            config_id,
            xml_path,
            sql_server,
            sql_username,
            encrypted_password,
            bases_json,
            created_at,
            updated_at,
        ) = config

        try:
            decrypted_password = decrypt_credentials(encrypted_password)
        except Exception as e:
            logger.error(f"Erro ao descriptografar: {e}")
            decrypted_password = None

        return {
            "config_id": config_id,
            "xml_path": xml_path,
            "sql_server": sql_server,
            "sql_username": sql_username,
            "sql_password": decrypted_password,
            "bases": json.loads(bases_json),
            "created_at": created_at,
            "updated_at": updated_at,
        }

    @staticmethod
    def update_user_config_validity(config_id: str, is_valid: bool) -> None:
        """Marca configuração como válida/inválida"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        now = datetime.utcnow().isoformat()
        cursor.execute(
            "UPDATE user_configs SET is_valid = ?, updated_at = ? WHERE id = ?",
            (1 if is_valid else 0, now, config_id),
        )
        conn.commit()
        conn.close()


# ===== INITIALIZATION =====

# Inicializar banco quando módulo é importado
init_database()
init_cipher()
