import requests
import json
import time

TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
GUILD_ID = "1475450344334037063"
MEMBER_ROLE_ID = "1476201292082057398"
VERIFY_CAT_ID = "1476201295445758096"
BASE_URL = "https://discord.com/api/v10"

# Permission bits
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

def get_categories():
    res = requests.get(f"{BASE_URL}/guilds/{GUILD_ID}/channels", headers=headers)
    if res.status_code == 200:
        return [c for c in res.json() if c['type'] == 4]
    return []

def update_permission(channel_id, role_id, type, allow, deny):
    url = f"{BASE_URL}/channels/{channel_id}/permissions/{role_id}"
    payload = {
        "allow": str(allow),
        "deny": str(deny),
        "type": type # 0 for role, 1 for member
    }
    res = requests.put(url, headers=headers, json=payload)
    if res.status_code == 204:
        print(f"[PASS] Updated perms for {channel_id} (Role: {role_id})")
    else:
        print(f"[FAIL] Updating perms for {channel_id}: {res.status_code} {res.text}")

def main():
    print("--- Locking Categories and Configuring Member Access ---")
    categories = get_categories()
    
    # Categories to LOCK from @everyone and ALLOW to Member
    # We skip 'System' as it's already secured for Admins
    public_cats = [c for c in categories if c['name'] != "System" and c['id'] != VERIFY_CAT_ID]
    
    for cat in public_cats:
        print(f"Locking Category: {cat['name']}...")
        # 1. Deny @everyone
        update_permission(cat['id'], GUILD_ID, 0, 0, VIEW_CHANNEL)
        # 2. Allow Member
        update_permission(cat['id'], MEMBER_ROLE_ID, 0, VIEW_CHANNEL, 0)

    # 3. Configure Verify Category: Allow @everyone, Deny Member (to hide it after verify)
    print("Configuring Verify Category access...")
    update_permission(VERIFY_CAT_ID, GUILD_ID, 0, VIEW_CHANNEL, 0) # Allow @everyone
    update_permission(VERIFY_CAT_ID, MEMBER_ROLE_ID, 0, 0, VIEW_CHANNEL) # Deny Member

if __name__ == "__main__":
    main()
