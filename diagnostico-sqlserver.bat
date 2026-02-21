@echo off
chcp 65001 >nul
echo ========================================
echo 🔍 DIAGNÓSTICO SQL SERVER - ACESSO REMOTO
echo ========================================
echo.

echo [1/7] Verificando Serviços SQL Server...
echo.
sc query MSSQLSERVER | findstr "STATE"
sc query SQLSERVERAGENT | findstr "STATE"
sc query SQLBrowser | findstr "STATE"
echo.

echo [2/7] Verificando Portas Abertas (1433 - SQL Server)...
echo.
netstat -an | findstr ":1433"
echo.

echo [3/7] Testando Conexão TCP na Porta 1433...
echo.
powershell -Command "Test-NetConnection -ComputerName localhost -Port 1433 -InformationLevel Detailed"
echo.

echo [4/7] Verificando Firewall - Regras para SQL Server...
echo.
netsh advfirewall firewall show rule name=all | findstr /C:"SQL" /C:"1433"
echo.

echo [5/7] Verificando Configuração TCP/IP do SQL Server...
echo.
echo 📝 Para verificar TCP/IP no SQL Server Configuration Manager:
echo    1. Abra: "SQL Server Configuration Manager"
echo    2. Expanda: "SQL Server Network Configuration"
echo    3. Clique: "Protocols for MSSQLSERVER"
echo    4. TCP/IP deve estar: ENABLED
echo    5. Clique duplo em TCP/IP > Aba "IP Addresses"
echo    6. Role até "IPAll" e verifique "TCP Port: 1433"
echo.

echo [6/7] Verificando Conexões Remotas Habilitadas...
echo.
echo 📝 No SQL Server Management Studio (SSMS):
echo    1. Botão direito no servidor > Properties
echo    2. Connections > "Allow remote connections to this server" ✅
echo    3. Remote query timeout: 600 (10 minutos)
echo.

echo [7/7] Informações de Rede do Servidor...
echo.
ipconfig | findstr /C:"IPv4" /C:"Subnet"
echo.

echo ========================================
echo ⚙️ COMANDOS PARA CORRIGIR PROBLEMAS
echo ========================================
echo.
echo 🔧 1. Habilitar SQL Server Browser:
echo    sc config SQLBrowser start= auto
echo    net start SQLBrowser
echo.
echo 🔧 2. Criar Regra de Firewall para Porta 1433:
echo    New-NetFirewallRule -DisplayName "SQL Server 1433" -Direction Inbound -LocalPort 1433 -Protocol TCP -Action Allow
echo.
echo 🔧 3. Criar Regra de Firewall para SQL Browser (UDP 1434):
echo    New-NetFirewallRule -DisplayName "SQL Browser" -Direction Inbound -LocalPort 1434 -Protocol UDP -Action Allow
echo.
echo 🔧 4. Reiniciar Serviço SQL Server:
echo    net stop MSSQLSERVER
echo    net start MSSQLSERVER
echo.
echo 🔧 5. Habilitar TCP/IP (via PowerShell - requer SQL Server PowerShell):
echo    Import-Module SQLPS
echo    $smo = 'Microsoft.SqlServer.Management.Smo.'
echo    $wmi = New-Object ($smo + 'Wmi.ManagedComputer')
echo    $tcp = $wmi.ServerInstances['MSSQLSERVER'].ServerProtocols['Tcp']
echo    $tcp.IsEnabled = $true
echo    $tcp.Alter()
echo.

echo ========================================
echo 📋 CHECKLIST DE VERIFICAÇÃO
echo ========================================
echo.
echo [ ] SQL Server Service está rodando
echo [ ] SQL Browser Service está rodando
echo [ ] TCP/IP está habilitado no Configuration Manager
echo [ ] Porta 1433 está aberta no firewall
echo [ ] "Allow remote connections" está habilitado
echo [ ] Autenticação SQL Server está habilitada (Mixed Mode)
echo [ ] Usuário SQL tem permissões no banco
echo.

echo ========================================
echo 🧪 TESTE MANUAL DE CONEXÃO
echo ========================================
echo.
echo Execute no PowerShell para testar conexão:
echo.
echo $server = "192.168.0.119,1433"
echo $database = "CORP"
echo $username = "sa"
echo $password = "sua_senha"
echo.
echo $connectionString = "Server=$server;Database=$database;User Id=$username;Password=$password;"
echo $connection = New-Object System.Data.SqlClient.SqlConnection($connectionString)
echo try { $connection.Open(); Write-Host "✅ CONEXÃO OK" -ForegroundColor Green; $connection.Close() }
echo catch { Write-Host "❌ ERRO: $_" -ForegroundColor Red }
echo.

echo ========================================
pause
