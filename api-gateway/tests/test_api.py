# api-gateway/tests/test_api.py (ATUALIZADO)
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestHealthEndpoints:
    """Teste dos endpoints de saúde"""
    
    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "PLD Data Generator API v2.0"
    
    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "online"
        assert response.json()["version"] == "2.0.0"

class TestAuthEndpoints:
    """Teste de autenticação"""
    
    def test_login_success(self):
        response = client.post("/login", json={
            "username": "admin",
            "password": "1234"
        })
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_login_failure(self):
        response = client.post("/login", json={
            "username": "wrong",
            "password": "wrong"
        })
        assert response.status_code == 401

class TestClientesPendentesEndpoint:
    """Teste do endpoint de clientes pendentes"""
    
    def test_clientes_pendentes_sem_config_key(self):
        """Deve retornar 400 se config_key não for fornecido"""
        response = client.post("/api/clientes-pendentes", json={})
        assert response.status_code == 400
        assert "config_key" in response.json()["erro"]
    
    @patch('database.get_db_session')
    def test_clientes_pendentes_com_config_key_valida(self, mock_db):
        """Teste com mock do banco de dados"""
        mock_session = MagicMock()
        mock_session.execute.return_value.fetchone.return_value = (5,)
        mock_db.return_value.__enter__.return_value = mock_session
        
        response = client.post(
            "/api/clientes-pendentes",
            json={"config_key": "test-config"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert "quantidade" in response.json()

class TestUtilityEndpoints:
    """Teste dos endpoints utilitários"""
    
    def test_gerar_clientes_endpoint(self):
        response = client.post("/gerar_clientes", json={
            "config_key": "test",
            "quantidade": 100
        })
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_monitoramento_endpoint(self):
        response = client.post("/monitoramento", json={})
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_movimentacoes_endpoint(self):
        response = client.post("/movimentacoes", json={})
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

class TestAmbienteEndpoints:
    """Teste dos endpoints de ambiente"""
    
    def test_check_ambiente_sem_config(self):
        response = client.post("/check_ambiente", json={})
        assert response.status_code == 400
    
    def test_setup_ambiente_sem_config(self):
        response = client.post("/setup_ambiente", json={})
        assert response.status_code == 400

class TestgRPCEndpoints:
    """Teste dos endpoints gRPC"""
    
    def test_grpc_gerar_clientes_sem_config(self):
        response = client.post("/grpc/gerar_clientes", json={})
        assert response.status_code == 400

class TestClientesPendentesEndpoint:
    """Teste do endpoint de clientes pendentes"""
    
    def test_clientes_pendentes_sem_config_key(self):
        """Deve retornar 400 se config_key não for fornecido"""
        response = client.post("/api/clientes-pendentes", json={})
        assert response.status_code == 400
        assert "config_key" in response.json()["erro"]
    
    @patch('main.get_db_session')
    def test_clientes_pendentes_com_mock_db(self, mock_db):
        """Teste com mock correto do banco de dados"""
        # Criar mock da sessão
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (5,)
        mock_session.execute.return_value = mock_result
        
        # Configurar context manager
        mock_db.return_value.__enter__.return_value = mock_session
        mock_db.return_value.__exit__.return_value = None
        
        response = client.post(
            "/api/clientes-pendentes",
            json={"config_key": "test-config"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "quantidade" in data