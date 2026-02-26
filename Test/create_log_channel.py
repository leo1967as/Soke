import requests
import json

TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
GUILD_ID = "1475450344334037063"
SYSTEM_CAT_ID = "1475715213641908356"
BASE_URL = "https://discord.com/api/v10"

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

def create_channel(name, parent_id):
    url = f"{BASE_URL}/guilds/{GUILD_ID}/channels"
    payload = {"name": name, "type": 0, "parent_id": parent_id}
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code == 201:
        chan = res.json()
        print(f"[PASS] Created Channel: {chan['name']} (ID: {chan['id']})")
        return chan['id']
    else:
        print(f"[FAIL] Creating Channel {name}: {res.status_code} {res.text}")
        return None

if __name__ == "__main__":
    print("--- Creating Audit Log Channel ---")
    create_channel("🏮𝐁𝐨𝐭-𝐋𝐨𝐠𝐬『🛡️』", SYSTEM_CAT_ID)
