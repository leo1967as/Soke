"""Vector database manager using ChromaDB for persistent semantic search."""

from __future__ import annotations

import logging
import uuid
import chromadb

logger = logging.getLogger("ai_support_bot.rag.vector_store")

class VectorStore:
    """Manages the persistent ChromaDB collection for semantic RAG."""
    
    def __init__(self, persist_dir: str = "./chroma_db", collection_name: str = "sokeber_knowledge"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Initialized VectorStore at {persist_dir} (Collection: {collection_name})")

    def reset_collection(self):
        """Delete and recreate the collection. Used for full refresh (!sync)."""
        try:
            self.client.delete_collection(name=self.collection_name)
        except ValueError:
            pass # Ignore if it doesn't exist yet
        
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Reset VectorStore collection '{self.collection_name}'")

    def add_documents(self, texts: list[str], embeddings: list[list[float]], metadatas: list[dict]):
        """Upsert a batch of documents and their pre-computed embeddings."""
        if not texts:
            return
            
        # Generate stable IDs from source/title or just random
        ids = [str(uuid.uuid4()) for _ in texts]
        
        # Batch insert
        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
        logger.debug(f"Added {len(texts)} documents to vector store.")

    def query(self, query_embedding: list[float], n_results: int = 5) -> list[tuple[str, float]]:
        """Query the database for the most semantically similar documents.
        
        Returns:
            List of tuples: (document_text, similarity_distance)
            Note: For cosine space in ChromaDB, lower distance = higher similarity.
        """
        if self.collection.count() == 0:
            return []
            
        # We ensure n_results is not greater than the collection size
        n = min(n_results, self.collection.count())
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n
        )
        
        matched_docs = []
        if results and results.get("documents") and results["documents"][0]:
            docs = results["documents"][0]
            distances = results["distances"][0]
            
            for doc, dist in zip(docs, distances):
                matched_docs.append((doc, dist))
                
        return matched_docs
