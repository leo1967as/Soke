"""
Discord Server Reorganizer — Sokeberlnwza
Plan:
  Main     : WELCOME, Rules, Announcement
  Shop     : Advertise, รีวิวร้าน, Code, Fanpage_FB   (NEW category)
  Social   : Message, หาเพื่อนเล่น, Event (news)
  Gaming   : Event (forum), Roblox 1/2/3, Event Jogo  (rename category)
  System   : (already done, admin-only)

Actions:
  1. Create 'Shop' category
  2. Move channels to correct parent
  3. Delete test channels
  4. Delete empty categories (Work, Lobby)
  5. Rename Gaming category
"""
import requests, time, sys

TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
GUILD_ID   = "1475450344334037063"

# ─── Channel IDs ───────────────────────────────────────────────
MAIN_CAT   = "1475451511340273697"   # 🟠 Main
SOCIAL_CAT = "1475694977425084477"   # 🔵 Social
GAMING_CAT = "1475451161275400264"   # 《 Gaming
SYSTEM_CAT = "1475715213641908356"   # System
WORK_CAT   = "1475450952667500636"   # 🔴 Work (empty)
LOBBY_CAT  = "1475715851796742317"   # 🔴 Lobby

RULES_CH        = "1475713132264423518"   # 🏮Rules
ANNOUNCE_CH     = "1475867499726766192"   # Announcement
ADVERTISE_CH    = "1475451668710686852"   # 🏮Advertise
REVIEW_CH       = "1475875038912712815"   # รีวิวร้าน
CODE_CH         = "1475875858420994058"   # 🏮Code (forum)
FANPAGE_CH      = "1475458148440604713"   # 🏮Fanpage_FB
EVENT_FORUM_CH  = "1475605394213568673"   # 🏮Event (forum)

# Test channels to delete
TEST_CHANNELS   = [
    "1476192312898879521",   # test-bot-access
    "1476192447343366188",   # bot-test-channel
    "1476192989687582760",   # bot-test-work-access
]

def load_token(path):
    with open(path, "r", encoding="utf-8") as f:
        c = f.read().strip()
        return c.split("=")[1].strip() if "=" in c else c

token   = load_token(TOKEN_FILE)
HEADERS = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}
BASE    = "https://discord.com/api/v10"

PASS = "[PASS]"
FAIL = "[FAIL]"

def patch(endpoint, payload):
    res = requests.patch(f"{BASE}{endpoint}", headers=HEADERS, json=payload)
    time.sleep(0.3)   # tiny rate-limit buffer
    return res

def delete(endpoint):
    res = requests.delete(f"{BASE}{endpoint}", headers=HEADERS)
    time.sleep(0.3)
    return res

def post(endpoint, payload):
    res = requests.post(f"{BASE}{endpoint}", headers=HEADERS, json=payload)
    time.sleep(0.3)
    return res

def move(ch_id, cat_id, label):
    r = patch(f"/channels/{ch_id}", {"parent_id": cat_id})
    if r.status_code == 200:
        print(f"{PASS} Moved {label}")
    else:
        print(f"{FAIL} Move {label}: {r.status_code} {r.text[:80]}")

def rename_cat(cat_id, new_name):
    r = patch(f"/channels/{cat_id}", {"name": new_name})
    if r.status_code == 200:
        print(f"{PASS} Renamed category → {new_name}")
    else:
        print(f"{FAIL} Rename category: {r.status_code} {r.text[:80]}")

def delete_ch(ch_id, label):
    r = delete(f"/channels/{ch_id}")
    if r.status_code == 200:
        print(f"{PASS} Deleted {label}")
    else:
        print(f"{FAIL} Delete {label}: {r.status_code} {r.text[:80]}")

# ── Check existing channels before touching anything ────────────
def get_channels():
    r = requests.get(f"{BASE}/guilds/{GUILD_ID}/channels", headers=HEADERS)
    return {c["id"]: c for c in r.json()} if r.status_code == 200 else {}

# ─────────────────────────────────────────────────────────────────
def main():
    channels = get_channels()

    # ── Step 1: Create SHOP category ──────────────────────────────
    print("\n[1/5] Creating Shop category...")
    r = post(f"/guilds/{GUILD_ID}/channels", {
        "name": "🟡  『 💎 』  〚 𝐒𝐡𝐨𝐩 〛",
        "type": 4      # GUILD_CATEGORY
    })
    if r.status_code == 201:
        shop_cat = r.json()["id"]
        print(f"{PASS} Created Shop category (ID: {shop_cat})")
    else:
        print(f"{FAIL} Create Shop: {r.status_code} {r.text[:80]}")
        sys.exit(1)

    # ── Step 2: Move channels to MAIN ─────────────────────────────
    print("\n[2/5] Moving channels to Main...")
    move(RULES_CH,    MAIN_CAT, "Rules → Main")
    move(ANNOUNCE_CH, MAIN_CAT, "Announcement → Main")

    # ── Step 3: Move channels to SHOP ─────────────────────────────
    print("\n[3/5] Moving channels to Shop...")
    move(ADVERTISE_CH, shop_cat, "Advertise → Shop")
    move(REVIEW_CH,    shop_cat, "รีวิวร้าน → Shop")
    move(CODE_CH,      shop_cat, "Code (forum) → Shop")
    move(FANPAGE_CH,   shop_cat, "Fanpage_FB → Shop")

    # ── Step 4: Move Event forum to GAMING ───────────────────────
    print("\n[4/5] Moving Event forum to Gaming...")
    move(EVENT_FORUM_CH, GAMING_CAT, "Event (forum) → Gaming")

    # ── Step 5: Rename Gaming category ────────────────────────────
    print("\n[5/5] Renaming Gaming category...")
    rename_cat(GAMING_CAT, "🟢  『 🎮 』  〚 𝐆𝐚𝐦𝐢𝐧𝐠 〛")

    # ── Step 6: Delete test channels ──────────────────────────────
    print("\n[6/7] Deleting test channels...")
    test_labels = ["test-bot-access", "bot-test-channel", "bot-test-work-access"]
    for ch_id, label in zip(TEST_CHANNELS, test_labels):
        delete_ch(ch_id, label)

    # ── Step 7: Delete empty categories ───────────────────────────
    print("\n[7/7] Deleting empty categories...")
    delete_ch(WORK_CAT,  "Work category (empty)")
    delete_ch(LOBBY_CAT, "Lobby category (empty after moves)")

    print("\n✅ Reorganization complete!")

if __name__ == "__main__":
    main()
