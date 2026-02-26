@echo off
REM ============================================
REM Sokeber AI Support Bot - Quick Launcher
REM ============================================

echo Starting AI Support Bot...
echo.

REM Change to project root directory
cd /d "%~dp0"

REM Run the bot
python -m core.ai_support_bot

REM Pause on error so you can see what went wrong
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Bot exited with error code %ERRORLEVEL%
    echo.
    pause
)
