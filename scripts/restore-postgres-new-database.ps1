param(
    [Parameter(Mandatory = $true)]
    [string]$BackupPath,

    [Parameter(Mandatory = $true)]
    [ValidatePattern("^tribotwin_restore_[A-Za-z0-9_]+$")]
    [string]$TargetDatabase
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$backup = (Resolve-Path $BackupPath).Path
$containerBackup = "/tmp/tribotwin-restore-$([guid]::NewGuid().ToString('N')).dump"

if ($TargetDatabase -eq "tribotwin") {
    throw "Restore target must be a new tribotwin_restore_* database, never the application database."
}

Push-Location $projectRoot
try {
    $exists = docker compose exec -T db psql --username=tribotwin --dbname=postgres --tuples-only --no-align --command="SELECT 1 FROM pg_database WHERE datname = '$TargetDatabase'"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not check PostgreSQL for an existing restore target."
    }
    if (($exists | Out-String).Trim() -eq "1") {
        throw "Restore target already exists; refusing to overwrite database $TargetDatabase."
    }

    docker compose cp $backup "db:$containerBackup"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not copy backup into the PostgreSQL container."
    }

    docker compose exec -T db pg_restore --list $containerBackup | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Backup archive is invalid or unreadable."
    }

    docker compose exec -T db createdb --username=tribotwin $TargetDatabase
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create isolated restore database $TargetDatabase."
    }

    docker compose exec -T db pg_restore --username=tribotwin --dbname=$TargetDatabase --no-owner --exit-on-error $containerBackup
    if ($LASTEXITCODE -ne 0) {
        throw "Restore failed. The original database was not changed; inspect the isolated target $TargetDatabase."
    }

    Write-Output "Backup restored into new isolated database: $TargetDatabase"
}
finally {
    docker compose exec -T db rm -f $containerBackup | Out-Null
    Pop-Location
}
