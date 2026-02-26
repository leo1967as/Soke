"""Text chunking for vector indexing.

Splits long documents into overlapping chunks suitable for embedding and retrieval.
"""

from dataclasses import dataclass

CHUNK_SIZE = 400
CHUNK_OVERLAP = 80


@dataclass(frozen=True)
class Chunk:
    """A single text chunk with metadata."""
    id: str
    text: str
    source_id: str
    start_offset: int


def chunk_text(
    text: str,
    source_id: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    """Split text into overlapping chunks.

    Args:
        text: The full document text.
        source_id: Identifier for the source document.
        chunk_size: Maximum characters per chunk.
        overlap: Character overlap between consecutive chunks.

    Returns:
        List of Chunk objects.
    """
    if not text or not text.strip():
        return []

    text = text.strip()
    chunks: list[Chunk] = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_text_slice = text[start:end]

        # Only add non-empty chunks
        if chunk_text_slice.strip():
            chunks.append(
                Chunk(
                    id=f"{source_id}_chunk_{start}",
                    text=chunk_text_slice,
                    source_id=source_id,
                    start_offset=start,
                )
            )

        # If we've reached the end, stop
        if end >= len(text):
            break

        # Advance with overlap
        next_start = start + chunk_size - overlap
        if next_start <= start:
            # Safety: always advance at least 1 char to avoid infinite loop
            next_start = start + 1
        start = next_start

    return chunks
