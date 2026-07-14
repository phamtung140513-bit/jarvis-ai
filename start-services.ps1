# Start Jarvis bot + VietQR pay + web as independent Windows processes
$ErrorActionPreference = "SilentlyContinue"
$BotDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PayDir = "C:\Users\Admin\vietqr-pay"
$Py = Join-Path $BotDir ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }

function Start-Independent {
    param(
        [Parameter(Mandatory)][string]$Exe,
        [Parameter(Mandatory)][string]$Args,
        [Parameter(Mandatory)][string]$WorkDir,
        [string]$OutLog = "",
        [string]$ErrLog = ""
    )
    if ($OutLog) {
        $dir = Split-Path $OutLog -Parent
        if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    }
    # UseShellExecute=true breaks away from parent Job Object (survives tool exit)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Exe
    $psi.Arguments = $Args
    $psi.WorkingDirectory = $WorkDir
    $psi.UseShellExecute = $true
    $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
    $p = [System.Diagnostics.Process]::Start($psi)
    return $p
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

function Start-Bot {
    if (Test-BotAlive) {
        Write-Host "Bot already running"
        return
    }
    # Wrapper .cmd so logs still captured without tying to PS job
    $wrapper = Join-Path $BotDir "logs\_run_bot.cmd"
    $out = Join-Path $BotDir "logs\bot-stdout.log"
    $err = Join-Path $BotDir "logs\bot-stderr.log"
    @"
@echo off
cd /d "$BotDir"
"$Py" launcher.py >> "$out" 2>> "$err"
"@ | Set-Content -Path $wrapper -Encoding ASCII
    $p = Start-Independent -Exe "cmd.exe" -Args "/c `"$wrapper`"" -WorkDir $BotDir
    Write-Host "Started bot PID=$($p.Id) (independent)"
}

function Start-Pay {
    if (Test-PayAlive) {
        Write-Host "Pay already running"
        return
    }
    if (-not (Test-Path $PayDir)) {
        Write-Host "Pay dir missing: $PayDir"
        return
    }
    $wrapper = Join-Path $BotDir "logs\_run_pay.cmd"
    $out = Join-Path $PayDir "logs-stdout.log"
    $err = Join-Path $PayDir "logs-stderr.log"
    @"
@echo off
cd /d "$PayDir"
node server.js >> "$out" 2>> "$err"
"@ | Set-Content -Path $wrapper -Encoding ASCII
    $p = Start-Independent -Exe "cmd.exe" -Args "/c `"$wrapper`"" -WorkDir $PayDir
    Write-Host "Started pay PID=$($p.Id) (independent)"
}

function Start-Web {
    if (Test-WebAlive) {
        Write-Host "Web already running"
        return
    }
    $wrapper = Join-Path $BotDir "logs\_run_web.cmd"
    $out = Join-Path $BotDir "logs\web-stdout.log"
    $err = Join-Path $BotDir "logs\web-stderr.log"
    @"
@echo off
cd /d "$BotDir"
"$Py" -m webapp.server >> "$out" 2>> "$err"
"@ | Set-Content -Path $wrapper -Encoding ASCII
    $p = Start-Independent -Exe "cmd.exe" -Args "/c `"$wrapper`"" -WorkDir $BotDir
    Write-Host "Started web PID=$($p.Id) → http://127.0.0.1:7860"
}

Start-Pay
Start-Bot
Start-Web
Start-Sleep -Seconds 7
try {
    $h = Invoke-RestMethod "http://127.0.0.1:8787/internal/health" -TimeoutSec 4
    Write-Host "Bot health: $($h | ConvertTo-Json -Compress)"
} catch { Write-Host "Bot health: FAIL - $($_.Exception.Message)" }
try {
    $h = Invoke-RestMethod "http://127.0.0.1:3000/api/health" -TimeoutSec 4
    Write-Host "Pay health: $($h | ConvertTo-Json -Compress)"
} catch { Write-Host "Pay health: FAIL - $($_.Exception.Message)" }
try {
    $h = Invoke-RestMethod "http://127.0.0.1:7860/api/health" -TimeoutSec 4
    Write-Host "Web health: $($h | ConvertTo-Json -Compress)"
} catch { Write-Host "Web health: FAIL - $($_.Exception.Message)" }

if (Test-BotAlive) { Write-Host "Bot process: ALIVE" } else { Write-Host "Bot process: MISSING" }
