"""Context retriever that combines Notion and Google Sheets data."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

try:
    from rank_bm25 import BM25Okapi
    from pythainlp.tokenize import word_tokenize
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False

if TYPE_CHECKING:
    from core.ai_support_bot.rag.notion_fetcher import NotionFetcher
    from core.ai_support_bot.rag.sheets_fetcher import SheetsFetcher
    from core.ai_support_bot.ai.embedding import EmbeddingEngine
    from core.ai_support_bot.rag.vector_store import VectorStore

logger = logging.getLogger("ai_support_bot.rag.retriever")

# Cosine distance threshold: lower = more similar. 
# Chunks with distance > this value are considered irrelevant.
# OpenAI embeddings typical distances for related text in Thai are 0.5 - 0.8.
# (ปรับขึ้นเป็น 0.90 - 1.0 ถ้าอยากได้ความแม่นยำลดลง / ดึงข้อมูลเผื่อมามากขึ้น)
MAX_DISTANCE = 0.95


class ContextRetriever:
    """Retrieves relevant context using Semantic Vector Search and BM25 (Hybrid)."""

    def __init__(
        self,
        embedding_engine: 'EmbeddingEngine' | None = None,
        vector_store: 'VectorStore' | None = None,
        notion_fetcher: 'NotionFetcher' | None = None,
        sheets_fetcher: 'SheetsFetcher' | None = None,
    ):
        """Initialize with vector components."""
        self.embedding_engine = embedding_engine
        self.vector_store = vector_store
        self.notion_fetcher = notion_fetcher
        self.sheets_fetcher = sheets_fetcher
        
        self.bm25: BM25Okapi | None = None
        self.corpus_docs: list[str] = []
        
        # Build BM25 index on start if data exists
        if HAS_BM25 and self.vector_store:
            self._rebuild_bm25_index()

    def _rebuild_bm25_index(self):
        """Rebuild BM25 index from all documents in ChromaDB."""
        try:
            results = self.vector_store._collection.get()
            docs = results.get("documents", [])
            if not docs:
                return
            
            self.corpus_docs = docs
            # Tokenize docs using PyThaiNLP
            tokenized_corpus = [word_tokenize(doc, engine="newmm") for doc in docs]
            self.bm25 = BM25Okapi(tokenized_corpus)
            logger.info(f"Built BM25 index with {len(docs)} documents.")
        except Exception as e:
            logger.error(f"Failed to build BM25 index: {e}")

    async def retrieve(self, query: str, top_k: int = 5) -> list[str]:
        """Retrieve using Hybrid Search (Vector + BM25) and merge results."""
        if not self.embedding_engine or not self.vector_store:
            logger.warning("Vector search components not initialized.")
            return []
            
        combined_chunks = set()
        
        # 1. Vector Search
        try:
            query_embeddings = await self.embedding_engine.embed([query])
            if query_embeddings:
                query_vector = query_embeddings[0]
                matched_docs = self.vector_store.query(query_vector, n_results=top_k * 2)
                
                vector_chunks_kept = 0
                for doc, distance in matched_docs:
                    if distance > MAX_DISTANCE:
                        continue
                    combined_chunks.add(doc)
                    vector_chunks_kept += 1
                    
                    if vector_chunks_kept >= top_k:
                        break
                logger.info(f"Vector search retrieved {vector_chunks_kept} valid chunks")
        except Exception as e:
            logger.error(f"Failed semantic retrieval: {e}")
            
        # 2. BM25 Keyword Search
        bm25_chunks_kept = 0
        if self.bm25 and HAS_BM25:
            try:
                # Rebuild if empty
                if not self.corpus_docs:
                    self._rebuild_bm25_index()
                
                if self.bm25:
                    tokenized_query = word_tokenize(query, engine="newmm")
                    m25_scores = self.bm25.get_scores(tokenized_query)
                    
                    # Sort indices by score desc
                    top_n = sorted(range(len(m25_scores)), key=lambda i: m25_scores[i], reverse=True)[:top_k]
                    for idx in top_n:
                        if m25_scores[idx] > 0: # Only keep if there's *some* match
                            doc = self.corpus_docs[idx]
                            combined_chunks.add(doc)
                            bm25_chunks_kept += 1
                logger.info(f"BM25 keyword search retrieved {bm25_chunks_kept} valid chunks")
            except Exception as e:
                logger.error(f"Failed BM25 retrieval: {e}")
                
        # Return unique chunks combined
        final_chunks = list(combined_chunks)
        # Limit total to prevent giant prompt (even though filter handles it)
        if len(final_chunks) > top_k * 2:
            final_chunks = final_chunks[:top_k * 2]
            
        logger.info(f"Total hybrid retrieved: {len(final_chunks)} unique chunks for: {query[:50]}")
        return final_chunks
