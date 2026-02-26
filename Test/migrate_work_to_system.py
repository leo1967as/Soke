import sys
import json
from discord_utils import DiscordManager

def automate_move():
    TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
    GUILD_ID = "1475450344334037063"
    
    WORK_CAT_ID = "1475450952667500636"
    SYSTEM_CAT_ID = "1475715213641908356"

    manager = DiscordManager(TOKEN_FILE)
    
    print(f"--- Automated Migration: Work -> System ---")
    channels = manager.get_channels(GUILD_ID)
    
    targets = [c for c in channels if c.get("parent_id") == WORK_CAT_ID]
    
    if not targets:
        print(f"No channels found under Work category ({WORK_CAT_ID}).")
        # Check if Work itself exists
        work_exists = any(c["id"] == WORK_CAT_ID for c in channels)
        if work_exists:
            print("Work category exists but is currently empty.")
        return

    print(f"Found {len(targets)} channels to move.")
    
    for c in targets:
        print(f"Moving '{c['name']}' ({c['id']})...")
        success, res = manager.move_channel(c["id"], SYSTEM_CAT_ID)
        if success:
            print(f"  [OK] Moved.")
        else:
            print(f"  [ERROR] {res}")

    print("Migration complete.")

if __name__ == "__main__":
    automate_move()
