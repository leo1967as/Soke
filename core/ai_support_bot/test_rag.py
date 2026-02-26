import asyncio
import logging
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.ai_support_bot.config import load_config
from core.ai_support_bot.ai.embedding import EmbeddingEngine
from core.ai_support_bot.rag.vector_store import VectorStore
from core.ai_support_bot.rag.retriever import ContextRetriever

logging.basicConfig(level=logging.INFO)

async def test_rag():
    config = load_config()
    
    print("1. Initializing EmbeddingEngine...")
    embedding_engine = EmbeddingEngine(
        api_key=config.openrouter_api_key,
        model=config.embedding_model
    )
    
    print("2. Initializing VectorStore...")
    vector_store = VectorStore()
    
    print("3. Initializing ContextRetriever...")
    retriever = ContextRetriever(
        embedding_engine=embedding_engine,
        vector_store=vector_store
    )
    
    print("4. Testing embedding...")
    test_texts = ["นี่คือประโยคทดสอบระบบ Vector Database เพื่อการค้นหาเนื้อหา", "โดนโกงทำไงดี", "แอดมินบิดครับ"]
    embeddings = await embedding_engine.embed(test_texts)
    print(f"   => Embedded {len(embeddings)} texts, first vector len {len(embeddings[0])}")
    
    print("5. Resetting and Adding to VectorStore...")
    vector_store.reset_collection()
    metadatas = [{"source": "test", "title": f"Title {i}"} for i in range(len(test_texts))]
    vector_store.add_documents(test_texts, embeddings, metadatas)
    
    print("6. Testing query: 'เรื่องระบบทุจริตโกงเงินบิดแอดมิน'")
    query = "เรื่องระบบทุจริตโกงเงินบิดแอดมิน"
    results = await retriever.retrieve(query, top_k=2)
    print(f"   => Query returned: {results}")
    
    print("\nSUCCESS! RAG Vector Search flow works correctly.")

if __name__ == "__main__":
    asyncio.run(test_rag())
