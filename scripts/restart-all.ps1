$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot

Write-Host "Reiniciando sistema completo..." -ForegroundColor Cyan

powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'stop-all.ps1')
Start-Sleep -Seconds 2
powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'start-all.ps1')

Write-Host "Restart concluído." -ForegroundColor Green
