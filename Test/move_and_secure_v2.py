import requests
import json
import os

TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
GUILD_ID = "1475450344334037063"
WORK_CAT_ID = "1475450952667500636"
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

def get_channels():
    url = f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels"
    res = requests.get(url, headers=headers)
    return res.json() if res.status_code == 200 else []

def patch_channel(channel_id, payload):
    url = f"https://discord.com/api/v10/channels/{channel_id}"
    res = requests.patch(url, headers=headers, json=payload)
    if res.status_code == 200:
        print(f"[PASS] Updated channel {channel_id}")
        return True
    else:
        print(f"[FAIL] Error updating channel {channel_id}: {res.status_code} {res.text}")
        return False

def main():
    print("--- Starting Move and Secure Process (Simplified) ---")
    
    # 1. Secure the System Category (only deny @everyone)
    print(f"Securing System Category ({SYSTEM_CAT_ID})...")
    # We only set the overwrite for @everyone. 
    # Admins will still see it because they have ADMINISTRATOR permission.
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
    patch_channel(SYSTEM_CAT_ID, payload)
    
    # 2. Find channels in Work Category
    channels = get_channels()
    work_channels = [c for c in channels if c.get('parent_id') == WORK_CAT_ID]
    
    print(f"Found {len(work_channels)} channels in 'Work' category.")
    
    # 3. Move them to System Category
    for chan in work_channels:
        chan_id = chan['id']
        chan_name = chan['name']
        print(f"Moving '{chan_name}' ({chan_id}) to System...")
        
        move_payload = {
            "parent_id": SYSTEM_CAT_ID,
            "permission_overwrites": [
                {
                    "id": EVERYONE_ROLE_ID,
                    "type": 0,
                    "allow": "0",
                    "deny": str(VIEW_CHANNEL)
                }
            ]
        }
        patch_channel(chan_id, move_payload)

    print("--- Process Complete ---")

if __name__ == "__main__":
    main()
