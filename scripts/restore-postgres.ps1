param(
    [Parameter(Mandatory = $true)]
    [string]$Backup
)

$ErrorActionPreference = "Stop"
$resolvedBackup = (Resolve-Path -LiteralPath $Backup).Path
if ([System.IO.Path]::GetExtension($resolvedBackup) -ne ".dump") { throw "El archivo debe ser un backup .dump de PostgreSQL." }

Write-Warning "La restauración reemplazará los objetos existentes de la base IPAC. Ejecútela primero en un entorno de prueba."
$containerId = (docker compose ps -q db).Trim()
if (-not $containerId) { throw "El contenedor de PostgreSQL no está en ejecución." }
docker cp $resolvedBackup "${containerId}:/tmp/ipac-restore.dump"
docker compose exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner /tmp/ipac-restore.dump'
docker compose exec -T db rm -f /tmp/ipac-restore.dump

docker compose exec -T backend python manage.py check
Write-Output "Restauración completada y validada con manage.py check."
