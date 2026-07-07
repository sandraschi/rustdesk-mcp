#!/usr/bin/env pwsh
# rustdesk-start.ps1 — Launch everything (hbbs/hbbr, fork API, MCP backend, webapp)

param(
    [switch]$NoRelay,
    [switch]$NoFork,
    [switch]$NoWebapp,
    [switch]$Kill
)

$HBB_ROOT = "D:\Dev\repos\rustdesk-server"
$FORK_ROOT = "D:\Dev\repos\rustdesk"
$MCP_ROOT = "D:\Dev\repos\rustdesk-mcp"
$WEB_ROOT = "$MCP_ROOT\web_sota"

if ($Kill) {
    Write-Host "Killing all rustdesk processes..." -ForegroundColor Yellow
    Get-Process -Name hbbs, hbbr, rustdesk-mcp* -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-NetTCPConnection -LocalPort 10805,10806,21116,21117 -ErrorAction SilentlyContinue |
        Where-Object State -eq "Listen" | Select-Object -ExpandProperty OwningProcess |
        ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
    Write-Host "All stopped." -ForegroundColor Green
    return
}

Write-Host "===== rustdesk++ Launch =====" -ForegroundColor Cyan

Get-Process -Name hbbs, hbbr -ErrorAction SilentlyContinue | Stop-Process -Force

if (-not $NoRelay) {
    Write-Host "[1/4] Starting hbbs on :21116..." -ForegroundColor Green
    Start-Process -NoNewWindow -FilePath "$HBB_ROOT\target\release\hbbs.exe"; Start-Sleep 2
    Write-Host "[2/4] Starting hbbr on :21117..." -ForegroundColor Green
    Start-Process -NoNewWindow -FilePath "$HBB_ROOT\target\release\hbbr.exe"; Start-Sleep 2
}

if (-not $NoFork) {
    Write-Host "[3/4] Starting rustdesk++ API server on :10806..." -ForegroundColor Green
    Start-Process -NoNewWindow -FilePath "$FORK_ROOT\target\debug\rustdesk.exe" -ArgumentList "--api-server 10806"; Start-Sleep 3
}

Write-Host "[4/4] Starting MCP backend on :10805..." -ForegroundColor Green
$env:RUSTDESK_PATH = "C:\Program Files\RustDesk\rustdesk.exe"
$env:MCP_PORT = "10805"
$env:MCP_TRANSPORT = "http"
Start-Process -NoNewWindow -FilePath "uv" -ArgumentList "run", "python", "-m", "rustdesk_mcp.server" -WorkingDirectory $MCP_ROOT

Start-Sleep 5
Write-Host "===== Services =====" -ForegroundColor Cyan
Write-Host "  hbbs  :21116  (ID/rendezvous)" -ForegroundColor White
Write-Host "  hbbr  :21117  (relay)" -ForegroundColor White
Write-Host "  fork  :10806  (rustdesk++ API)" -ForegroundColor White
Write-Host "  mcp   :10805  (Python MCP backend)" -ForegroundColor White
Write-Host "`nWebapp: http://127.0.0.1:10805" -ForegroundColor Cyan
if (-not $NoWebapp) { Start-Process "http://127.0.0.1:10805" }
