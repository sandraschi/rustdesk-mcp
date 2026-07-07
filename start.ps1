#!/usr/bin/env pwsh
# rustdesk-start.ps1 — Launch everything (hbbs/hbbr, fork API, MCP backend, webapp)
# Ports: 10804 (Vite), 10805 (MCP), 10806 (fork), 21116 (hbbs), 21117 (hbbr)

param([switch]$Kill)

$HBB="D:\Dev\repos\rustdesk-server\target\release"
$FORK="D:\Dev\repos\rustdesk\target\debug"
$MCP=$PSScriptRoot
$TARGET_PORTS=@(10804,10805,10806,21115,21116,21117,21118,21119)

function Kill-Zombies {
    Get-NetTCPConnection -ErrorAction SilentlyContinue | Where-Object {
        $_.LocalPort -in $TARGET_PORTS -and $_.State -eq "Listen"
    } | ForEach-Object { taskkill /F /PID $_.OwningProcess 2>$null }
    Get-Process -Name hbbs,hbbr,rustdesk-mcp* -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep 2
}

if ($Kill) { Kill-Zombies; Write-Host "All stopped." -ForegroundColor Green; return }

Kill-Zombies

Write-Host "===== rustdesk++ Launch =====" -ForegroundColor Cyan

Write-Host "[1/6] Starting hbbs on :21116..." -ForegroundColor Green
Start-Process -NoNewWindow -FilePath "$HBB\hbbs.exe"; Start-Sleep 3

Write-Host "[2/6] Starting hbbr on :21117..." -ForegroundColor Green
Start-Process -NoNewWindow -FilePath "$HBB\hbbr.exe"; Start-Sleep 2

Write-Host "[3/6] Starting fork API on :10806..." -ForegroundColor Green
Start-Process -NoNewWindow -FilePath "$FORK\rustdesk.exe" -ArgumentList "--api-server 10806"; Start-Sleep 3

Write-Host "[4/6] Starting MCP backend on :10805..." -ForegroundColor Green
$env:RUSTDESK_PATH="C:\Program Files\RustDesk\rustdesk.exe"
$env:MCP_PORT="10805"
$env:MCP_TRANSPORT="http"
Start-Process -NoNewWindow -FilePath "uv" -ArgumentList "run","python","-m","rustdesk_mcp.server" -WorkingDirectory $MCP
Start-Sleep 6

Write-Host "[5/6] Starting webapp on :10804..." -ForegroundColor Green
Start-Process -NoNewWindow -FilePath "bun" -ArgumentList "run","dev" -WorkingDirectory "$MCP\web_sota"
Start-Sleep 3

Write-Host "[6/6] Health check..." -ForegroundColor Green
try { $r=Invoke-WebRequest "http://127.0.0.1:10805/api/health" -TimeoutSec 5 -UseBasicParsing; Write-Host "  MCP: $($r.StatusCode)" -ForegroundColor Green }
catch { Write-Host "  MCP: DOWN" -ForegroundColor Red }
try { $r=Invoke-WebRequest "http://127.0.0.1:10806/api/v1/health" -TimeoutSec 3 -UseBasicParsing; Write-Host "  Fork: $($r.StatusCode)" -ForegroundColor Green }
catch { Write-Host "  Fork: DOWN" -ForegroundColor Red }

Start-Process "http://127.0.0.1:10805"
Write-Host "All services started" -ForegroundColor Cyan
