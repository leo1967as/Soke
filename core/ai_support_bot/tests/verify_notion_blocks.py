
import asyncio
from core.ai_support_bot.config import load_config
from core.ai_support_bot.rag.notion_fetcher import NotionFetcher
from notion_client import Client as NotionClient

async def main():
    config = load_config()
    notion_client = NotionClient(auth=config.notion_token)
    notion_fetcher = NotionFetcher(notion_client)
    
    root_page_id = config.notion_page_ids[0]
    print(f"Fetching blocks for root page: {root_page_id}")
    
    blocks = notion_fetcher._fetch_all_blocks(root_page_id)
    print(f"Total blocks in root page: {len(blocks)}")
    
    for b in blocks:
        b_type = b.get("type", "")
        if b_type in ["child_page", "child_database", "link_to_page"]:
            print(f"Found sub-item: type={b_type}, data={b.get(b_type, {})}, id={b['id']}")

if __name__ == "__main__":
    asyncio.run(main())
