# 🚀 PLD Data Generator v2.0 - Arquitetura de Alta Performance

## 🏗️ Estrutura do Projeto
O projeto foi organizado para suportar alta carga e processamento distribuído.

## 🚀 Como Iniciar
1. Configure seu `.env` com as credenciais do SQL Server.
2. Instale as dependências: `pip install -r api-gateway/requirements.txt`
3. Execute a API: `python api-gateway/main.py`

## 🧭 Execução Padronizada (.venv por módulo)
Use os scripts abaixo para sempre rodar cada serviço com o `.venv` correto:

- `npm run backend:start` → sobe `api-gateway` com `api-gateway/.venv`
- `npm run backend:test` → roda testes do `api-gateway` com `api-gateway/.venv`
- `npm run worker:start` → sobe `microservice-worker` com `microservice-worker/.venv`
- `npm run worker:test` → roda testes reais do `worker/tests` com `microservice-worker/.venv`
- `npm run test:all` → executa backend + worker
