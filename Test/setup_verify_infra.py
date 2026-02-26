import requests
import json
import time

TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
GUILD_ID = "1475450344334037063"
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

def create_role(name, color=0x3498db):
    url = f"{BASE_URL}/guilds/{GUILD_ID}/roles"
    payload = {"name": name, "color": color, "permissions": "0"}
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code == 201:
        role = res.json()
        print(f"[PASS] Created Role: {role['name']} (ID: {role['id']})")
        return role['id']
    else:
        print(f"[FAIL] Creating Role {name}: {res.status_code} {res.text}")
        return None

def create_category(name):
    url = f"{BASE_URL}/guilds/{GUILD_ID}/channels"
    payload = {"name": name, "type": 4}
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code == 201:
        cat = res.json()
        print(f"[PASS] Created Category: {cat['name']} (ID: {cat['id']})")
        return cat['id']
    else:
        print(f"[FAIL] Creating Category {name}: {res.status_code} {res.text}")
        return None

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

def main():
    print("--- Setting up Verification Infrastructure ---")
    
    # 1. Create Member Role
    member_role_id = create_role("Member", color=0x2ecc71) # Greenish color for members
    
    # 2. Create Verify Category (Place at Top)
    verify_cat_id = create_category("🛡️ 『 ✅ 』 〚 𝐕𝐞𝐫𝐢𝐟𝐲 〛")
    
    # 3. Create Verify channel inside category
    if verify_cat_id:
        verify_chan_id = create_channel("🏮𝐕𝐞𝐫𝐢𝐟𝐲-𝐡𝐞𝐫𝐞『✅』", verify_cat_id)
        
    print("\nNext step: Configure permissions and move Category to top.")

if __name__ == "__main__":
    main()
