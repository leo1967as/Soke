"""OpenRouter integration — prompt construction and response generation.

Supports OpenRouter and any OpenAI-compatible API provider.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from openai import AsyncOpenAI

logger = logging.getLogger("ai_support_bot.ai.openrouter")

SYSTEM_PROMPT = """คุณคือผู้ช่วย AI ฝ่ายบริการลูกค้าของ Sokeber บน Discord โดยมีบุคลิกแบบ "สุคุนะ" (Sukuna จาก Jujutsu Kaisen)

กฎที่คุณต้องปฏิบัติตามอย่างเคร่งครัด:
1. คุณต้องตอบคำถามโดยอ้างอิงจาก CONTEXT ที่ให้มาเท่านั้น! หากไม่รู้คำตอบ ให้บอกไปเลยว่า "หึ เรื่องแค่นี้ไม่มีในหัวผมหรอกนะ ไปถามพวกแอดมิน Sokeber เอาเองเถอะ" หรืออะไรทำนองนี้ ห้ามมั่วข้อมูล พิมพ์ตัวเลข หรือแต่งนโยบายเองเด็ดขาด
2. *สำคัญมาก*: ห้ามพูดเด็ดขาดว่า "ใน CONTEXT กล่าวว่า..." หรือ "จากข้อมูลที่ให้ไว้..." ให้ตอบเสมือนว่าคุณรู้ทุกอย่างด้วยตัวเอง
3. บุคลิกของคุณ: เย่อหยิ่ง มั่นใจในตัวเอง ทรงอำนาจ แต่ยังคงยอมช่วยเหลือและตอบคำถามอย่างถูกต้องตรงประเด็น (แบบตัวร้ายที่มาเป็นแอดมินตอบแชท)
4. สรรพนาม: แทนตัวเองว่า "ผม" หรือ "ข้า" และเรียกคู่สนทนาว่า "แก" "พวกแก" หรือ "นาย" (ห้ามใช้คำหยาบคายรุนแรงเกินไป)
5. ห้ามใช้คำพูดแบบหุ่นยนต์เด็ดขาด เช่น "ขออภัย", "ฉันคือ AI", "ด้วยความยินดี"
6. ตอบเป็นภาษาที่ผู้ใช้ถาม (ถ้าไทยก็ตอบไทย แต่คงความหยิ่งไว้)
7. หากถามเรื่องนอกเหนือจากธุรกิจของ Sokeber ให้ปฏิเสธอย่างเย็นชาว่าไม่สนใจเรื่องไร้สาระ
8. กระชับ ตรงประเด็น ไม่ต้องอารัมภบทเยอะ
"""


@dataclass
class LLMResponse:
    """Wrapper for LLM API response."""
    text: str
    tokens_used: int
    model: str


class OpenRouterEngine:
    """Manages OpenRouter/OpenAI-compatible API calls with context-aware prompts.

    Args:
        api_key: OpenRouter or provider API key.
        model: Model identifier (e.g., "google/gemini-2.5-flash", "anthropic/claude-3.5-sonnet").
        provider: Provider name for logging (default: "openrouter").
        base_url: Optional custom base URL (default: OpenRouter).
    """

    def __init__(
        self,
        api_key: str,
        model: str = "google/gemini-2.5-flash",
        provider: str = "openrouter",
        base_url: str | None = None,
    ):
        if base_url is None:
            base_url = "https://openrouter.ai/api/v1"
        
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        self._model = model
        self._provider = provider

    def build_prompt(self, user_question: str, context_chunks: list[str]) -> str:
        """Build the final prompt with retrieved context.

        Args:
            user_question: The sanitized user question.
            context_chunks: Relevant text chunks from the knowledge base.

        Returns:
            Formatted prompt string.
        """
        if context_chunks:
            context_block = "\n---\n".join(context_chunks)
            prompt = (
                f"=== CONTEXT FROM KNOWLEDGE BASE ===\n"
                f"{context_block}\n"
                f"=== END CONTEXT ===\n\n"
                f"User Question: {user_question}"
            )
        else:
            prompt = (
                f"=== NO CONTEXT AVAILABLE ===\n"
                f"There is no relevant context in the knowledge base for this question.\n"
                f"=== END ===\n\n"
                f"User Question: {user_question}"
            )
        return prompt

    async def generate(
        self, user_question: str, context_chunks: list[str], history: list[dict] | None = None
    ) -> LLMResponse:
        """Generate a response using OpenRouter with RAG context.

        Args:
            user_question: The sanitized user question.
            context_chunks: Relevant text chunks from the knowledge base.
            history: Optional list of previous conversation messages.

        Returns:
            LLMResponse with text and token usage.
        """
        prompt = self.build_prompt(user_question, context_chunks)
        logger.info(f"[LLM SEND] Model={self._model}, context_chunks={len(context_chunks)}")
        logger.debug(f"[LLM SEND] Full prompt:\n{prompt[:500]}...")

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0.3,
                top_p=0.8,
                max_tokens=1024,
            )

            # Extract token usage
            tokens = 0
            if response.usage:
                tokens = response.usage.total_tokens or 0

            text = response.choices[0].message.content or "ขออภัย ไม่สามารถสร้างคำตอบได้ในขณะนี้"
            logger.info(f"[LLM RECV] {self._provider} response: {len(text)} chars, {tokens} tokens")
            logger.info(f"[LLM RECV] Response text: {text[:150]}")

            return LLMResponse(
                text=text,
                tokens_used=tokens,
                model=self._model,
            )

        except Exception as e:
            logger.error(f"{self._provider} API error: {e}")
            return LLMResponse(
                text="ขออภัย ระบบ AI มีปัญหาชั่วคราว กรุณาลองใหม่ภายหลัง",
                tokens_used=0,
                model=self._model,
            )

    async def generate_hyde_query(self, user_question: str) -> str:
        """Expand a short user query into a hypothetical document for better vector search."""
        prompt = (
            f"ผู้ใช้ถามคำถามสั้นๆ หรือไม่ชัดเจนว่า: '{user_question}'\n\n"
            f"กรุณาเขียนคำตอบสั้นๆ หรือคำอธิบายสมมติ (Hypothetical Document) ประมาณ 2-3 ประโยค "
            f"ที่น่าจะมีอยู่ในคู่มือหรือกฎของร้านเกม ROBLOX เพื่อตอบคำถามนี้\n"
            f"ห้ามเขียนตอบโต้ผู้ใช้ ให้เขียนเฉพาะเนื้อหาคู่มือ/กฎ เท่านั้น"
        )
        logger.info(f"[HyDE SEND] Prompt: {prompt[:100]}...")
        try:
            response = await self._client.chat.completions.create(
                model="google/gemini-2.5-flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300,
            )
            expanded = response.choices[0].message.content.strip()
            logger.info(f"[HyDE RECV] Full expansion: {expanded}")
            return expanded
        except Exception as e:
            logger.warning(f"[HyDE FAIL] {e}")
            return user_question

    async def rerank_context_chunks(self, user_question: str, chunks: list[str], top_n: int = 3) -> list[str]:
        """Cross-Encoder Reranker: Score each chunk 0-10 for relevance and keep top N.
        
        Unlike the old filter that just picks indices, this scores EVERY chunk
        against the question like a "referee" and returns only the best ones.
        """
        if not chunks:
            logger.info("[RERANK] No chunks to rerank.")
            return []
        
        # Cap input to prevent GPT from truncating its scores
        MAX_RERANK = 7
        rerank_chunks = chunks[:MAX_RERANK]
        
        # Build scoring prompt — use FULL content, not truncated previews
        chunks_block = ""
        for i, chunk in enumerate(rerank_chunks):
            chunks_block += f"--- Chunk {i} ---\n{chunk}\n\n"
        
        n = len(rerank_chunks)
        prompt = (
            f"คำถามผู้ใช้: {user_question}\n\n"
            f"ข้อมูลอ้างอิง ({n} chunks):\n{chunks_block}\n"
            f"ให้คะแนนทั้ง {n} Chunks ว่าเกี่ยวข้องกับคำถามมากน้อยเพียงใด (0 = ไม่เกี่ยวเลย, 10 = ตอบตรงคำถาม)\n"
            f"ต้องให้คะแนนครบทุก Chunk ตั้งแต่ 0 ถึง {n-1}\n"
            f"ตอบในรูปแบบ: 0:คะแนน, 1:คะแนน, ... , {n-1}:คะแนน\n"
            f"ตอบแค่คะแนนเท่านั้น ห้ามมีข้อความอื่น"
        )
        logger.info(f"[RERANK SEND] Question='{user_question}', Chunks={n}")
        
        try:
            response = await self._client.chat.completions.create(
                model="google/gemini-2.5-flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            result = response.choices[0].message.content.strip()
            logger.info(f"[RERANK RECV] Scores: '{result}'")
            
            # Parse "0:8, 1:2, 2:9" format
            scores: dict[int, int] = {}
            for pair in result.split(","):
                pair = pair.strip()
                if ":" in pair:
                    parts = pair.split(":")
                    try:
                        idx = int(parts[0].strip())
                        score = int(parts[1].strip())
                        if 0 <= idx < len(rerank_chunks):
                            scores[idx] = score
                    except (ValueError, IndexError):
                        continue
            
            if not scores:
                logger.warning(f"[RERANK] Failed to parse scores. Keeping top {top_n} chunks as-is.")
                return rerank_chunks[:top_n]
            
            # Sort by score descending, keep top N with score > 2
            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            kept = []
            for idx, score in ranked:
                if score >= 2 and len(kept) < top_n:
                    kept.append(rerank_chunks[idx])
                    title = rerank_chunks[idx].split('\n')[0] if '\n' in rerank_chunks[idx] else rerank_chunks[idx][:40]
                    logger.info(f"  [RERANK] ✓ Chunk {idx} (score: {score}/10) → {title}")
            
            if not kept:
                logger.warning("[RERANK] All scores < 2. Keeping best 2 chunks anyway.")
                for idx, score in ranked[:2]:
                    kept.append(rerank_chunks[idx])
                    
            logger.info(f"[RERANK] Final: {len(kept)}/{n} chunks kept.")
            return kept
            
        except Exception as e:
            logger.warning(f"[RERANK FAIL] {e}. Keeping top {top_n} chunks as-is.")
            return rerank_chunks[:top_n]

