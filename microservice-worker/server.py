import grpc
from concurrent import futures
import time
import uuid
import random
import threading
import pyodbc

import gerador_pb2
import gerador_pb2_grpc

JOBS = {}
JOBS_LOCK = threading.Lock()

def _build_conn_str(servidor, banco, usuario, senha, driver):
    drv = (driver or "ODBC Driver 17 for SQL Server").strip("{}")
    return (
        f"DRIVER={{{drv}}};"
        f"SERVER={servidor};"
        f"DATABASE={banco};"
        f"UID={usuario};"
        f"PWD={senha};"
        f"TrustServerCertificate=yes;"
    )

def _set_job(job_id, status, percent, inserted, message):
    with JOBS_LOCK:
        JOBS[job_id] = {
            "status": status,
            "percent": int(percent),
            "inserted": int(inserted),
            "message": message
        }

def _run_insert(job_id, req):
    try:
        _set_job(job_id, "running", 0, 0, "starting")
        conn_str = _build_conn_str(req.servidor, req.banco, req.usuario, req.senha, req.driver)
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.fast_executemany = True

        total = int(req.quantidade or 0)
        batch_size = 1000
        inserted = 0

        while inserted < total:
            current = min(batch_size, total - inserted)
            rows = []
            for _ in range(current):
                cd_cliente = uuid.uuid4().hex[:20].upper()
                de_cliente = f"CLIENTE_{random.randint(1000, 9999)}"
                rows.append((cd_cliente, de_cliente))

            cursor.executemany(
                "INSERT INTO TAB_CLIENTES_PLD (CD_CLIENTE, DE_CLIENTE) VALUES (?, ?)",
                rows
            )
            conn.commit()

            inserted += current
            percent = int((inserted / total) * 100) if total > 0 else 100
            _set_job(job_id, "running", percent, inserted, "inserting")

        cursor.close()
        conn.close()
        _set_job(job_id, "done", 100, inserted, "completed")

    except Exception as e:
        _set_job(job_id, "error", 0, 0, str(e))

class DataGeneratorService(gerador_pb2_grpc.DataGeneratorServicer):
    def GenerateClientes(self, request, context):
        job_id = str(uuid.uuid4())[:8]
        _set_job(job_id, "queued", 0, 0, "queued")
        t = threading.Thread(target=_run_insert, args=(job_id, request), daemon=True)
        t.start()

        return gerador_pb2.GenerateClientesResponse(
            status="accepted",
            job_id=job_id,
            message="job queued",
            inserted=0
        )

    def GetJobStatus(self, request, context):
        with JOBS_LOCK:
            data = JOBS.get(request.job_id)
        if not data:
            return gerador_pb2.JobStatusResponse(
                status="not_found",
                percent=0,
                inserted=0,
                message="job not found"
            )
        return gerador_pb2.JobStatusResponse(
            status=data["status"],
            percent=data["percent"],
            inserted=data["inserted"],
            message=data["message"]
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    gerador_pb2_grpc.add_DataGeneratorServicer_to_server(DataGeneratorService(), server)
    server.add_insecure_port("0.0.0.0:50051")
    server.start()
    print("gRPC worker listening on 0.0.0.0:50051")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    serve()
