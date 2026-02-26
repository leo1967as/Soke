import requests
import json
import os

TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
GUILD_ID = "1475450344334037063"
SYSTEM_CAT_ID = "1475715213641908356"
EVERYONE_ROLE_ID = GUILD_ID

# Permission bit for VIEW_CHANNEL
VIEW_CHANNEL = 1 << 10

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

def secure_moved_channels():
    # Fetch channels
    res = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=headers)
    all_channels = res.json()
    
    # We want channels in System category
    system_channels = [c for c in all_channels if c.get('parent_id') == SYSTEM_CAT_ID]
    print(f"Found {len(system_channels)} channels in 'System' category to secure.")
    
    for chan in system_channels:
        chan_id = chan['id']
        chan_name = chan['name']
        print(f"Securing '{chan_name}'...")
        
        url = f"https://discord.com/api/v10/channels/{chan_id}"
        # Set overwrite to only deny @everyone. 
        # This will remove other user-specific overwrites that might have been copied.
        payload = {
            "permission_overwrites": [
                {
                    "id": EVERYONE_ROLE_ID,
                    "type": 0,
                    "allow": "0",
                    "deny": str(VIEW_CHANNEL)
                }
            ]
        }
        res_patch = requests.patch(url, headers=headers, json=payload)
        
        if res_patch.status_code == 200:
            print(f"[PASS] Successfully secured {chan_name}")
        else:
            print(f"[FAIL] Error securing {chan_name}: {res_patch.status_code} {res_patch.text}")

if __name__ == "__main__":
    secure_moved_channels()
