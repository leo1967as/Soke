@echo off
echo Verifying Discord MCP Server Installation...
cd /d "%~dp0mcp-discord"
uv run python ../Test/verify_discord.py
pause
