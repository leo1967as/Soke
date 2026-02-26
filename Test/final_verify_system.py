import requests

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
headers = {"Authorization": f"Bot {token}"}

def verify_setup():
    # 1. Check roles
    res = requests.get(f"{BASE_URL}/guilds/{GUILD_ID}/roles", headers=headers)
    roles = res.json()
    member_role = next((r for r in roles if r['name'] == "Member"), None)
    if member_role:
        print(f"[PASS] Member role found: {member_role['id']}")
    else:
        print("[FAIL] Member role not found")

    # 2. Check channels and perms
    res = requests.get(f"{BASE_URL}/guilds/{GUILD_ID}/channels", headers=headers)
    channels = res.json()
    
    verify_cat = next((c for c in channels if "𝐕𝐞𝐫𝐢𝐟𝐲" in c['name'] and c['type'] == 4), None)
    if verify_cat:
        print(f"[PASS] Verify category found: {verify_cat['id']}")
        print(f"  Overwrites: {verify_cat.get('permission_overwrites')}")
    else:
        print("[FAIL] Verify category not found")

    main_cat = next((c for c in channels if "𝐌𝐚𝐢𝐧" in c['name'] and c['type'] == 4), None)
    if main_cat:
        print(f"[PASS] Main category found: {main_cat['id']}")
        print(f"  Overwrites: {main_cat.get('permission_overwrites')}")

if __name__ == "__main__":
    verify_setup()
