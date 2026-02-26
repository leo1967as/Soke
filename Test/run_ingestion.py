import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.abspath('.'))

from dotenv import load_dotenv
load_dotenv('core/ai_support_bot/.env')

from core.ai_support_bot.config import load_config
from core.ai_support_bot.rag.ingestion import DataIngestionTask
from core.ai_support_bot.rag.vector_store import VectorStore
from core.ai_support_bot.ai.openrouter import OpenRouterEngine

logging.basicConfig(level=logging.INFO)

async def main():
    config = load_config('core/ai_support_bot/.env')
    
    # Initialize components
    vector_store = VectorStore(persist_dir="./chroma_db")
    embedding_engine = OpenRouterEngine(api_key=config.openrouter_api_key)
    
    ingestor = DataIngestionTask(
        config=config,
        vector_store=vector_store,
        embedding_engine=embedding_engine
    )
    
    print("Starting re-ingestion...")
    await ingestor.ingest_notion_only()
    print("Ingestion complete.")

if __name__ == "__main__":
    asyncio.run(main())
