# api-gateway/tests/test_endpoints.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

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
        assert "status" in response.json()
        assert response.json()["status"] == "ok"
    
    def test_movimentacoes_endpoint(self):
        response = client.post("/movimentacoes", json={})
        assert response.status_code == 200
        assert "status" in response.json()
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
    
    def test_grpc_job_status(self):
        response = client.get("/grpc/job_status/invalid-job-id")
        assert response.status_code in [200, 500]