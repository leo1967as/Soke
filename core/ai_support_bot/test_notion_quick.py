"""Quick test to verify Notion connection and database/page access."""

import sys
from pathlib import Path

# Add root directory to python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from notion_client import Client
from core.ai_support_bot.config import load_config
from core.ai_support_bot.rag.notion_fetcher import NotionFetcher

print("=" * 60)
print("Notion Connection Test")
print("=" * 60)
print()

# Test 1: Connect to Notion
print("[1/3] Loading Configuration and Connecting to Notion...")
try:
    config = load_config(str(Path(__file__).parent / ".env"))
    client = Client(auth=config.notion_token)
    fetcher = NotionFetcher(client)
    print("✓ Connected to Notion using .env settings")
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 2: Try to fetch Pages
print()
print("[2/3] Fetching Page IDs...")
if config.notion_page_ids:
    for pid in config.notion_page_ids:
        print(f"  - Page ID: {pid}")
        try:
            page = fetcher.fetch_page_content(pid)
            print(f"    ✓ Success - Title: {page.title} ({len(page.content)} chars extract)")
        except Exception as e:
            print(f"    ✗ Failed to fetch page: {e}")
else:
    print("  - No Page IDs configured.")

# Test 3: Try to fetch Databases
print()
print("[3/3] Fetching Database IDs...")
if config.notion_database_ids:
    for dbid in config.notion_database_ids:
        print(f"  - Database ID: {dbid}")
        try:
            pages = fetcher.fetch_database_pages(dbid)
            print(f"    ✓ Query successful. Found {len(pages)} pages.")
            for p in pages[:2]:
                print(f"      > {p.title}")
            if len(pages) > 2:
                print(f"      > ... and {len(pages) - 2} more")
        except Exception as e:
            print(f"    ✗ Failed to fetch database: {e}")
else:
    print("  - No Database IDs configured.")

print()
print("=" * 60)
print("✓ Test script execution finished!")
print("=" * 60)
print()
