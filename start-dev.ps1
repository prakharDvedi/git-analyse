param(
    [string]$BackendHost = "127.0.0.1",
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000,
    [switch]$CleanPorts
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = $root
$frontendDir = Join-Path $root "frontend"
$activateScript = Join-Path $root ".venv\Scripts\Activate.ps1"

if (-not (Test-Path $activateScript)) {
    Write-Error "Missing venv activation script at $activateScript"
}

if (-not (Test-Path $frontendDir)) {
    Write-Error "Missing frontend directory at $frontendDir"
}

function Stop-ProcessOnPort {
    param([int]$Port)

    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($null -eq $connections) { return }

    $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($pid in $pids) {
        try {
            Stop-Process -Id $pid -Force -ErrorAction Stop
            Write-Host "Stopped process $pid on port $Port"
        } catch {
            Write-Warning "Could not stop process $pid on port $Port"
        }
    }
}

if ($CleanPorts) {
    Stop-ProcessOnPort -Port $BackendPort
    Stop-ProcessOnPort -Port $FrontendPort
}

$backendCommand = @"
Set-Location '$backendDir'
& '$activateScript'
uvicorn app.main:app --reload --host $BackendHost --port $BackendPort
"@

$frontendCommand = @"
Set-Location '$frontendDir'
npm.cmd run dev -- -p $FrontendPort
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand

Write-Host "Started backend:  http://$BackendHost`:$BackendPort"
Write-Host "Started frontend: http://localhost:$FrontendPort"
Write-Host "Two new PowerShell windows were opened for logs."
