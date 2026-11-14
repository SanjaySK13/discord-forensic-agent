@echo off
title Stop Discord Forensic Agent
color 0C
chcp 65001 >nul

echo ========================================================================
echo                 STOPPING DISCORD FORENSIC AGENT
echo ========================================================================
echo.
echo [*] Terminating server and bot processes on port 5000...

set "FOUND=0"
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING 2^>nul') do (
    taskkill /f /pid %%a >nul 2>&1
    set "FOUND=1"
    echo   [-] Terminated process PID: %%a
)

echo.
if "%FOUND%"=="1" (
    echo [SUCCESS] Discord Forensic Agent server and Discord bot stopped.
    echo Port 5000 has been freed.
) else (
    echo [INFO] No active server was running on port 5000.
)
echo ========================================================================
timeout /t 3 >nul
exit

