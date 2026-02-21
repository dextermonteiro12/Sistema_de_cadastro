$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$apiDir = Join-Path $root 'api-gateway'
$pythonExe = Join-Path $apiDir '.venv\Scripts\python.exe'

if (-not (Test-Path $pythonExe)) {
    Write-Error "Python do backend não encontrado em: $pythonExe"
}

Push-Location $apiDir
try {
    & $pythonExe -m pytest 'tests' '-q'
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
