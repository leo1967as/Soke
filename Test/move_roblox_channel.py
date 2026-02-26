import requests
import sys

TOKEN = "MTQ3NjE4MzYyMTI1NjYwOTgzNA.Gx8a4k.lHDEi4VlVdL_xyDRkuaaz1Yp-xxwKcpMBikNmA"
CHANNEL_ID = "1475739990599274609"  # Roblox 3
PARENT_ID = "1475451161275400264"   # Gaming Category

url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}"
headers = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json"
}
payload = {
    "parent_id": PARENT_ID,
    "position": 2  # After Roblox 2
}

print(f"Moving channel {CHANNEL_ID} to category {PARENT_ID}...")
response = requests.patch(url, headers=headers, json=payload)

if response.status_code == 200:
    print("[PASS] Channel moved successfully!")
    # Verify
    verify_res = requests.get(url, headers=headers)
    data = verify_res.json()
    print(f"Current Parent ID: {data.get('parent_id')}")
    if data.get('parent_id') == PARENT_ID:
        print("[VERIFIED] Parent ID matches target.")
    else:
        print("[ERROR] Parent ID does not match.")
    sys.exit(0)
else:
    print(f"[FAIL] Error moving channel: {response.status_code}")
    print(response.text)
    sys.exit(1)
