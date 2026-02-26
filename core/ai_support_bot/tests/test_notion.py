"""Quick test script to verify Notion connection and data retrieval."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.ai_support_bot.config import load_config
from core.ai_support_bot.rag.notion_fetcher import NotionFetcher
from notion_client import Client


def main():
    print("=" * 60)
    print("Notion Connection Test")
    print("=" * 60)
    print()

    # Load config
    print("[1/4] Loading configuration...")
    try:
        config = load_config(Path(__file__).parent / ".env")
        print(f"✓ Config loaded")
        print(f"  - Notion token: {config.notion_token[:20]}...")
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        return

    # Connect to Notion
    print()
    print("[2/4] Connecting to Notion...")
    try:
        client = Client(auth=config.notion_token)
        fetcher = NotionFetcher(client)
        print("✓ Connected to Notion")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return

    # Get database ID from user
    print()
    print("[3/4] Enter your Notion Database ID")
    print("(Find it in the URL: notion.so/workspace/DATABASE_ID?v=...)")
    database_id = input("Database ID: ").strip()

    if not database_id:
        print("✗ No database ID provided")
        return

    # Fetch pages
    print()
    print("[4/4] Fetching pages from database...")
    try:
        pages = fetcher.fetch_database_pages(database_id)
        print(f"✓ Found {len(pages)} pages")
        print()

        if pages:
            print("=" * 60)
            print("Sample Pages:")
            print("=" * 60)
            for i, page in enumerate(pages[:3], 1):
                print(f"\n[Page {i}]")
                print(f"Title: {page.title}")
                print(f"Content ({len(page.content)} chars):")
                print(page.content[:200] + "..." if len(page.content) > 200 else page.content)
                print("-" * 60)
        else:
            print("⚠ No pages found in database")
            print("Make sure:")
            print("  1. Database has content")
            print("  2. Integration is connected to the database")
            print("  3. Database ID is correct")

    except Exception as e:
        print(f"✗ Failed to fetch pages: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Check if database ID is correct")
        print("  2. Verify integration has access to the database")
        print("  3. Check Notion token is valid")
        return

    print()
    print("=" * 60)
    print("✓ Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
