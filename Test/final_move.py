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

def move_all_work_to_system():
    # Fetch channels
    res = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=headers)
    all_channels = res.json()
    
    work_channels = [c for c in all_channels if c.get('parent_id') == WORK_CAT_ID]
    print(f"Found {len(work_channels)} channels to move.")
    
    for chan in work_channels:
        chan_id = chan['id']
        chan_name = chan['name']
        print(f"Moving '{chan_name}'...")
        
        url = f"https://discord.com/api/v10/channels/{chan_id}"
        payload = {"parent_id": SYSTEM_CAT_ID}
        move_res = requests.patch(url, headers=headers, json=payload)
        
        if move_res.status_code == 200:
            print(f"[PASS] Successfully moved {chan_name}")
        else:
            print(f"[FAIL] Error moving {chan_name}: {move_res.status_code} {move_res.text}")

if __name__ == "__main__":
    move_all_work_to_system()
