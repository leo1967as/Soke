import requests
import json
import os

TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
GUILD_ID = "1475450344334037063"
SYSTEM_CAT_ID = "1475715213641908356"
EVERYONE_ROLE_ID = GUILD_ID
BOT_ID = "1476183621256609834"

# Permission bits
VIEW_CHANNEL = 1 << 10
MANAGE_CHANNELS = 1 << 4

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

def finalize_security():
    # Fetch channels
    res = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=headers)
    all_channels = res.json()
    
    system_channels = [c for c in all_channels if c.get('parent_id') == SYSTEM_CAT_ID]
    print(f"Adding Bot access to {len(system_channels)} channels.")
    
    for chan in system_channels:
        chan_id = chan['id']
        chan_name = chan['name']
        print(f"Updating '{chan_name}'...")
        
        # Keep @everyone denied, and explicitly allow Bot (and optionally Admin if we could, but we can't touch Admin)
        payload = {
            "permission_overwrites": [
                {
                    "id": EVERYONE_ROLE_ID,
                    "type": 0,
                    "allow": "0",
                    "deny": str(VIEW_CHANNEL)
                },
                {
                    "id": BOT_ID,
                    "type": 1, # member
                    "allow": str(VIEW_CHANNEL | MANAGE_CHANNELS),
                    "deny": "0"
                }
            ]
        }
        requests.patch(f"https://discord.com/api/v10/channels/{chan_id}", headers=headers, json=payload)

if __name__ == "__main__":
    finalize_security()
