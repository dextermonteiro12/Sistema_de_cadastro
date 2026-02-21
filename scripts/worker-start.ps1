$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$workerDir = Join-Path $root 'microservice-worker'
$pythonExe = Join-Path $workerDir '.venv\Scripts\python.exe'

if (-not (Test-Path $pythonExe)) {
    Write-Error "Python do worker não encontrado em: $pythonExe"
}

Push-Location $workerDir
try {
    & $pythonExe 'server.py'
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
