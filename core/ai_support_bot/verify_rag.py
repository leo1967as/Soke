
import asyncio
import os
from pathlib import Path
from core.ai_support_bot.config import load_config
from core.ai_support_bot.rag.notion_fetcher import NotionFetcher
from core.ai_support_bot.rag.sheets_fetcher import SheetsFetcher
from core.ai_support_bot.rag.retriever import ContextRetriever
from core.ai_support_bot.rag.ingestion import DataIngestionTask
from notion_client import Client as NotionClient

async def main():
    print("=== RAG Internal Verification ===")
    
    # 1. Load config
    config = load_config()
    print(f"Config loaded (Notion Pages: {len(config.notion_page_ids)}, DBs: {len(config.notion_database_ids)})")
    
    # 2. Init fetchers
    notion_client = NotionClient(auth=config.notion_token)
    notion_fetcher = NotionFetcher(notion_client)
    
    sheets_fetcher = None
    if config.google_sa_base64:
        try:
            sheets_fetcher = SheetsFetcher.from_base64_sa(config.google_sa_base64)
            print("Sheets fetcher initialized")
        except Exception as e:
            print(f"Sheets error: {e}")

    # 3. Create retriever and ingestion task
    retriever = ContextRetriever(notion_fetcher, sheets_fetcher)
    
    ingestion = DataIngestionTask(
        notion_fetcher=notion_fetcher,
        sheets_fetcher=sheets_fetcher,
        notion_page_ids=config.notion_page_ids,
        notion_database_ids=config.notion_database_ids,
        sheets_spreadsheet_ids=config.sheets_spreadsheet_ids
    )

    # 4. Perform ingestion
    print("\nStarting ingestion...")
    await ingestion.ingest_now()
    
    # 5. Inspect cache
    print("\n=== Lodaed Data ===")
    notion_pages = notion_fetcher._cached_pages
    print(f"Notion pages in cache: {len(notion_pages)}")
    for p in notion_pages:
        print(f" - [Notion] {p.title} ({len(p.content or '')} chars)")
        if len(p.content or '') < 100:
            print(f"   Content: {p.content}")

    sheets_rows = getattr(sheets_fetcher, '_cached_rows', []) if sheets_fetcher else []
    print(f"Sheets rows in cache: {len(sheets_rows)}")
    for r in sheets_rows[:5]:
        print(f" - [Sheets] {r.title}: {r.text[:100]}...")

    # 6. Test retrieval
    test_queries = ["ร้านชื่อไร", "โปรโมชั่น", "Sokeber"]
    print("\n=== Test Retrieval ===")
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        chunks = await retriever.retrieve(query)
        if chunks:
            print(f"Found {len(chunks)} chunks:")
            for c in chunks:
                print(f"--- Chunk Start ---\n{c}\n--- Chunk End ---")
        else:
            print("No chunks found.")
            
            # Debug keyword splitting
            keywords = query.lower().split()
            print(f"Keywords used: {keywords}")

if __name__ == "__main__":
    asyncio.run(main())
