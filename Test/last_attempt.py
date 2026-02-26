import requests
import json
import os

TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
GUILD_ID = "1475450344334037063"
WORK_CAT_ID = "1475450952667500636"
SYSTEM_CAT_ID = "1475715213641908356"

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

def move_only():
    # Attempt to move sorcerer_ascent without changing anything else
    chan_id = "1475451972311187528"
    url = f"https://discord.com/api/v10/channels/{chan_id}"
    payload = {"parent_id": SYSTEM_CAT_ID}
    res = requests.patch(url, headers=headers, json=payload)
    print(f"Move Result: {res.status_code} {res.text}")

if __name__ == "__main__":
    move_only()
