import sys
import json
from discord_utils import DiscordManager

def debug_channels():
    TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
    GUILD_ID = "1475450344334037063"
    
    manager = DiscordManager(TOKEN_FILE)
    channels = manager.get_channels(GUILD_ID)
    
    ids = ["1475451972311187528", "1475957424992161926"]
    
    for c in channels:
        if c["id"] in ids:
            print(f"Channel: {c['name']} (Type: {c['type']}, PID: {c.get('parent_id')})")

if __name__ == "__main__":
    debug_channels()
