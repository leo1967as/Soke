"""Engine for generating vector embeddings from text via OpenRouter API."""

from __future__ import annotations

import logging
from openai import AsyncOpenAI

logger = logging.getLogger("ai_support_bot.ai.embedding")

class EmbeddingEngine:
    """Uses OpenRouter's OpenAI-compatible API to generate text embeddings."""
    
    def __init__(self, api_key: str, model: str = "openai/text-embedding-3-small"):
        self.api_key = api_key
        self.model = model
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        logger.info(f"Initialized EmbeddingEngine with model {self.model}")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Convert a list of strings into embedding vectors.
        
        Args:
            texts: List of text strings to embed.
            
        Returns:
            List of embedding vectors (list of floats).
        """
        if not texts:
            return []
            
        try:
            # We batch texts to process efficiently
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            # The API returns them in the same order
            embeddings = [item.embedding for item in response.data]
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
