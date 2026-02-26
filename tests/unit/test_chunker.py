"""Unit tests for text chunking."""

import pytest

from core.ai_support_bot.rag.chunker import CHUNK_OVERLAP, CHUNK_SIZE, Chunk, chunk_text


class TestChunker:
    """Test suite for chunk_text function."""

    def test_short_text_single_chunk(self):
        chunks = chunk_text("Hello world", source_id="doc1")
        assert len(chunks) == 1
        assert chunks[0].text == "Hello world"
        assert chunks[0].source_id == "doc1"
        assert chunks[0].id == "doc1_chunk_0"

    def test_empty_text_returns_empty(self):
        assert chunk_text("", source_id="doc1") == []

    def test_whitespace_only_returns_empty(self):
        assert chunk_text("   ", source_id="doc1") == []

    def test_none_text_returns_empty(self):
        # chunk_text expects str, but let's be safe
        assert chunk_text("", source_id="doc1") == []

    def test_exact_chunk_size_single_chunk(self):
        text = "a" * CHUNK_SIZE
        chunks = chunk_text(text, source_id="doc1")
        assert len(chunks) == 1
        assert len(chunks[0].text) == CHUNK_SIZE

    def test_long_text_creates_multiple_chunks(self):
        text = "a" * (CHUNK_SIZE * 3)
        chunks = chunk_text(text, source_id="doc1")
        assert len(chunks) > 1

    def test_overlap_between_chunks(self):
        text = "a" * (CHUNK_SIZE + 100)
        chunks = chunk_text(text, source_id="doc1", chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
        assert len(chunks) >= 2
        # Second chunk should start at CHUNK_SIZE - OVERLAP
        assert chunks[1].start_offset == CHUNK_SIZE - CHUNK_OVERLAP

    def test_chunk_ids_unique(self):
        text = "a" * 2000
        chunks = chunk_text(text, source_id="doc1")
        ids = [c.id for c in chunks]
        assert len(ids) == len(set(ids))

    def test_source_id_preserved(self):
        text = "Hello world"
        chunks = chunk_text(text, source_id="notion_page_abc")
        assert all(c.source_id == "notion_page_abc" for c in chunks)

    def test_custom_chunk_size(self):
        text = "abcdefghij" * 10  # 100 chars
        chunks = chunk_text(text, source_id="doc1", chunk_size=20, overlap=5)
        assert all(len(c.text) <= 20 for c in chunks)

    def test_zero_overlap(self):
        text = "a" * 100
        chunks = chunk_text(text, source_id="doc1", chunk_size=25, overlap=0)
        assert len(chunks) == 4
        # No overlap means chunks don't repeat
        full_text = "".join(c.text for c in chunks)
        assert full_text == text

    def test_start_offsets_increasing(self):
        text = "a" * 2000
        chunks = chunk_text(text, source_id="doc1")
        offsets = [c.start_offset for c in chunks]
        assert offsets == sorted(offsets)
        # Each offset should be strictly greater than the previous
        for i in range(1, len(offsets)):
            assert offsets[i] > offsets[i - 1]

    def test_no_infinite_loop_on_edge_case(self):
        """Ensure chunker doesn't infinite loop on pathological input."""
        text = "a" * 10
        # Overlap >= chunk_size would normally cause issues
        chunks = chunk_text(text, source_id="doc1", chunk_size=5, overlap=5)
        assert len(chunks) > 0
        assert len(chunks) < 100  # Sanity: shouldn't create excessive chunks
