import os
import grpc

import sys
sys.path.insert(0, os.path.dirname(__file__))

import gerador_pb2
import gerador_pb2_grpc

GRPC_HOST = os.getenv("GRPC_HOST", "localhost")
GRPC_PORT = os.getenv("GRPC_PORT", "50051")

def gerar_clientes(config: dict, config_key: str, quantidade: int, qtd_pf: int = 0, qtd_pj: int = 0):
    channel = grpc.insecure_channel(f"{GRPC_HOST}:{GRPC_PORT}")
    stub = gerador_pb2_grpc.DataGeneratorStub(channel)
    req = gerador_pb2.GenerateClientesRequest(
        config_key=config_key,
        quantidade=quantidade,
        qtd_pf=qtd_pf,
        qtd_pj=qtd_pj,
        servidor=config.get("servidor", ""),
        banco=config.get("banco", ""),
        usuario=config.get("usuario", ""),
        senha=config.get("senha", ""),
        driver=config.get("driver", "ODBC Driver 17 for SQL Server"),
    )
    return stub.GenerateClientes(req)

def job_status(job_id: str):
    channel = grpc.insecure_channel(f"{GRPC_HOST}:{GRPC_PORT}")
    stub = gerador_pb2_grpc.DataGeneratorStub(channel)
    req = gerador_pb2.JobStatusRequest(job_id=job_id)
    return stub.GetJobStatus(req)
