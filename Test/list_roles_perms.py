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

def get_roles_bits():
    url = f"https://discord.com/api/v10/guilds/{GUILD_ID}/roles"
    res = requests.get(url, headers=headers)
    for role in res.json():
        print(f"Role: {role['name']}, ID: {role['id']}, Perms: {role['permissions']}")

if __name__ == "__main__":
    get_roles_bits()
