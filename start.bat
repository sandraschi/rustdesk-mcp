@echo off
REM ============================================================================
REM rustdesk-start.bat — Launch everything
REM Starts: hbbs/hbbr (self-hosted relay), fork API server, MCP backend, webapp
REM ============================================================================
cd /d "%~dp0..\.."

set HBB_ROOT=D:\Dev\repos\rustdesk-server
set FORK_ROOT=D:\Dev\repos\rustdesk
set MCP_ROOT=D:\Dev\repos\rustdesk-mcp
set WEB_ROOT=%MCP_ROOT%\web_sota

echo ===== rustdesk++ Launch =====

:: Step 1: Kill stale
taskkill /F /IM hbbs.exe 2>nul
taskkill /F /IM hbbr.exe 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq rustdesk*" 2>nul
timeout /t 2 /nobreak >nul

:: Step 2: Start self-hosted relay servers
echo [1/4] Starting hbbs (ID/rendezvous server) on :21116...
start "rustdesk-hbbs" /B /MIN "%HBB_ROOT%\target\release\hbbs.exe"
timeout /t 2 /nobreak >nul

echo [2/4] Starting hbbr (relay server) on :21117...
start "rustdesk-hbbr" /B /MIN "%HBB_ROOT%\target\release\hbbr.exe"
timeout /t 2 /nobreak >nul

:: Step 3: Start fork API server
echo [3/4] Starting rustdesk++ API server on :10806...
set RUSTDESK_HOME=%APPDATA%\RustDesk
start "rustdesk-fork-api" /B /MIN "%FORK_ROOT%\target\debug\rustdesk.exe" --api-server 10806
timeout /t 3 /nobreak >nul

:: Step 4: Start MCP backend
echo [4/4] Starting MCP backend on :10805...
set RUSTDESK_PATH=C:\Program Files\RustDesk\rustdesk.exe
set MCP_PORT=10805
set MCP_TRANSPORT=http
start "rustdesk-mcp" /B /MIN "uv" run python -m rustdesk_mcp.server
timeout /t 5 /nobreak >nul

:: Step 5: Open webapp
echo Opening webapp at http://127.0.0.1:10805
start http://127.0.0.1:10805

echo ===== All services started =====
echo   hbbs  :21116  (ID/rendezvous)
echo   hbbr  :21117  (relay)
echo   fork  :10806  (rustdesk++ API)
echo   mcp   :10805  (Python MCP backend)
echo   web   :10804  (Vite dev server)
