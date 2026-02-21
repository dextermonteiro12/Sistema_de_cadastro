$ErrorActionPreference = 'SilentlyContinue'

$ports = @(3000, 5000, 50051)
$killed = New-Object System.Collections.Generic.HashSet[int]

Write-Host "Encerrando serviços do sistema..." -ForegroundColor Cyan

foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen
    foreach ($conn in $connections) {
        $pid = [int]$conn.OwningProcess
        if ($pid -gt 0 -and -not $killed.Contains($pid)) {
            try {
                Stop-Process -Id $pid -Force
                $killed.Add($pid) | Out-Null
                Write-Host "Porta $port liberada (PID $pid encerrado)." -ForegroundColor Yellow
            } catch {}
        }
    }
}

$patterns = @(
    'backend-start.ps1',
    'worker-start.ps1',
    'frontend-app start',
    'react-scripts start',
    'api-gateway\\main.py',
    'microservice-worker\\server.py'
)

$procs = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match 'powershell|pwsh|python|node' -and
    $_.CommandLine -and
    $_.CommandLine -match 'sistema_cadastro'
}

foreach ($proc in $procs) {
    $line = $proc.CommandLine
    $match = $false
    foreach ($pattern in $patterns) {
        if ($line -match $pattern) {
            $match = $true
            break
        }
    }

    if ($match) {
        $pid = [int]$proc.ProcessId
        if ($pid -gt 0 -and -not $killed.Contains($pid)) {
            try {
                Stop-Process -Id $pid -Force
                $killed.Add($pid) | Out-Null
                Write-Host "Processo encerrado: $($proc.Name) (PID $pid)." -ForegroundColor Yellow
            } catch {}
        }
    }
}

if ($killed.Count -eq 0) {
    Write-Host "Nenhum processo ativo do sistema foi encontrado." -ForegroundColor DarkYellow
} else {
    Write-Host "Concluído. Total de processos encerrados: $($killed.Count)." -ForegroundColor Green
}
