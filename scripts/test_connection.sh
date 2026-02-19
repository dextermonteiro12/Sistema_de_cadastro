#!/usr/bin/env bash
# scripts/test_connection.sh - Testar conexão com banco de dados

source "$(dirname "$0")/_common.sh"

API_URL="${API_URL:-http://localhost:5000}"

echo "=== DIAGNÓSTICO DE CONEXÃO ==="
echo ""

# 1. Verificar se a API está rodando
echo "1. Verificando se API está rodando..."
if curl -fsS "$API_URL/health" >/dev/null 2>&1; then
  echo "   ✓ API online"
else
  echo "   ✗ API OFFLINE"
  exit 1
fi

echo ""
echo "2. Qual é sua config_key?"
echo "   (Você deve ter visto isso ao fazer login no seu sistema)"
echo ""
read -p "config_key: " config_key

if [[ -z "$config_key" ]]; then
  echo "❌ Config_key não fornecida"
  exit 1
fi

echo ""
echo "=== TESTANDO SAÚDE DO SERVIDOR ==="
echo "URL: $API_URL/api/saude-servidor"
echo "Config Key: $config_key"
echo ""

response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/saude-servidor" \
  -H "Content-Type: application/json" \
  -H "X-Config-Key: $config_key" \
  -d "{\"config_key\":\"$config_key\"}")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

echo "Status HTTP: $http_code"
echo "Resposta:"
echo "$body"

if [[ "$http_code" == "200" ]]; then
  echo ""
  echo "✓ Conexão funcionando!"
else
  echo ""
  echo "✗ Erro na conexão"
  echo ""
  echo "Possíveis causas:"
  echo "  1. config_key inválida"
  echo "  2. Banco de dados offline"
  echo "  3. Credenciais incorretas"
fi

echo ""
echo "=== TESTANDO CLIENTES PENDENTES ==="
echo ""

response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/clientes-pendentes" \
  -H "Content-Type: application/json" \
  -H "X-Config-Key: $config_key" \
  -d "{\"config_key\":\"$config_key\"}")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

echo "Status HTTP: $http_code"
echo "Resposta:"
echo "$body"

echo ""
echo "=== FIM DO DIAGNÓSTICO ==="