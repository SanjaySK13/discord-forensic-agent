@echo off
title Discord Forensic Agent Controller
color 0B
chcp 65001 >nul

cd /d "%~dp0"

echo ========================================================================
echo                 DISCORD FORENSIC AGENT & BOT RUNNER
echo ========================================================================
echo.
echo [*] Checking for previous instances on port 5000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING 2^>nul') do (
    echo [*] Stopping previous process (PID: %%a)...
    taskkill /f /pid %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

echo [*] Starting Discord Forensic Server & Discord Gateway Bot...
start /b "" python -u server.py > server_runtime.log 2>&1

timeout /t 2 /nobreak >nul

echo [*] Launching Web Dashboard in browser...
start http://localhost:5000

cls
echo ========================================================================
echo                 DISCORD FORENSIC AGENT & BOT RUNNER
echo ========================================================================
echo.
echo   [+] Web Dashboard:  http://localhost:5000 (Opened in browser)
echo   [+] Discord Bot:    ONLINE in Discord (Gateway Connected)
echo   [+] Server Engine:  Flask + Gemini 3.5 Flash + Math Stylometrics
echo.
echo ------------------------------------------------------------------------
echo   TO SHUT DOWN THE SERVER:
echo     - Press [Q] or any key in this window
echo     - OR click the red "Shut Down" button in the web dashboard header
echo     - OR double-click "Stop Discord Forensic Agent" on your Desktop
echo ========================================================================
echo.

pause

echo.
echo [*] Shutting down Discord Forensic Agent and bot...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING 2^>nul') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo [OK] Server and Discord bot successfully shut down.
timeout /t 2 /nobreak >nul
exit
