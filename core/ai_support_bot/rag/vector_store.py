"""Vector database manager using ChromaDB for Parent-Child semantic search."""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path

import chromadb

logger = logging.getLogger("ai_support_bot.rag.vector_store")


class VectorStore:
    """Manages ChromaDB with Parent-Child architecture.
    
    - 'children' collection: Small chunks used for precise vector search
    - 'parent_docs' dict: Full parent documents mapped by parent_id
    """
    
    def __init__(self, persist_dir: str = "./chroma_db", collection_name: str = "sokeber_knowledge"):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        # Parent document store
        self.parent_docs_path = self.persist_dir / "parent_docs.json"
        self.parent_docs: dict[str, str] = self._load_parent_docs()
        logger.info(f"Initialized VectorStore at {persist_dir} (Collection: {collection_name}, Parents: {len(self.parent_docs)})")

    def _load_parent_docs(self) -> dict[str, str]:
        """Load parent documents from disk."""
        if self.parent_docs_path.exists():
            try:
                with open(self.parent_docs_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load parent docs: {e}")
        return {}

    def _save_parent_docs(self):
        """Save parent documents to disk."""
        try:
            with open(self.parent_docs_path, "w", encoding="utf-8") as f:
                json.dump(self.parent_docs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save parent docs: {e}")

    def reset_collection(self):
        """Delete and recreate the collection. Used for full refresh (!sync)."""
        try:
            self.client.delete_collection(name=self.collection_name)
        except ValueError:
            pass
        
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self.parent_docs = {}
        if self.parent_docs_path.exists():
            self.parent_docs_path.unlink()
        logger.info(f"Reset VectorStore collection '{self.collection_name}'")

    def add_parent_document(self, parent_id: str, full_text: str):
        """Store a full parent document in memory (call save_parent_docs() after batch)."""
        self.parent_docs[parent_id] = full_text

    def save_parent_docs(self):
        """Persist all parent documents to disk. Call once after a batch of add_parent_document()."""
        self._save_parent_docs()

    def add_documents(self, texts: list[str], embeddings: list[list[float]], metadatas: list[dict]):
        """Add child chunks with their embeddings and metadata (including parent_id)."""
        if not texts:
            return
            
        ids = [str(uuid.uuid4()) for _ in texts]
        
        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
        logger.debug(f"Added {len(texts)} child chunks to vector store.")

    def query(self, query_embedding: list[float], n_results: int = 5) -> list[tuple[str, float, dict]]:
        """Query for most similar child chunks.
        
        Returns:
            List of tuples: (child_text, distance, metadata)
        """
        if self.collection.count() == 0:
            return []
            
        n = min(n_results, self.collection.count())
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n,
            include=["documents", "distances", "metadatas"]
        )
        
        matched = []
        if results and results.get("documents") and results["documents"][0]:
            docs = results["documents"][0]
            distances = results["distances"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            
            for doc, dist, meta in zip(docs, distances, metas):
                matched.append((doc, dist, meta))
                
        return matched

    def get_parent(self, parent_id: str) -> str | None:
        """Retrieve the full parent document by its ID."""
        return self.parent_docs.get(parent_id)
