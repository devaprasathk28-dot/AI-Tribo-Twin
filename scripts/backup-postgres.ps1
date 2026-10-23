param(
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$containerBackup = "/tmp/tribotwin-backup-$([guid]::NewGuid().ToString('N')).dump"

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $backupDirectory = Join-Path $projectRoot "backups"
    New-Item -ItemType Directory -Force -Path $backupDirectory | Out-Null
    $OutputPath = Join-Path $backupDirectory ("tribotwin-{0}.dump" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
}

$destination = [System.IO.Path]::GetFullPath($OutputPath)
if (Test-Path $destination) {
    throw "Refusing to overwrite existing backup: $destination"
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
Push-Location $projectRoot
try {
    docker compose exec -T db pg_dump --username=tribotwin --dbname=tribotwin --format=custom --file=$containerBackup
    if ($LASTEXITCODE -ne 0) {
        throw "PostgreSQL backup failed with exit code $LASTEXITCODE."
    }

    docker compose cp "db:$containerBackup" $destination
    if ($LASTEXITCODE -ne 0) {
        throw "Could not copy the PostgreSQL backup to $destination."
    }

    if ((Get-Item $destination).Length -eq 0) {
        throw "PostgreSQL created an empty backup file: $destination"
    }
    Write-Output "PostgreSQL backup created: $destination"
}
finally {
    docker compose exec -T db rm -f $containerBackup | Out-Null
    Pop-Location
}
