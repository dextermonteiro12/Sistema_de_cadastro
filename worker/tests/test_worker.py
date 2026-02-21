import importlib.util
import sys
import types
import uuid
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
WORKER_SOURCE_DIR = WORKSPACE_ROOT / "microservice-worker"
SERVER_FILE = WORKER_SOURCE_DIR / "server.py"

if str(WORKER_SOURCE_DIR) not in sys.path:
	sys.path.insert(0, str(WORKER_SOURCE_DIR))

if "pyodbc" not in sys.modules:
	pyodbc_stub = types.ModuleType("pyodbc")

	def _connect_not_implemented(*args, **kwargs):
		raise RuntimeError("pyodbc.connect não deve ser chamado neste teste")

	pyodbc_stub.connect = _connect_not_implemented
	sys.modules["pyodbc"] = pyodbc_stub

spec = importlib.util.spec_from_file_location("worker_server_under_test", SERVER_FILE)
server = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(server)


def test_build_conn_str_uses_default_driver_when_empty():
	conn_str = server._build_conn_str("sql-host", "DB1", "sa", "secret", "")
	assert "DRIVER={ODBC Driver 17 for SQL Server};" in conn_str
	assert "SERVER=sql-host;" in conn_str
	assert "DATABASE=DB1;" in conn_str


def test_get_job_status_returns_not_found_for_unknown_job():
	service = server.DataGeneratorService()
	request = server.gerador_pb2.JobStatusRequest(job_id="missing-job")

	response = service.GetJobStatus(request, None)

	assert response.status == "not_found"
	assert response.percent == 0
	assert response.inserted == 0


def test_set_job_and_get_job_status_returns_current_state():
	job_id = "job-status-1"
	server._set_job(job_id, "running", 55, 11, "inserting")

	service = server.DataGeneratorService()
	request = server.gerador_pb2.JobStatusRequest(job_id=job_id)
	response = service.GetJobStatus(request, None)

	assert response.status == "running"
	assert response.percent == 55
	assert response.inserted == 11
	assert response.message == "inserting"


def test_generate_clientes_queues_job_and_starts_thread(monkeypatch):
	captured = {}

	class DummyThread:
		def __init__(self, target, args, daemon):
			captured["target"] = target
			captured["args"] = args
			captured["daemon"] = daemon

		def start(self):
			captured["started"] = True

	monkeypatch.setattr(server.threading, "Thread", DummyThread)
	monkeypatch.setattr(server.uuid, "uuid4", lambda: uuid.UUID("12345678-1234-5678-1234-567812345678"))

	service = server.DataGeneratorService()
	request = server.gerador_pb2.GenerateClientesRequest(
		servidor="host",
		banco="db",
		usuario="user",
		senha="pwd",
		driver="",
		quantidade=10,
	)

	response = service.GenerateClientes(request, None)

	assert response.status == "accepted"
	assert response.job_id == "12345678"
	assert response.message == "job queued"
	assert captured["started"] is True
	assert captured["target"] == server._run_insert
	assert captured["args"][0] == response.job_id
	assert captured["daemon"] is True

	with server.JOBS_LOCK:
		queued_job = server.JOBS.get(response.job_id)
	assert queued_job["status"] == "queued"
	assert queued_job["percent"] == 0
