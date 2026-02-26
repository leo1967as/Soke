
import os
import sys
from dotenv import load_dotenv

# Path to the mcp-discord directory
MCP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mcp-discord")
sys.path.append(os.path.join(MCP_DIR, "src"))

def verify():
    print("--- MCP Discord Verification ---")
    
    # 1. Load .env
    env_path = os.path.join(MCP_DIR, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"[PASS] .env file found at {env_path}")
    else:
        print(f"[FAIL] .env file not found at {env_path}")
        return False

    # 2. Check DISCORD_TOKEN
    token = os.getenv("DISCORD_TOKEN")
    if token:
        print(f"[PASS] DISCORD_TOKEN is set (starts with {token[:5]}...)")
    else:
        print("[FAIL] DISCORD_TOKEN is not set")
        return False

    # 3. Try import
    try:
        import discord
        import mcp
        print("[PASS] Dependencies (discord.py, mcp) imported successfully")
    except ImportError as e:
        print(f"[FAIL] Missing dependencies: {e}")
        return False

    try:
        from discord_mcp.server import app
        print("[PASS] discord_mcp.server.app imported successfully")
    except Exception as e:
        print(f"[FAIL] Error importing discord_mcp: {e}")
        return False

    print("--- Verification Successful ---")
    return True

if __name__ == "__main__":
    if verify():
        sys.exit(0)
    else:
        sys.exit(1)
