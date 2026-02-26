import requests

TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
CHAN_ID = "1476201306598150274" # Verify channel

def load_token(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if "=" in content:
            return content.split("=")[1].strip()
        return content

token = load_token(TOKEN_FILE)
headers = {"Authorization": f"Bot {token}"}

res = requests.get(f"https://discord.com/api/v10/channels/{CHAN_ID}/messages?limit=10", headers=headers)
messages = res.json()
for msg in messages:
    print(f"[{msg['author']['username']}]: {msg['content']} (Embeds: {len(msg.get('embeds', []))}, Components: {len(msg.get('components', []))})")
