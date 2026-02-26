import requests
import json
import os

TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
GUILD_ID = "1475450344334037063"

def load_token(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if "=" in content:
            return content.split("=")[1].strip()
        return content

token = load_token(TOKEN_FILE)
headers = {
    "Authorization": f"Bot {token}",
    "Content-Type": "application/json"
}

def check_bot_identity():
    # Get current user
    res = requests.get("https://discord.com/api/v10/users/@me", headers=headers)
    bot_info = res.json()
    print(f"Bot Name: {bot_info['username']}, ID: {bot_info['id']}")
    
    # Get member info in guild
    res = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/members/{bot_info['id']}", headers=headers)
    member_info = res.json()
    print(f"Bot Roles in Guild: {member_info.get('roles', [])}")

if __name__ == "__main__":
    check_bot_identity()
