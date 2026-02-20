param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$Targets = @(
    "__pycache__",
    ".pytest_cache",
    "tmp_install",
    "temp",
    "api-gateway/main.py.backup_before_fix",
    "config_backup.py",
    "legado/migrate_to_v2.py",
    "legado/fix_imports.py",
    "venv312.backup"
)

$ExtensionsToDelete = @("*.pyc", "*.pyo")

foreach ($target in $Targets) {
    $fullPath = Join-Path $ProjectRoot $target
    if (Test-Path $fullPath) {
        if ($DryRun) { Write-Host "[DRYRUN] Remover: $fullPath" }
        else {
            Remove-Item $fullPath -Recurse -Force
            Write-Host "Removido: $fullPath" -ForegroundColor Green
        }
    }
}

foreach ($pattern in $ExtensionsToDelete) {
    Get-ChildItem -Path $ProjectRoot -Recurse -File -Filter $pattern -ErrorAction SilentlyContinue | ForEach-Object {
        if ($DryRun) { Write-Host "[DRYRUN] Remover: $($_.FullName)" }
        else {
            Remove-Item $_.FullName -Force
            Write-Host "Removido: $($_.FullName)" -ForegroundColor Green
        }
    }
}
