import sys
import json
from discord_utils import DiscordManager

def count_work_system():
    TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
    GUILD_ID = "1475450344334037063"
    WORK_CAT_ID = "1475450952667500636"
    SYSTEM_CAT_ID = "1475715213641908356"
    
    manager = DiscordManager(TOKEN_FILE)
    channels = manager.get_channels(GUILD_ID)
    
    work_list = [c["name"] for c in channels if c.get("parent_id") == WORK_CAT_ID]
    system_list = [c["name"] for c in channels if c.get("parent_id") == SYSTEM_CAT_ID]
    
    print(f"Channels in Work: {work_list}")
    print(f"Channels in System: {system_list}")

if __name__ == "__main__":
    count_work_system()
