import sys
import logging
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from core.ai_support_bot.config import load_config
from core.ai_support_bot.rag.notion_fetcher import NotionFetcher
from core.ai_support_bot.rag.sheets_fetcher import SheetsFetcher
from core.ai_support_bot.rag.ingestion import DataIngestionTask

# Setup minimal logging to stdout
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("verify")

async def test_init():
    logger.info("Starting bot initialization test...")
    
    try:
        config = load_config()
        logger.info("✓ Config loaded successfully")
        logger.info(f"  - Notion Page IDs: {config.notion_page_ids}")
        logger.info(f"  - Notion Database IDs: {config.notion_database_ids}")
        logger.info(f"  - Sheets IDs: {config.sheets_spreadsheet_ids}")
    except Exception as e:
        logger.error(f"✗ Config failure: {e}")
        return

    # Test Notion
    if config.notion_token:
        try:
            from notion_client import Client
            client = Client(auth=config.notion_token)
            fetcher = NotionFetcher(client)
            logger.info("✓ NotionFetcher initialized")
            
            # Test database query if IDs exist
            for db_id in config.notion_database_ids:
                logger.info(f"Testing Notion DB query for: {db_id}")
                pages = fetcher.fetch_database_pages(db_id)
                logger.info(f"  ✓ Found {len(pages)} pages")
        except Exception as e:
            logger.error(f"✗ Notion failure: {e}")
    
    # Test Sheets
    if config.google_sa_base64:
        try:
            fetcher = SheetsFetcher.from_base64_sa(config.google_sa_base64)
            logger.info("✓ SheetsFetcher initialized")
            
            for sid in config.sheets_spreadsheet_ids:
                logger.info(f"Testing Sheets fetch for: {sid}")
                # We'll just test the metadata to avoid hanging on large sheet
                service = fetcher._get_service()
                meta = service.spreadsheets().get(spreadsheetId=sid).execute()
                logger.info(f"  ✓ Found spreadsheet: {meta.get('properties', {}).get('title')}")
        except Exception as e:
            logger.error(f"✗ Sheets failure: {e}")

    logger.info("Initialization test complete.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_init())
