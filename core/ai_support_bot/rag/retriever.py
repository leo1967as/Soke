"""Context retriever: Hybrid Search (Vector + BM25) with Parent-Child resolution."""

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

MAX_DISTANCE = 0.95


class ContextRetriever:
    """Hybrid retriever with Parent-Child chunk resolution.
    
    Search flow:
    1. Vector search on CHILD chunks (precise paragraph-level)
    2. BM25 keyword search on CHILD chunks (exact term matching)
    3. Resolve matched children → unique PARENT documents
    4. Return full parent documents as context
    """

    def __init__(
        self,
        embedding_engine: 'EmbeddingEngine' | None = None,
        vector_store: 'VectorStore' | None = None,
        notion_fetcher: 'NotionFetcher' | None = None,
        sheets_fetcher: 'SheetsFetcher' | None = None,
    ):
        self.embedding_engine = embedding_engine
        self.vector_store = vector_store
        self.notion_fetcher = notion_fetcher
        self.sheets_fetcher = sheets_fetcher
        
        self.bm25: BM25Okapi | None = None
        self.corpus_docs: list[str] = []
        self.corpus_metas: list[dict] = []
        
        if HAS_BM25 and self.vector_store:
            self._rebuild_bm25_index()

    def _rebuild_bm25_index(self):
        """Rebuild BM25 index from all child chunks in ChromaDB."""
        try:
            results = self.vector_store.collection.get(include=["documents", "metadatas"])
            docs = results.get("documents", [])
            metas = results.get("metadatas", [])
            if not docs:
                return
            
            self.corpus_docs = docs
            self.corpus_metas = metas if metas else [{}] * len(docs)
            tokenized_corpus = [word_tokenize(doc, engine="newmm") for doc in docs]
            self.bm25 = BM25Okapi(tokenized_corpus)
            logger.info(f"Built BM25 index with {len(docs)} child chunks.")
        except Exception as e:
            logger.error(f"Failed to build BM25 index: {e}")

    async def retrieve(self, query: str, top_k: int = 5) -> list[str]:
        """Search children → resolve to unique parent documents."""
        if not self.embedding_engine or not self.vector_store:
            logger.warning("Vector search components not initialized.")
            return []
            
        matched_parent_ids: dict[str, float] = {}  # parent_id → best score
        
        # 1. Vector Search on children
        try:
            query_embeddings = await self.embedding_engine.embed([query])
            if query_embeddings:
                query_vector = query_embeddings[0]
                results = self.vector_store.query(query_vector, n_results=top_k * 3)
                
                for doc, distance, meta in results:
                    if distance > MAX_DISTANCE:
                        continue
                    parent_id = meta.get("parent_id", "")
                    if parent_id:
                        # Keep the best (lowest) distance per parent
                        if parent_id not in matched_parent_ids or distance < matched_parent_ids[parent_id]:
                            matched_parent_ids[parent_id] = distance
                
                logger.info(f"Vector search → {len(matched_parent_ids)} unique parents")
        except Exception as e:
            logger.error(f"Failed vector search: {e}")
            
        # 2. BM25 Keyword Search on children
        if self.bm25 and HAS_BM25:
            try:
                if not self.corpus_docs:
                    self._rebuild_bm25_index()
                
                if self.bm25:
                    tokenized_query = word_tokenize(query, engine="newmm")
                    scores = self.bm25.get_scores(tokenized_query)
                    
                    top_n = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k * 2]
                    bm25_added = 0
                    for idx in top_n:
                        if scores[idx] > 0 and idx < len(self.corpus_metas):
                            parent_id = self.corpus_metas[idx].get("parent_id", "")
                            if parent_id and parent_id not in matched_parent_ids:
                                matched_parent_ids[parent_id] = 0.5  # Default relevance
                                bm25_added += 1
                    logger.info(f"BM25 search → added {bm25_added} new parents")
            except Exception as e:
                logger.error(f"Failed BM25 search: {e}")
                
        # 3. Resolve parent_ids → full parent documents
        sorted_parents = sorted(matched_parent_ids.items(), key=lambda x: x[1])
        
        parent_docs = []
        for parent_id, score in sorted_parents[:top_k * 2]:
            full_doc = self.vector_store.get_parent(parent_id)
            if full_doc:
                parent_docs.append(full_doc)
                title = full_doc.split('\n')[0] if '\n' in full_doc else full_doc[:50]
                logger.info(f"  ✓ Parent '{title}' (best child dist: {score:.4f})")
        
        logger.info(f"Total: {len(parent_docs)} unique parent docs for: {query[:50]}")
        return parent_docs
