@echo off
title JoyAI Launcher
color 0A

echo.
echo  ================================================
echo   JoyAI - Starting Services
echo  ================================================
echo.

:: Stop any existing gateway/backend to avoid Telegram polling conflicts
echo  [0/2] Stopping any running instances...
hermes gateway stop >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Hermes Gateway" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq JoyAI Backend" >nul 2>&1

:: Give Telegram 5s to release the polling session
timeout /t 5 /nobreak >nul

:: Start Hermes Gateway in a new window
echo  [1/2] Starting Hermes Gateway...
start "Hermes Gateway" cmd /k "title Hermes Gateway && color 0B && hermes gateway run"

:: Give gateway time to initialize before backend connects to it
timeout /t 4 /nobreak >nul

:: Start Python backend in a new window
echo  [2/2] Starting JoyAI Python Backend...
start "JoyAI Backend" cmd /k "title JoyAI Backend && color 0E && cd /d C:\Users\HadiMoti\JoyAI-WebUI\backend && python hermes_api.py"

echo.
echo  ================================================
echo   Both services launched in separate windows:
echo.
echo   Hermes Gateway  ^>  http://127.0.0.1:9119
echo   Hermes API      ^>  http://127.0.0.1:8642
echo   JoyAI Backend   ^>  http://127.0.0.1:8000
echo  ================================================
echo.
echo  Close this window or press any key to exit.
pause >nul
