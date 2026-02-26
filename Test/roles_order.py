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

def list_roles_order():
    url = f"https://discord.com/api/v10/guilds/{GUILD_ID}/roles"
    res = requests.get(url, headers=headers)
    roles = res.json()
    # Sort by position
    roles.sort(key=lambda x: x['position'], reverse=True)
    for r in roles:
        print(f"Pos {r['position']}: {r['name']} (ID: {r['id']})")

if __name__ == "__main__":
    list_roles_order()
