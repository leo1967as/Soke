@echo off
echo Starting Discord MCP Server...
cd /d "%~dp0mcp-discord"
uv run mcp-discord
pause
