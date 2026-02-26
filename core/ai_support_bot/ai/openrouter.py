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
        model: Model identifier (e.g., "openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet").
        provider: Provider name for logging (default: "openrouter").
        base_url: Optional custom base URL (default: OpenRouter).
    """

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-4o-mini",
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
            logger.info(f"{self._provider} response: {len(text)} chars, {tokens} tokens")

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
        try:
            response = await self._client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300,
            )
            expanded = response.choices[0].message.content.strip()
            logger.info(f"HyDE expansion for '{user_question[:20]}': {expanded[:50]}...")
            return expanded
        except Exception as e:
            logger.warning(f"HyDE expansion failed: {e}")
            return user_question

    async def filter_context_chunks(self, user_question: str, chunks: list[str]) -> list[str]:
        """Filter chunks using LLM to ensure they are at least somewhat relevant to the user's question."""
        if not chunks:
            return []
            
        chunks_text = ""
        for i, chunk in enumerate(chunks):
            chunks_text += f"--- Chunk {i} ---\n{chunk}\n\n"
            
        prompt = (
            f"คำถามผู้ใช้: {user_question}\n\n"
            f"ข้อมูลอ้างอิง:\n{chunks_text}\n"
            f"จงบอกว่า Chunk ไหนที่มีแนวโน้ม 'เกี่ยวข้อง' หรือ 'มีเบาะแส' ที่จะนำไปใช้ตอบคำถามผู้ใช้ได้ (แม้เพียงบางส่วนก็ให้ถือว่าเกี่ยว) "
            f"ตอบเป็นตัวเลข Index คั่นด้วยลูกน้ำ (เช่น 0, 2, 3) หากมั่นใจว่าไม่มี Chunk ไหนเกี่ยวเลยจริงๆ ให้ตอบคำว่า NONE "
            f"ตอบแค่ตัวเลขหรือ NONE เท่านั้น ห้ามมีข้อความอื่น"
        )
        
        try:
            response = await self._client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            result = response.choices[0].message.content.strip()
            
            # If the LLM says NONE or we can't parse it, fallback to the top 2 chunks 
            # instead of returning [] to avoid the bot completely blanking out.
            if result.upper() == "NONE":
                logger.warning("Context filter said NONE. Falling back to top 2 chunks just in case.")
                return chunks[:2]
                
            indices = [int(x.strip()) for x in result.split(",") if x.strip().isdigit()]
            if not indices:
                 return chunks[:2]
                 
            filtered = [chunks[i] for i in indices if 0 <= i < len(chunks)]
            logger.info(f"Context filter: kept {len(filtered)}/{len(chunks)} chunks.")
            return filtered
        except Exception as e:
            logger.warning(f"Context filter failed: {e}. Falling back to all chunks.")
            return chunks
