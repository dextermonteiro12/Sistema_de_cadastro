"""
Rotas para gerenciar configuração de banco de dados
"""

from fastapi import APIRouter, HTTPException, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Optional
import re
from database import db_manager, validar_conexao, check_db_health

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["configuration"])

# ===== MODELOS PYDANTIC =====

class DatabaseConfig(BaseModel):
    """Modelo para configuração de banco"""
    servidor: str
    banco: str
    usuario: str
    senha: str
    driver: str = "{ODBC Driver 17 for SQL Server}"

class ValidarConfigRequest(BaseModel):
    """Request para validar configuração"""
    config: DatabaseConfig
    session_id: Optional[str] = None
    ambiente: Optional[str] = None

class ListarBasesPastaRequest(BaseModel):
    """Request para listar possíveis nomes de bases a partir de um caminho"""
    folder_path: str


def _resolve_advice_xml(path_texto: str) -> Path:
    path = Path(path_texto)
    logger.info(f"Resolvendo Advice.xml para: {path_texto}")

    if path.suffix.lower() == ".xml":
        logger.info(f"Caminho é arquivo XML: {path}")
        if not path.exists() or not path.is_file():
            logger.error(f"Arquivo XML não encontrado: {path}")
            raise HTTPException(status_code=404, detail=f"Arquivo XML não encontrado: {path}")
        logger.info(f"Arquivo XML encontrado: {path}")
        return path

    if not path.exists() or not path.is_dir():
        logger.error(f"Pasta não encontrada: {path}")
        raise HTTPException(status_code=404, detail=f"Pasta não encontrada: {path}")

    candidatos = [
        path / "config" / "Advice.xml",
        path / "Advice.xml"
    ]

    for candidato in candidatos:
        logger.info(f"Procurando em: {candidato}")
        if candidato.exists() and candidato.is_file():
            logger.info(f"Advice.xml encontrado em: {candidato}")
            return candidato

    logger.error(f"Advice.xml não encontrado em nenhum dos candidatos: {candidatos}")
    raise HTTPException(
        status_code=404,
        detail=f"Advice.xml não encontrado. Procurado em: {candidatos}"
    )


def _sanitize_session_id(session_id: str | None) -> str:
    raw = (session_id or "").strip()
    if not raw:
        return "default"
    return re.sub(r"[^a-zA-Z0-9_-]", "", raw)[:64] or "default"


def _extract_bases_from_xml(xml_path: Path) -> list[dict]:
    try:
        logger.info(f"Parsing XML: {xml_path}")
        tree = ET.parse(xml_path)
        root = tree.getroot()
        logger.info(f"Raiz do XML: {root.tag}")
    except ET.ParseError as e:
        logger.error(f"XML inválido: {str(e)}")
        raise HTTPException(status_code=400, detail=f"XML inválido: {str(e)}")
    except Exception as e:
        logger.error(f"Erro ao ler XML: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao ler XML: {str(e)}")

    configuracoes = []

    def local_name(tag: str) -> str:
        if not tag:
            return ""
        return tag.split("}")[-1].strip()

    def find_child(parent, child_name: str):
        alvo = child_name.lower()
        for child in list(parent):
            if local_name(child.tag).lower() == alvo:
                return child
        return None

    def find_text(parent, child_name: str) -> str:
        node = find_child(parent, child_name)
        if node is None or node.text is None:
            return ""
        return node.text.strip()

    def find_sistema_node(nome_sistema: str):
        alvo = nome_sistema.lower()
        for child in list(root):
            if local_name(child.tag).lower() == alvo:
                return child
        return None

    for sistema in ["CORP", "EGUARDIAN"]:
        logger.info(f"Procurando sistema: {sistema}")
        sistema_node = find_sistema_node(sistema)
        if sistema_node is None:
            logger.warning(f"Sistema {sistema} não encontrado no XML")
            continue

        logger.info(f"Sistema {sistema} encontrado")
        empresa_root = find_child(sistema_node, "EMPRESA")
        if empresa_root is None:
            logger.warning(f"Nó EMPRESA não encontrado para {sistema}")
            continue

        logger.info(f"Nó EMPRESA encontrado para {sistema}")
        for empresa_node in list(empresa_root):
            banco_node = find_child(empresa_node, "BANCO_DADOS")
            if banco_node is None:
                logger.debug(f"BANCO_DADOS não encontrado em {local_name(empresa_node.tag)}")
                continue

            servidor = find_text(banco_node, "NOME_SERVIDOR")
            banco = find_text(banco_node, "NOME_BD")
            usuario = find_text(banco_node, "USUARIO")
            provider = find_text(banco_node, "PROVIDER")
            timeout = find_text(banco_node, "TIME_OUT")
            empresa = local_name(empresa_node.tag).strip()

            if not banco:
                logger.warning(f"Banco não encontrado para {sistema}/{empresa}")
                continue

            config_item = {
                "id": f"{sistema}:{empresa}:{banco}",
                "sistema": sistema,
                "empresa": empresa,
                "servidor": servidor,
                "banco": banco,
                "usuario": usuario,
                "provider": provider,
                "timeout": timeout,
                "label": f"{sistema} | {empresa} | {banco}"
            }
            configuracoes.append(config_item)
            logger.info(f"Base encontrada: {config_item['label']}")

    logger.info(f"Total de bases encontradas: {len(configuracoes)}")
    return configuracoes

# ===== ENDPOINTS =====

@router.post("/validar")
async def validar_configuracao(request: ValidarConfigRequest):
    """
    Valida configuração de banco de dados do frontend
    
    Example:
        POST /config/validar
        {
            "config": {
                "servidor": "localhost",
                "banco": "PLD",
                "usuario": "sa",
                "senha": "senha123"
            }
        }
    """
    config = request.config
    
    logger.info(f"Validando config para: {config.servidor}/{config.banco}")
    
    result = await validar_conexao(
        servidor=config.servidor,
        banco=config.banco,
        usuario=config.usuario,
        senha=config.senha,
        driver=config.driver
    )
    
    if result["status"] != "ok":
        raise HTTPException(status_code=400, detail=result)
    
    # Se validado, criar engine por sessão (isola abas/sessões)
    session_id = _sanitize_session_id(request.session_id)
    ambiente = (request.ambiente or "").strip()
    config_key = f"{session_id}:{config.usuario}@{config.servidor}:{config.banco}"
    
    success = db_manager.criar_engine(
        config_key=config_key,
        servidor=config.servidor,
        banco=config.banco,
        usuario=config.usuario,
        senha=config.senha,
        driver=config.driver
    )
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Erro ao criar pool de conexões"
        )
    
    return {
        "status": "ok",
        "mensagem": "✓ Configuração validada e ativada",
        "config_key": config_key,
        "session_id": session_id,
        "ambiente": ambiente,
        "detalhes": result["detalhes"]
    }

@router.post("/teste")
async def testar_conexao(request: ValidarConfigRequest):
    """
    Apenas testa a conexão sem criar engine
    Útil para UI validação antes de salvar
    """
    config = request.config
    
    result = await validar_conexao(
        servidor=config.servidor,
        banco=config.banco,
        usuario=config.usuario,
        senha=config.senha,
        driver=config.driver
    )
    
    status_code = 200 if result["status"] == "ok" else 400
    
    return JSONResponse(content=result, status_code=status_code)

@router.post("/listar-bases-pasta")
async def listar_bases_pasta(request: ListarBasesPastaRequest):
    """
    Lista nomes de bases candidatas a partir do Advice.xml.

    Entrada aceita:
    - Pasta raiz (espera <pasta>/config/Advice.xml)
    - Caminho completo para o arquivo Advice.xml
    """
    folder_path = (request.folder_path or "").strip()
    if not folder_path:
        logger.error("folder_path não informado na requisição")
        raise HTTPException(status_code=400, detail="folder_path não informado")

    try:
        logger.info(f"Iniciando leitura de bases da pasta: {folder_path}")
        xml_path = _resolve_advice_xml(folder_path)
        logger.info(f"Arquivo XML resolvido: {xml_path}")
        
        bases = _extract_bases_from_xml(xml_path)
        logger.info(f"Sucesso! {len(bases)} base(s) encontrada(s)")
        
        return {
            "status": "ok",
            "folder_path": str(xml_path),
            "total": len(bases),
            "bases": bases
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao listar bases: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")

@router.get("/status/{config_key}")
async def status_configuracao(config_key: str):
    """
    Obtém status de uma configuração ativa
    """
    engine = db_manager.obter_engine(config_key)
    
    if engine is None:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    
    health = await check_db_health(config_key)
    
    return {
        "config_key": config_key,
        "status": health["status"],
        "mensagem": health["message"],
        "pool": {
            "tamanho": health.get("pool_size", 0),
            "utilizadas": health.get("pool_checked_out", 0),
            "disponiveis": health.get("pool_size", 0) - health.get("pool_checked_out", 0)
        }
    }

@router.get("/listar")
async def listar_configuracoes():
    """
    Lista todas as configurações ativas
    """
    engines = db_manager.listar_engines()
    
    return {
        "total": len(engines),
        "configuracoes": engines
    }

@router.post("/fechar/{config_key}")
async def fechar_configuracao(config_key: str):
    """
    Fecha uma configuração específica
    """
    db_manager.fechar_engine(config_key)
    
    return {
        "status": "ok",
        "mensagem": f"Configuração {config_key} fechada"
    }
