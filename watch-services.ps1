# Keep bot + vietqr-pay + web alive. Fully detached loop.
$ErrorActionPreference = "SilentlyContinue"
$BotDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$StartScript = Join-Path $BotDir "start-services.ps1"
$Log = Join-Path $BotDir "logs\watchdog.log"
New-Item -ItemType Directory -Force -Path (Join-Path $BotDir "logs") | Out-Null

function Write-Log($msg) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg"
    Add-Content -Path $Log -Value $line -Encoding utf8
}

function Test-BotAlive {
    $p = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
        Where-Object { $_.CommandLine -match 'launcher\.py' }
    return [bool]$p
}

function Test-PayAlive {
    $p = Get-CimInstance Win32_Process -Filter "Name = 'node.exe'" |
        Where-Object { $_.CommandLine -match 'server\.js' }
    return [bool]$p
}

function Test-WebAlive {
    $p = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
        Where-Object { $_.CommandLine -match 'webapp\.server|uvicorn.*webapp' }
    return [bool]$p
}

Write-Log "watchdog started pid=$PID"
while ($true) {
    $need = $false
    if (-not (Test-BotAlive)) { Write-Log "bot DOWN"; $need = $true }
    if (-not (Test-PayAlive)) { Write-Log "pay DOWN"; $need = $true }
    if (-not (Test-WebAlive)) { Write-Log "web DOWN"; $need = $true }
    if ($need) {
        try {
            & powershell -NoProfile -ExecutionPolicy Bypass -File $StartScript | Out-File -Append $Log -Encoding utf8
            Write-Log "restarted via start-services.ps1"
        } catch {
            Write-Log "restart error: $_"
        }
    }
    Start-Sleep -Seconds 15
}
