import requests
import json
import os

class DiscordManager:
    def __init__(self, token_path):
        self.token = self._load_token(token_path)
        self.headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://discord.com/api/v10"

    def _load_token(self, path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            # Handle format OREO_MM = TOKEN
            if "=" in content:
                return content.split("=")[1].strip()
            return content

    def get_channels(self, guild_id):
        url = f"{self.base_url}/guilds/{guild_id}/channels"
        res = requests.get(url, headers=self.headers)
        return res.json() if res.status_code == 200 else []

    def move_channel(self, channel_id, category_id, position=None):
        url = f"{self.base_url}/channels/{channel_id}"
        payload = {"parent_id": category_id}
        if position is not None:
            payload["position"] = position
        res = requests.patch(url, headers=self.headers, json=payload)
        return res.status_code == 200, res.text

    def rename_channel(self, channel_id, new_name):
        url = f"{self.base_url}/channels/{channel_id}"
        payload = {"name": new_name}
        res = requests.patch(url, headers=self.headers, json=payload)
        return res.status_code == 200, res.text

    def delete_channel(self, channel_id):
        url = f"{self.base_url}/channels/{channel_id}"
        res = requests.delete(url, headers=self.headers)
        return res.status_code == 200, res.text

    def create_channel(self, guild_id, name, type=0, parent_id=None):
        url = f"{self.base_url}/guilds/{guild_id}/channels"
        payload = {"name": name, "type": type}
        if parent_id:
            payload["parent_id"] = parent_id
        res = requests.post(url, headers=self.headers, json=payload)
        return res.status_code == 201, res.text

if __name__ == "__main__":
    # Test/Example Usage
    TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
    GUILD_ID = "1475450344334037063"
    
    manager = DiscordManager(TOKEN_FILE)
    print("Discord Utility Loaded.")
