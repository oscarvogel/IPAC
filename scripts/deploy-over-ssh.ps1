param(
    [Parameter(Mandatory = $true)][string]$Server,
    [Parameter(Mandatory = $true)][string]$User,
    [Parameter(Mandatory = $true)][string]$RemotePath,
    [string]$Branch = "main"
)

$remoteCommand = "cd '$RemotePath' && bash scripts/deploy-production.sh '$Branch'"
ssh "$User@$Server" $remoteCommand
if ($LASTEXITCODE -ne 0) {
    throw "El despliegue remoto falló. Revisá los logs del servidor."
}
