import requests
import json

TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
CHAN_ID = "1476201306598150274" # Verify channel

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

def send_command_msg():
    # We send !setup_verify but we need to do it as a user or the bot needs to hear it from somewhere.
    # Actually, the bot has administrator perms. 
    # I can just use the tool to send the message to the channel where it can hear it.
    url = f"https://discord.com/api/v10/channels/{CHAN_ID}/messages"
    payload = {"content": "!setup_verify"}
    res = requests.post(url, headers=headers, json=payload)
    print(f"Sent Command: {res.status_code} {res.text[:100]}")

if __name__ == "__main__":
    send_command_msg()
