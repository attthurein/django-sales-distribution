# Archive Audit Logs (Older than 6 months)
# Run this via Task Scheduler or manually

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Join-Path $ScriptDir ".."
Set-Location $ProjectRoot

# Activate venv if exists
$VenvActivate = Join-Path $ProjectRoot "venv\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    try {
        . $VenvActivate
    } catch {
        Write-Warning "Could not activate venv. Python might not be found if not in PATH."
    }
}

# Create logs directory if not exists
$LogDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

$LogFile = Join-Path $LogDir "archive_log.txt"
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Add-Content -Path $LogFile -Value "Running Audit Log Archiving at $Timestamp"

# Run archiving
try {
    # Using cmd /c to handle redirection reliably in all PS versions or just invoke directly
    # Capturing output to variable to append cleanly
    $Output = python manage.py archive_audit_logs 2>&1
    Add-Content -Path $LogFile -Value $Output
    Add-Content -Path $LogFile -Value "Archiving completed at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
}
catch {
    Add-Content -Path $LogFile -Value "Archiving failed at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Add-Content -Path $LogFile -Value $_.Exception.Message
    exit 1
}

exit 0
