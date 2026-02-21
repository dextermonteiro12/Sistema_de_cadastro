$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$workerDir = Join-Path $root 'microservice-worker'
$pythonExe = Join-Path $workerDir '.venv\Scripts\python.exe'
$testsDir = Join-Path $root 'worker\tests'

if (-not (Test-Path $pythonExe)) {
    Write-Error "Python do worker não encontrado em: $pythonExe"
}

if (-not (Test-Path $testsDir)) {
    Write-Error "Pasta de testes do worker não encontrada em: $testsDir"
}

& $pythonExe -m pytest $testsDir '-q'
exit $LASTEXITCODE
