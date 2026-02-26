@echo off
setlocal enabledelayedexpansion
REM ============================================
REM Sokeber AI Support Bot - robust Launcher
REM ============================================

set PROJECT_DIR=core\ai_support_bot
set BOT_ROOT=%~dp0..\..
cd /d "%BOT_ROOT%"

echo ========================================
echo   Sokeber AI Support Bot
echo   OpenRouter + Notion + Discord
echo ========================================
echo.

REM [1/3] Detection: uv
echo [1/3] Detecting environment tools...
set UV_CMD=uv
where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [!] 'uv' command not found in PATH.
    echo [!] Checking for python -m uv...
    python -m uv --version >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set UV_CMD=python -m uv
        echo [✓] Found uv via python -m uv
    ) else (
        echo [ERROR] 'uv' is not installed. 
        echo please run: pip install uv
        pause
        exit /b 1
    )
) else (
    echo [✓] Found global uv command
)

REM [2/3] Setup environment
echo [2/3] Syncing dependencies...
%UV_CMD% venv %PROJECT_DIR%\.venv >nul 2>nul
%UV_CMD% pip install -e %PROJECT_DIR% >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to sync dependencies in %PROJECT_DIR%.
    pause
    exit /b 1
)

REM [3/3] Launch
echo [3/3] Starting bot...
echo.
echo Using LLM: openai/gpt-4o-mini
echo ----------------------------------------

REM Inject PYTHONPATH to ensure core package is found
set PYTHONPATH=%CD%;%PYTHONPATH%

REM Run the bot pointing to the project config
%UV_CMD% run --project %PROJECT_DIR% python -m core.ai_support_bot

REM Handle errors
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo [ERROR] Bot crashed with code %ERRORLEVEL%
    echo ========================================
    echo.
    pause
)
