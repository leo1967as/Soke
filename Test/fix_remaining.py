import requests, time

TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
MAIN_CAT   = "1475451511340273697"
GAMING_CAT = "1475451161275400264"
WELCOME_CH = "1475451610648805477"   # orphaned
ROBLOX3_CH = "1475739990599274609"   # in System incorrectly

def load_token(path):
    with open(path, "r", encoding="utf-8") as f:
        c = f.read().strip()
        return c.split("=")[1].strip() if "=" in c else c

token   = load_token(TOKEN_FILE)
HEADERS = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}
BASE    = "https://discord.com/api/v10"

def patch(endpoint, payload):
    r = requests.patch(f"{BASE}{endpoint}", headers=HEADERS, json=payload)
    time.sleep(0.3)
    return r

# Fix 1: Move WELCOME to Main
r = patch(f"/channels/{WELCOME_CH}", {"parent_id": MAIN_CAT})
print(f"WELCOME → Main: {'[PASS]' if r.status_code==200 else f'[FAIL] {r.text[:80]}'}")

# Fix 2: Move Roblox 3 from System to Gaming
r = patch(f"/channels/{ROBLOX3_CH}", {"parent_id": GAMING_CAT})
print(f"Roblox 3 → Gaming: {'[PASS]' if r.status_code==200 else f'[FAIL] {r.text[:80]}'}")
