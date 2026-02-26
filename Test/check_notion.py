import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath('.'))
load_dotenv('core/ai_support_bot/.env')

from core.ai_support_bot.config import load_config
from core.ai_support_bot.rag.notion_fetcher import NotionFetcher
from notion_client import Client

async def main():
    config = load_config('core/ai_support_bot/.env')
    client = Client(auth=config.notion_token)
    fetcher = NotionFetcher(client)
    fetcher.fetch_tree(config.notion_page_ids, config.notion_database_ids)
    pages = fetcher._cached_pages
    
    print(f"Total pages: {len(pages)}")
    for p in pages:
        if 'bizzare' in p.title.lower() or 'boss' in p.title.lower() or 'raid' in p.title.lower():
            print(f"--- {p.title} ({p.id}) ---")
            print(p.content[:2000])

if __name__ == "__main__":
    asyncio.run(main())
