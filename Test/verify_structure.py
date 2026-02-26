import requests, sys

TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
GUILD_ID   = "1475450344334037063"

def load_token(path):
    with open(path, "r", encoding="utf-8") as f:
        c = f.read().strip()
        return c.split("=")[1].strip() if "=" in c else c

token   = load_token(TOKEN_FILE)
HEADERS = {"Authorization": f"Bot {token}"}

r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS)
channels = r.json()

# Group by parent
cats   = {c["id"]: c["name"] for c in channels if c["type"] == 4}
others = [c for c in channels if c["type"] != 4]

print("\n=== Current Server Structure ===")
print(f"\nCategories ({len(cats)}):")
for cid, cname in cats.items():
    print(f"  [{cid}] {cname}")
    children = [ch for ch in others if ch.get("parent_id") == cid]
    for ch in children:
        t = {0:"text",2:"voice",5:"news",15:"forum"}.get(ch["type"],"?")
        print(f"    ├─ {ch['name']} ({t})")

no_parent = [c for c in others if not c.get("parent_id")]
if no_parent:
    print(f"\nNo-parent channels ({len(no_parent)}):")
    for c in no_parent:
        print(f"  ⚠ {c['name']} (ID: {c['id']})")
else:
    print("\n✅ No orphan channels!")
