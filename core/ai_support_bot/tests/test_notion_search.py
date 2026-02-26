import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()
notion_token = os.getenv("NOTION_TOKEN")
client = Client(auth=notion_token)

try:
    response = client.search()
    results = response.get("results", [])
    with open("search_output.txt", "w", encoding="utf-8") as f:
        f.write(f"Found {len(results)} pages in the workspace.\n")
        for page in results:
            title = "Untitled"
            if "properties" in page:
                for prop in page["properties"].values():
                    if prop.get("type") == "title":
                        title_arr = prop.get("title", [])
                        if title_arr:
                            title = "".join(t.get("plain_text", "") for t in title_arr)
            f.write(f"- {title} (ID: {page['id']})\n")
except Exception as e:
    print(f"Error: {e}")
