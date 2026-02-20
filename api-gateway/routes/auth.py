"""
Rotas de autenticação: login, register, logout
Responsável por gerenciar tokens JWT e sessões
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
import logging
import os
from typing import Optional
from auth_database import AuthDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# ===== CONFIGURAÇÃO JWT =====

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_secret_key_please_change_in_production")
ALGORITHM = "HS256"
TOKEN_EXPIRATION_HOURS = int(os.getenv("TOKEN_EXPIRATION_HOURS", 24))


# ===== MODELOS PYDANTIC =====

class LoginRequest(BaseModel):
    """Request para login"""
    username: str
    password: str


class RegisterRequest(BaseModel):
    """Request para registrar novo usuário"""
    username: str
    password: str
    email: Optional[str] = None


class TokenResponse(BaseModel):
    """Response com token JWT"""
    access_token: str
    token_type: str
    expires_in: int
    user: dict


class UserResponse(BaseModel):
    """Dados do usuário autenticado"""
    id: str
    username: str
    email: Optional[str] = None


# ===== FUNÇÕES AUXILIARES =====

def create_jwt_token(user_id: str, username: str) -> tuple[str, datetime]:
    """
    Cria token JWT válido por TOKEN_EXPIRATION_HOURS horas
    Returns: (token, expiration_time)
    """
    expiration = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRATION_HOURS)
    
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": expiration,
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, expiration


def verify_jwt_token(token: str) -> Optional[dict]:
    """
    Verifica e decodifica token JWT
    Returns: payload se válido, None se inválido
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expirado")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token inválido: {e}")
        return None


def get_user_from_token(authorization: str = Header(None)) -> Optional[dict]:
    """
    Extrai usuário do header Authorization
    Formato esperado: "Bearer <token>"
    """
    if not authorization:
        return None
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    token = parts[1]
    payload = verify_jwt_token(token)
    
    return payload


# ===== ENDPOINTS =====

@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """
    Registra novo usuário e retorna token JWT
    
    Example:
        POST /auth/register
        {
            "username": "user1",
            "password": "senha123",
            "email": "user@example.com"
        }
    """
    if not request.username or not request.password:
        raise HTTPException(
            status_code=400,
            detail="username e password são obrigatórios"
        )
    
    if len(request.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Senha deve ter no mínimo 6 caracteres"
        )
    
    try:
        user = AuthDB.create_user(
            username=request.username,
            password=request.password,
            email=request.email
        )
        
        token, expiration = create_jwt_token(user["id"], user["username"])
        
        logger.info(f"Novo usuário registrado: {request.username}")
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=TOKEN_EXPIRATION_HOURS * 3600,
            user={
                "id": user["id"],
                "username": user["username"],
                "email": request.email
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao registrar usuário: {e}")
        raise HTTPException(status_code=500, detail="Erro ao registrar usuário")


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Autentica usuário e retorna token JWT
    
    Example:
        POST /auth/login
        {
            "username": "user1",
            "password": "senha123"
        }
    """
    if not request.username or not request.password:
        raise HTTPException(
            status_code=400,
            detail="username e password são obrigatórios"
        )
    
    user = AuthDB.authenticate(request.username, request.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Credenciais inválidas"
        )
    
    token, expiration = create_jwt_token(user["id"], user["username"])
    
    logger.info(f"Login bem-sucedido: {request.username}")
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=TOKEN_EXPIRATION_HOURS * 3600,
        user={
            "id": user["id"],
            "username": user["username"]
        }
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(authorization: str = Header(None)):
    """
    Retorna dados do usuário autenticado
    Requer token no header: Authorization: Bearer <token>
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Token não fornecido"
        )
    
    payload = get_user_from_token(authorization)
    
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Token inválido ou expirado"
        )
    
    user = AuthDB.get_user(payload["user_id"])
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado"
        )
    
    return UserResponse(**user)


@router.post("/validate-token")
async def validate_token(authorization: str = Header(None)):
    """
    Valida se token JWT é válido
    """
    if not authorization:
        return {"valid": False, "message": "Token não fornecido"}
    
    payload = get_user_from_token(authorization)
    
    if not payload:
        return {"valid": False, "message": "Token inválido ou expirado"}
    
    return {
        "valid": True,
        "user_id": payload.get("user_id"),
        "username": payload.get("username"),
        "expires_at": payload.get("exp")
    }


@router.post("/logout")
async def logout(authorization: str = Header(None)):
    """
    Logout do usuário (validação no frontend)
    Backend apenas valida token e confirma
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Token não fornecido")
    
    payload = get_user_from_token(authorization)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    logger.info(f"Logout: {payload.get('username')}")
    
    return {"message": "Logout bem-sucedido"}
