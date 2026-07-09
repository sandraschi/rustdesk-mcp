#!/usr/bin/env pwsh
# rustdesk-start.ps1 — Launch everything (hbbs/hbbr, fork API, MCP backend, webapp)
# Ports: 10804 (Vite), 10805 (MCP), 10806 (fork), 21116 (hbbs), 21117 (hbbr)

param([switch]$Kill)

$FORK="D:\Dev\repos\rustdesk\target\debug"
$MCP="D:\Dev\repos\rustdesk-mcp"
$TARGET_PORTS=@(10804,10805,10806,21115,21116,21117,21118,21119)

if ($Kill) {
    Write-Host "Stopping services..." -ForegroundColor Yellow
    Get-NetTCPConnection -ErrorAction SilentlyContinue | Where-Object {
        $_.LocalPort -in $TARGET_PORTS -and $_.State -eq "Listen"
    } | ForEach-Object { taskkill /F /PID $_.OwningProcess 2>$null }
    Get-Process -Name hbbs,hbbr,rustdesk-mcp* -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host "All stopped." -ForegroundColor Green
    return
}

# Kill stale MCP and fork API processes on 10805, 10806
Write-Host "Killing stale processes on target ports..." -ForegroundColor Yellow
Get-NetTCPConnection -ErrorAction SilentlyContinue | Where-Object {
    $_.LocalPort -in @(10805,10806) -and $_.State -eq "Listen"
} | ForEach-Object { taskkill /F /PID $_.OwningProcess 2>$null }
Start-Sleep 2

# Ensure hbbs/hbbr are running via scheduled tasks
$sched = Get-ScheduledTask -TaskName "RustDesk hbbs" -ErrorAction SilentlyContinue
if (-not $sched) {
    Write-Host "Installing relay server tasks (as admin)..." -ForegroundColor Yellow
    Start-Process "D:\Dev\repos\rustdesk\install-server.bat" -Verb RunAs -Wait
} else {
    Write-Host "Starting relay server tasks..." -ForegroundColor Green
    try { Start-ScheduledTask "RustDesk hbbs" } catch {}
    try { Start-ScheduledTask "RustDesk hbbr" } catch {}
}
Start-Sleep 4

# Start fork API server via WMI (survives shell exit)
Write-Host "Starting fork API on :10806..." -ForegroundColor Green
Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine="$FORK\rustdesk.exe --api-server 10806"
} 2>$null
Start-Sleep 3

# Start MCP backend
Write-Host "Starting MCP backend on :10805..." -ForegroundColor Green
$env:RUSTDESK_PATH = "C:\Program Files\RustDesk\rustdesk.exe"
$env:MCP_PORT = "10805"
$env:MCP_TRANSPORT = "http"
Start-Process -NoNewWindow -FilePath "uv" -ArgumentList "run","python","-m","rustdesk_mcp.server" -WorkingDirectory $MCP
Start-Sleep 5

# Health checks
try { $r = Invoke-WebRequest "http://127.0.0.1:10805/api/health" -TimeoutSec 5 -UseBasicParsing; Write-Host "  MCP: OK" -ForegroundColor Green }
catch { Write-Host "  MCP: DOWN" -ForegroundColor Red }

try { $r = Invoke-WebRequest "http://127.0.0.1:10806/api/v1/health" -TimeoutSec 3 -UseBasicParsing; Write-Host "  Fork: OK" -ForegroundColor Green }
catch { Write-Host "  Fork: DOWN" -ForegroundColor Red }

Write-Host "`nWebapp: http://127.0.0.1:10805" -ForegroundColor Cyan
Start-Process "http://127.0.0.1:10805"
