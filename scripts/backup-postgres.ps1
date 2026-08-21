param(
    [string]$Destination = ".\backups",
    [int]$RetentionDays = 14
)

$ErrorActionPreference = "Stop"
$backupRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\$Destination"))
New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$target = Join-Path $backupRoot "ipac-$timestamp.dump"

$containerId = (docker compose ps -q db).Trim()
if (-not $containerId) { throw "El contenedor de PostgreSQL no está en ejecución." }
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/ipac-backup.dump'
docker cp "${containerId}:/tmp/ipac-backup.dump" $target
docker compose exec -T db rm -f /tmp/ipac-backup.dump
if ((Get-Item -LiteralPath $target).Length -eq 0) { throw "El backup se generó vacío." }

$limit = (Get-Date).AddDays(-$RetentionDays)
Get-ChildItem -LiteralPath $backupRoot -Filter "ipac-*.dump" -File |
    Where-Object { $_.LastWriteTime -lt $limit } |
    Remove-Item -Force

Write-Output "Backup creado: $target"
