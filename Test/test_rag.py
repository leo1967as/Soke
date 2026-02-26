import asyncio
import os
import sys

# Add the project root to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.ai_support_bot.config import load_config
from core.ai_support_bot.ai.embedding import EmbeddingEngine
from core.ai_support_bot.ai.openrouter import OpenRouterEngine
from core.ai_support_bot.rag.vector_store import VectorStore
from core.ai_support_bot.rag.notion_fetcher import NotionFetcher
from core.ai_support_bot.rag.retriever import ContextRetriever
from core.ai_support_bot.rag.ingestion import DataIngestionTask

async def main():
    print("Loading config...")
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core", "ai_support_bot", ".env"))
    config = load_config(env_path)
    
    print("Initializing components...")
    embedding = EmbeddingEngine(api_key=config.openrouter_api_key, model=config.embedding_model)
    llm = OpenRouterEngine(api_key=config.openrouter_api_key, model=config.llm_model)
    vector_store = VectorStore(persist_dir="./core/ai_support_bot/chroma_db")
    
    from notion_client import Client
    notion_client = Client(auth=config.notion_token)
    notion_fetcher = NotionFetcher(notion_client)
    
    ingestion = DataIngestionTask(
        embedding_engine=embedding,
        vector_store=vector_store,
        notion_fetcher=notion_fetcher,
        sheets_fetcher=None,
        interval_seconds=0,
        notion_page_ids=config.notion_page_ids,
        notion_database_ids=config.notion_database_ids,
        sheets_spreadsheet_ids=config.sheets_spreadsheet_ids,
    )
    
    retriever = ContextRetriever(
        embedding_engine=embedding,
        vector_store=vector_store,
        notion_fetcher=notion_fetcher,
        sheets_fetcher=None,
    )

    print("\n--- INGESTION ---")
    await ingestion.ingest_notion_only() 
    
    collection_count = vector_store.collection.count()
    parent_count = len(vector_store.parent_docs)
    print(f"Index built: {parent_count} parents, {collection_count} child chunks")
    
    question = "Raid Boss ลงแล้วได้ไรบ้างอะ Bizzare"
    print(f"\n--- QUERY: {question} ---")
    
    expanded = await llm.generate_hyde_query(question)
    print(f"HyDE: {expanded}")
    
    raw_chunks = await retriever.retrieve(expanded, top_k=10)
    print(f"\nRetrieved {len(raw_chunks)} parents.")
    for i, c in enumerate(raw_chunks):
        title = c.split('\n')[0] if '\n' in c else c[:60]
        print(f"[{i}] {title.strip()}")
        
    print("\n--- RERANK ---")
    reranked = await llm.rerank_context_chunks(question, raw_chunks, top_n=3)
    print(f"Reranked {len(reranked)} parents.")
    for i, c in enumerate(reranked):
        title = c.split('\n')[0] if '\n' in c else c[:60]
        print(f"[{i}] {title.strip()}")
    
    if reranked:
        print("\n=== TOP CHUNK CONTENT ===")
        print(reranked[0][:1000])
        print("=========================")
        
    print("\n--- LLM ANSWER ---")
    result = await llm.generate(question, reranked)
    print(result.text)

if __name__ == "__main__":
    asyncio.run(main())
