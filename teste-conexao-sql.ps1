# Script para testar conexão do BACKEND com SQL Server remoto
param(
    [Parameter(Mandatory=$false)]
    [string]$SqlServer,
    
    [Parameter(Mandatory=$false)]
    [string]$Database = "master",
    
    [Parameter(Mandatory=$false)]
    [string]$Username,
    
    [Parameter(Mandatory=$false)]
    [string]$Password
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🔍 TESTE DE CONEXÃO SQL SERVER REMOTO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Se não foram passados parâmetros, solicitar
if (-not $SqlServer) {
    $SqlServer = Read-Host "Digite o IP ou nome do servidor SQL (ex: 192.168.0.200)"
}

if (-not $Username) {
    $Username = Read-Host "Digite o usuário SQL"
}

if (-not $Password) {
    $securePassword = Read-Host "Digite a senha" -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
    $Password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
}

Write-Host ""
Write-Host "📋 Configuração do Teste:" -ForegroundColor Yellow
Write-Host "  - Servidor SQL: $SqlServer" -ForegroundColor White
Write-Host "  - Banco: $Database" -ForegroundColor White
Write-Host "  - Usuário: $Username" -ForegroundColor White
Write-Host ""

# Extrair IP se tiver porta
$serverIP = $SqlServer -replace ',.*$', ''
$serverIP = $serverIP -replace ':.*$', ''

# ==============================================
# TESTE 1: PING
# ==============================================
Write-Host "[1/5] 🌐 Testando alcance do servidor (PING)..." -ForegroundColor Cyan
try {
    $ping = Test-Connection -ComputerName $serverIP -Count 2 -Quiet -ErrorAction Stop
    if ($ping) {
        Write-Host "  ✅ Servidor responde ao ping" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Servidor não responde ao ping (pode estar bloqueado, mas SQL pode funcionar)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠️  Ping bloqueado (isso é normal, continuando...)" -ForegroundColor Yellow
}
Write-Host ""

# ==============================================
# TESTE 2: PORTA 1433
# ==============================================
Write-Host "[2/5] 🔌 Testando porta 1433 (TCP/IP)..." -ForegroundColor Cyan
try {
    $portTest = Test-NetConnection -ComputerName $serverIP -Port 1433 -WarningAction SilentlyContinue
    if ($portTest.TcpTestSucceeded) {
        Write-Host "  ✅ Porta 1433 está ABERTA e acessível" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Porta 1433 está FECHADA ou bloqueada" -ForegroundColor Red
        Write-Host "     💡 Ações necessárias NO SERVIDOR SQL ($serverIP):" -ForegroundColor Yellow
        Write-Host "        1. Habilitar TCP/IP no SQL Server Configuration Manager" -ForegroundColor White
        Write-Host "        2. Configurar porta 1433 em TCP/IP Properties" -ForegroundColor White
        Write-Host "        3. Liberar porta 1433 no Firewall do Windows" -ForegroundColor White
        Write-Host "        4. Reiniciar serviço SQL Server" -ForegroundColor White
    }
} catch {
    Write-Host "  ❌ Erro ao testar porta: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# ==============================================
# TESTE 3: CONEXÃO SQL (SEM PORTA)
# ==============================================
Write-Host "[3/5] 🔐 Testando autenticação SQL (sem porta explícita)..." -ForegroundColor Cyan
$connectionString1 = "Server=$SqlServer;Database=$Database;User Id=$Username;Password=$Password;TrustServerCertificate=True;Connection Timeout=10"
$connection1 = New-Object System.Data.SqlClient.SqlConnection($connectionString1)

try {
    $connection1.Open()
    Write-Host "  ✅ CONEXÃO ESTABELECIDA (sem porta explícita)" -ForegroundColor Green
    
    $command = $connection1.CreateCommand()
    $command.CommandText = "SELECT @@VERSION AS Version, DB_NAME() AS CurrentDB, SUSER_NAME() AS CurrentUser"
    $reader = $command.ExecuteReader()
    
    if ($reader.Read()) {
        Write-Host "     📊 Versão SQL: $($reader['Version'].Split("`n")[0])" -ForegroundColor Cyan
        Write-Host "     📊 Banco conectado: $($reader['CurrentDB'])" -ForegroundColor Cyan
        Write-Host "     📊 Usuário autenticado: $($reader['CurrentUser'])" -ForegroundColor Cyan
    }
    
    $reader.Close()
    $connection1.Close()
} catch {
    Write-Host "  ❌ FALHA na conexão (sem porta)" -ForegroundColor Red
    Write-Host "     Erro: $($_.Exception.Message)" -ForegroundColor Gray
}
Write-Host ""

# ==============================================
# TESTE 4: CONEXÃO SQL (COM PORTA ,1433)
# ==============================================
Write-Host "[4/5] 🔐 Testando autenticação SQL (com porta ,1433)..." -ForegroundColor Cyan

# Adicionar porta se não tiver
$serverWithPort = $SqlServer
if ($SqlServer -notmatch '[,:]') {
    $serverWithPort = "$SqlServer,1433"
}

$connectionString2 = "Server=$serverWithPort;Database=$Database;User Id=$Username;Password=$Password;TrustServerCertificate=True;Connection Timeout=10"
$connection2 = New-Object System.Data.SqlClient.SqlConnection($connectionString2)

try {
    $connection2.Open()
    Write-Host "  ✅ CONEXÃO ESTABELECIDA (com porta ,1433)" -ForegroundColor Green
    
    $command = $connection2.CreateCommand()
    $command.CommandText = "SELECT @@VERSION AS Version, DB_NAME() AS CurrentDB, SUSER_NAME() AS CurrentUser"
    $reader = $command.ExecuteReader()
    
    if ($reader.Read()) {
        Write-Host "     📊 Versão SQL: $($reader['Version'].Split("`n")[0])" -ForegroundColor Cyan
        Write-Host "     📊 Banco conectado: $($reader['CurrentDB'])" -ForegroundColor Cyan
        Write-Host "     📊 Usuário autenticado: $($reader['CurrentUser'])" -ForegroundColor Cyan
    }
    
    $reader.Close()
    $connection2.Close()
    
    Write-Host ""
    Write-Host "  🎉 SUCESSO TOTAL! O backend consegue acessar o SQL Server!" -ForegroundColor Green
    
} catch {
    Write-Host "  ❌ FALHA na conexão (com porta ,1433)" -ForegroundColor Red
    Write-Host "     Erro: $($_.Exception.Message)" -ForegroundColor Gray
    
    # Diagnóstico detalhado de erro
    if ($_.Exception.Message -match "Login failed") {
        Write-Host ""
        Write-Host "  💡 PROBLEMA: Credenciais incorretas ou usuário sem permissão" -ForegroundColor Yellow
        Write-Host "     Soluções:" -ForegroundColor White
        Write-Host "     1. Verifique usuário e senha no XML" -ForegroundColor White
        Write-Host "     2. No servidor SQL, execute:" -ForegroundColor White
        Write-Host "        SELECT name FROM sys.server_principals WHERE name = '$Username'" -ForegroundColor Gray
        Write-Host "     3. Crie o usuário se não existir:" -ForegroundColor White
        Write-Host "        CREATE LOGIN [$Username] WITH PASSWORD = 'SuaSenha'" -ForegroundColor Gray
    }
    elseif ($_.Exception.Message -match "timeout|network") {
        Write-Host ""
        Write-Host "  💡 PROBLEMA: Timeout de rede ou servidor inacessível" -ForegroundColor Yellow
        Write-Host "     Soluções:" -ForegroundColor White
        Write-Host "     1. Verificar firewall NO SERVIDOR SQL ($serverIP)" -ForegroundColor White
        Write-Host "     2. Verificar se SQL Server está rodando" -ForegroundColor White
        Write-Host "     3. Verificar se TCP/IP está habilitado" -ForegroundColor White
    }
}
Write-Host ""

# ==============================================
# TESTE 5: VERIFICAR PERMISSÕES
# ==============================================
Write-Host "[5/5] 🔑 Verificando permissões do usuário..." -ForegroundColor Cyan

if ($connection2.State -eq [System.Data.ConnectionState]::Open) {
    $connection2.Open()
}

try {
    if ($connection2.State -ne [System.Data.ConnectionState]::Open) {
        # Tentar reabrir
        $connection2.Open()
    }
    
    $command = $connection2.CreateCommand()
    $command.CommandText = "SELECT DB_NAME() AS DatabaseName, IS_SRVROLEMEMBER('sysadmin') AS IsSysAdmin"
    $reader = $command.ExecuteReader()
    
    if ($reader.Read()) {
        Write-Host "  [Permissoes]" -ForegroundColor Cyan
        Write-Host "     - Banco: $($reader['DatabaseName'])" -ForegroundColor White
        
        if ($reader['IsSysAdmin'] -eq 1) {
            Write-Host "     - SysAdmin: SIM" -ForegroundColor Green
        } else {
            Write-Host "     - SysAdmin: NAO" -ForegroundColor Yellow
        }
    }
    
    $reader.Close()
    $connection2.Close()
} catch {
    Write-Host "  ⚠️  Não foi possível verificar permissões" -ForegroundColor Yellow
}
Write-Host ""

# ==============================================
# RESUMO FINAL
# ================[AVISO] Nao foi possivel verificar permisso
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📊 RESUMO DO DIAGNÓSTICO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Connection String que funcionou:" -ForegroundColor Yellow
Write-Host "Server=$serverWithPort;Database=$Database;User Id=$Username;Password=***;TrustServerCertificate=True" -ForegroundColor White
Write-Host ""
Write-Host "Para usar no XML do Advice:" -ForegroundColor Yellow
Write-Host "  <Servidor>$serverWithPort</Servidor>" -ForegroundColor White
Write-Host "  <Usuario>$Username</Usuario>" -ForegroundColor White
Write-Host "  <Senha>SuaSenhaAqui</Senha>" -ForegroundColor White
Write-Host ""
