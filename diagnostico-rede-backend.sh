#!/bin/bash
# Script para verificar conectividade do backend com SQL Server
# Execute este script NO SERVIDOR BACKEND (onde roda o Python/FastAPI)

echo "========================================"
echo "🔍 DIAGNÓSTICO DE REDE - BACKEND → SQL"
echo "========================================"
echo ""

# Verificar se está rodando no backend
echo "📍 Servidor atual (Backend):"
hostname
ip addr show | grep "inet " | grep -v "127.0.0.1"
echo ""

# Solicitar IP do SQL Server
read -p "Digite o IP do SQL Server (ex: 192.168.0.200): " SQL_SERVER

if [ -z "$SQL_SERVER" ]; then
    echo "❌ IP não informado"
    exit 1
fi

echo ""
echo "========================================"
echo "🧪 TESTES DE CONECTIVIDADE"
echo "========================================"
echo ""

# Teste 1: Ping
echo "[1/4] 🌐 Testando alcance via PING..."
if ping -c 2 $SQL_SERVER > /dev/null 2>&1; then
    echo "  ✅ Servidor responde ao ping"
else
    echo "  ⚠️  Ping bloqueado (isso é normal, continuando...)"
fi
echo ""

# Teste 2: DNS/Resolução
echo "[2/4] 🔍 Resolvendo nome/IP..."
host $SQL_SERVER > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Nome resolvido"
else
    echo "  ℹ️  IP direto (não precisa resolver)"
fi
echo ""

# Teste 3: Porta 1433
echo "[3/4] 🔌 Testando porta 1433 (TCP/IP)..."
timeout 5 bash -c "cat < /dev/null > /dev/tcp/$SQL_SERVER/1433" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  ✅ Porta 1433 está ABERTA e acessível"
    echo "     🎉 SQL Server está alcançável!"
else
    echo "  ❌ Porta 1433 está FECHADA ou bloqueada"
    echo ""
    echo "     💡 Ações necessárias NO SERVIDOR SQL ($SQL_SERVER):"
    echo "        1. Habilitar TCP/IP:"
    echo "           - SQL Server Configuration Manager"
    echo "           - Protocols for MSSQLSERVER → TCP/IP → Enable"
    echo ""
    echo "        2. Configurar porta:"
    echo "           - TCP/IP Properties → IP Addresses → IPAll"
    echo "           - TCP Port: 1433"
    echo ""
    echo "        3. Liberar firewall:"
    echo "           New-NetFirewallRule -DisplayName \"SQL Server\" \\"
    echo "             -Direction Inbound -LocalPort 1433 -Protocol TCP -Action Allow"
    echo ""
    echo "        4. Reiniciar SQL Server:"
    echo "           net stop MSSQLSERVER && net start MSSQLSERVER"
    echo ""
fi

# Teste 4: Traceroute
echo "[4/4] 🗺️  Traçando rota até o servidor..."
traceroute -m 10 -w 2 $SQL_SERVER 2>/dev/null | head -n 15
echo ""

echo "========================================"
echo "📊 RESUMO"
echo "========================================"
echo ""
echo "Servidor Backend: $(hostname)"
echo "Servidor SQL: $SQL_SERVER"
echo ""
echo "Se a porta 1433 estiver fechada:"
echo "  - Configure NO SERVIDOR SQL ($SQL_SERVER)"
echo "  - Use o script: ./teste-conexao-sql.ps1"
echo ""
echo "Documentação completa:"
echo "  - ARQUITETURA_REDE.md"
echo "  - SQL_SERVER_ACESSO_REMOTO.md"
echo ""
