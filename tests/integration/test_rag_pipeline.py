"""Integration tests for the RAG pipeline — chunking + cache + prompt flow."""

import pytest

from core.ai_support_bot.cache.memory_cache import MemoryCache
from core.ai_support_bot.rag.chunker import chunk_text


class TestRAGPipeline:
    """Test the full RAG flow: chunk → cache → prompt construction."""

    def test_chunk_and_cache_round_trip(self):
        """Simulate: Notion page → chunk → cache → retrieve."""
        # Step 1: Chunk a document
        doc_text = (
            "Sokeber provides cloud-based financial tools. "
            "Our pricing starts at $10/month for the Basic plan. "
            "The Pro plan costs $30/month and includes advanced analytics. "
            "Enterprise plans are custom-quoted. "
            "Refund policy: Full refund within 30 days of purchase. "
            "Support hours: Monday-Friday 9AM-6PM Bangkok time."
        )
        chunks = chunk_text(doc_text, source_id="notion_faq_001", chunk_size=100, overlap=20)

        assert len(chunks) > 1
        assert all(c.source_id == "notion_faq_001" for c in chunks)

        # Step 2: Cache each chunk
        cache = MemoryCache(default_ttl=60)
        for chunk in chunks:
            cache.set(chunk.id, chunk.text)

        # Step 3: Verify retrieval
        first_chunk = cache.get(chunks[0].id)
        assert first_chunk is not None
        assert "Sokeber" in first_chunk

    def test_answer_cache_deduplication(self):
        """Same question asked twice should hit cache on second call."""
        cache = MemoryCache(default_ttl=60)

        question = "What is the pricing?"
        answer = "Basic plan: $10/month. Pro plan: $30/month."

        # First call: miss
        assert cache.get(question) is None

        # Store answer
        cache.set(question, answer)

        # Second call: hit
        assert cache.get(question) == answer

    def test_cache_different_questions(self):
        """Different questions should not collide."""
        cache = MemoryCache(default_ttl=60)

        cache.set("pricing question", "answer about pricing")
        cache.set("refund question", "answer about refunds")

        assert cache.get("pricing question") == "answer about pricing"
        assert cache.get("refund question") == "answer about refunds"

    def test_full_pipeline_simulation(self):
        """End-to-end: document → chunks → search (simple) → prompt context."""
        # Simulate multiple documents
        docs = [
            ("doc_1", "Sokeber Basic plan costs $10 per month. Includes 5 users."),
            ("doc_2", "Sokeber Pro plan costs $30 per month. Includes unlimited users."),
            ("doc_3", "Refund policy: 30-day money back guarantee for all plans."),
        ]

        all_chunks = []
        for doc_id, text in docs:
            chunks = chunk_text(text, source_id=doc_id, chunk_size=200, overlap=0)
            all_chunks.extend(chunks)

        # Simple keyword search (Phase 0 — no vector store yet)
        query = "pricing"
        relevant = [c for c in all_chunks if query.lower() in c.text.lower()]

        # Should not match the refund doc
        assert len(relevant) == 0  # "pricing" not literally in the text

        # Try a term that IS in the text
        query2 = "costs"
        relevant2 = [c for c in all_chunks if query2.lower() in c.text.lower()]
        assert len(relevant2) == 2  # doc_1 and doc_2

        # Build context for prompt
        context_texts = [c.text for c in relevant2]
        assert "$10" in context_texts[0] or "$10" in context_texts[1]
        assert "$30" in context_texts[0] or "$30" in context_texts[1]
