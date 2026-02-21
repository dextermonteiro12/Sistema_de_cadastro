# Script simplificado para testar conexao SQL Server
param(
    [string]$SqlServer,
    [string]$Database = "master",
    [string]$Username,
    [string]$Password
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TESTE DE CONEXAO SQL SERVER" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Solicitar informacoes se nao foram passadas
if (-not $SqlServer) {
    $SqlServer = Read-Host "Digite o IP ou nome do servidor SQL (ex: ADV-NOT000337)"
}

if (-not $Username) {
    $Username = Read-Host "Digite o usuario SQL"
}

if (-not $Password) {
    $securePassword = Read-Host "Digite a senha" -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
    $Password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
}

Write-Host ""
Write-Host "Configuracao do Teste:" -ForegroundColor Yellow
Write-Host "  - Servidor SQL: $SqlServer" -ForegroundColor White
Write-Host "  - Banco: $Database" -ForegroundColor White
Write-Host "  - Usuario: $Username" -ForegroundColor White
Write-Host ""

# Extrair IP
$serverIP = $SqlServer -replace ',.*$', ''
$serverIP = $serverIP -replace ':.*$', ''

# Adicionar porta se não tiver
$serverWithPort = $SqlServer
if ($SqlServer -notmatch '[,:]') {
    $serverWithPort = "$SqlServer,1433"
}

# TESTE 1: PING
Write-Host "[1/3] Testando alcance do servidor (PING)..." -ForegroundColor Cyan
try {
    $ping = Test-Connection -ComputerName $serverIP -Count 2 -Quiet -ErrorAction Stop
    if ($ping) {
        Write-Host "  [OK] Servidor responde ao ping" -ForegroundColor Green
    } else {
        Write-Host "  [AVISO] Servidor nao responde ao ping" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [AVISO] Ping bloqueado (isso e normal)" -ForegroundColor Yellow
}
Write-Host ""

# TESTE 2: PORTA 1433
Write-Host "[2/3] Testando porta 1433 (TCP/IP)..." -ForegroundColor Cyan
try {
    $portTest = Test-NetConnection -ComputerName $serverIP -Port 1433 -WarningAction SilentlyContinue
    if ($portTest.TcpTestSucceeded) {
        Write-Host "  [OK] Porta 1433 esta ABERTA e acessivel" -ForegroundColor Green
    } else {
        Write-Host "  [ERRO] Porta 1433 esta FECHADA ou bloqueada" -ForegroundColor Red
        Write-Host ""
        Write-Host "  Acoes necessarias NO SERVIDOR SQL ($serverIP):" -ForegroundColor Yellow
        Write-Host "    1. Habilitar TCP/IP no SQL Server Configuration Manager" -ForegroundColor White
        Write-Host "    2. Configurar porta 1433 em TCP/IP Properties" -ForegroundColor White
        Write-Host "    3. Liberar porta 1433 no Firewall do Windows" -ForegroundColor White
        Write-Host "    4. Reiniciar servico SQL Server" -ForegroundColor White
    }
} catch {
    Write-Host "  [ERRO] Nao foi possivel testar porta: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# TESTE 3: CONEXAO SQL
Write-Host "[3/3] Testando autenticacao SQL (com porta ,1433)..." -ForegroundColor Cyan

$connectionString = "Server=$serverWithPort;Database=$Database;User Id=$Username;Password=$Password;TrustServerCertificate=True;Connection Timeout=15"
$connection = New-Object System.Data.SqlClient.SqlConnection($connectionString)

try {
    Write-Host "  Tentando conectar..." -ForegroundColor Gray
    $connection.Open()
    Write-Host "  [SUCESSO] CONEXAO ESTABELECIDA!" -ForegroundColor Green
    Write-Host ""
    
    $command = $connection.CreateCommand()
    $command.CommandText = "SELECT @@VERSION AS Version, DB_NAME() AS CurrentDB, SUSER_NAME() AS CurrentUser"
    $reader = $command.ExecuteReader()
    
    if ($reader.Read()) {
        Write-Host "  Informacoes da Conexao:" -ForegroundColor Cyan
        $version = $reader['Version'].ToString().Split([char]10)[0]
        Write-Host "    - Versao SQL: $version" -ForegroundColor White
        Write-Host "    - Banco conectado: $($reader['CurrentDB'])" -ForegroundColor White
        Write-Host "    - Usuario autenticado: $($reader['CurrentUser'])" -ForegroundColor White
    }
    
    $reader.Close()
    $connection.Close()
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "SUCESSO TOTAL!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "O backend consegue acessar o SQL Server!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Atualize o XML do Advice com:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  <Servidor>$serverWithPort</Servidor>" -ForegroundColor White
    Write-Host "  <Usuario>$Username</Usuario>" -ForegroundColor White
    Write-Host "  <Senha>SuaSenhaAqui</Senha>" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "  [ERRO] Falha na conexao" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Mensagem de erro: $($_.Exception.Message)" -ForegroundColor Gray
    Write-Host ""
    
    # Diagnostico detalhado
    $errorMsg = $_.Exception.Message.ToLower()
    
    if ($errorMsg -match "login failed") {
        Write-Host "  [DIAGNOSTICO] Problema: Credenciais incorretas" -ForegroundColor Yellow
        Write-Host "    - Verifique usuario e senha no XML" -ForegroundColor White
        Write-Host "    - Confirme que o usuario existe no SQL Server" -ForegroundColor White
        Write-Host "    - Verifique se SQL Server esta em Mixed Mode (SQL + Windows Auth)" -ForegroundColor White
    }
    elseif ($errorMsg -match "cannot open database") {
        Write-Host "  [DIAGNOSTICO] Problema: Banco '$Database' nao encontrado" -ForegroundColor Yellow
        Write-Host "    - Verifique o nome do banco no XML" -ForegroundColor White
        Write-Host "    - Execute no SQL Server: SELECT name FROM sys.databases" -ForegroundColor White
    }
    elseif ($errorMsg -match "timeout" -or $errorMsg -match "wait operation timed out") {
        Write-Host "  [DIAGNOSTICO] Problema: Timeout ao conectar" -ForegroundColor Yellow
        Write-Host "    - O backend nao conseguiu alcançar o SQL Server em 15 segundos" -ForegroundColor White
        Write-Host "    - Verifique firewall NO SERVIDOR SQL ($serverIP)" -ForegroundColor White
        Write-Host "    - Verifique se SQL Server esta rodando" -ForegroundColor White
        Write-Host "    - Verifique se TCP/IP esta habilitado" -ForegroundColor White
    }
    else {
        Write-Host "  [DIAGNOSTICO] Erro desconhecido" -ForegroundColor Yellow
        Write-Host "    - Verifique os logs do SQL Server" -ForegroundColor White
        Write-Host "    - Verifique configuracoes de rede" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "Documentacao:" -ForegroundColor Cyan
    Write-Host "  - TROUBLESHOOTING_SQL_TIMEOUT.md" -ForegroundColor White
    Write-Host "  - SQL_SERVER_ACESSO_REMOTO.md" -ForegroundColor White
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fim do teste" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
