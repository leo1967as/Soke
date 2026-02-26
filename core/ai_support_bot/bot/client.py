"""Discord bot client — main event loop and message handling."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from core.ai_support_bot.cache.memory_cache import MemoryCache
from core.ai_support_bot.audit_logging.audit import log_event, log_interaction
from core.ai_support_bot.security.rate_limiter import RateLimiter
from core.ai_support_bot.security.sanitizer import sanitize_user_input

if TYPE_CHECKING:
    from core.ai_support_bot.ai.openrouter import OpenRouterEngine
    from core.ai_support_bot.config import BotConfig

logger = logging.getLogger("ai_support_bot.bot")

RATE_LIMIT_MSG = "⏳ คุณส่งข้อความเร็วเกินไป กรุณารอสักครู่แล้วลองใหม่"
REJECTED_MSG = "⚠️ ข้อความของคุณไม่สามารถประมวลผลได้ กรุณาลองถามใหม่"
MAX_DISCORD_LENGTH = 2000


class SokeberSupportBot(commands.Bot):
    """AI-powered customer support Discord bot.

    Listens to designated channels, retrieves context, generates AI responses.
    """

    def __init__(
        self,
        config: BotConfig,
        llm_engine: OpenRouterEngine,
        answer_cache: MemoryCache,
        context_retriever=None,
        **kwargs,
    ):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(
            command_prefix="!",  # Not used, but required for commands.Bot
            intents=intents,
            **kwargs
        )

        self.config = config
        self.llm = llm_engine
        self.answer_cache = answer_cache
        self.context_retriever = context_retriever
        self.rate_limiter = RateLimiter(
            max_calls=config.rate_limit_max_calls,
            window_seconds=config.rate_limit_window_seconds,
        )
        self.conversation_history = {}

    async def on_ready(self):
        logger.info(f"Bot logged in as {self.user} (ID: {self.user.id})")
        log_event("bot_ready", user=str(self.user), guilds=len(self.guilds))

    async def on_message(self, message: discord.Message):
        # Ignore own messages and other bots
        if message.author.bot:
            return

        # Channel filter
        if self.config.allowed_channel_ids and message.channel.id not in self.config.allowed_channel_ids:
            return

        user_id = message.author.id

        # Admin Bypass logic
        is_admin = False
        if getattr(message.author, "guild_permissions", None) and message.author.guild_permissions.administrator:
            is_admin = True

        # Manual Sync/Refresh Command  (!sync, !sync notion, !sync sheets)
        msg_lower = message.content.strip().lower()
        if msg_lower.startswith("!sync") or msg_lower.startswith("!refresh"):
            if is_admin:
                parts = msg_lower.split()
                sync_target = parts[1] if len(parts) > 1 else "all"

                if not hasattr(self, 'ingestion_task'):
                    await message.reply("❌ ไม่พบ Ingestion Task!", mention_author=False)
                    return

                if sync_target in ("notion", "database", "db"):
                    await message.reply("⏳ กำลังดึงข้อมูลจาก Notion ใหม่...", mention_author=False)
                    try:
                        await self.ingestion_task.ingest_notion_only()
                        await message.reply("✅ อัพเดต Notion สมบูรณ์แล้ว!", mention_author=False)
                    except Exception as e:
                        await message.reply(f"❌ Error: {e}", mention_author=False)

                elif sync_target == "sheets":
                    await message.reply("⏳ กำลังดึงข้อมูลจาก Google Sheets ใหม่...", mention_author=False)
                    try:
                        await self.ingestion_task.ingest_sheets_only()
                        await message.reply("✅ อัพเดต Sheets สมบูรณ์แล้ว!", mention_author=False)
                    except Exception as e:
                        await message.reply(f"❌ Error: {e}", mention_author=False)

                else:  # "all" or just "!sync"
                    await message.reply("⏳ กำลังดึงข้อมูลทั้งหมดใหม่ (Notion + Sheets)...", mention_author=False)
                    try:
                        await self.ingestion_task.ingest_now()
                        await message.reply("✅ อัพเดตข้อมูลทั้งหมดสมบูรณ์แล้ว!", mention_author=False)
                    except Exception as e:
                        await message.reply(f"❌ Error: {e}", mention_author=False)
            else:
                await message.reply("หึ แกไม่มีสิทธิ์มาสั่งผมหรอกนะ", mention_author=False)
            return
            
        # Rate limiting
        if not is_admin and not self.rate_limiter.is_allowed(user_id):
            wait_time = int(self.rate_limiter.time_until_reset(user_id) / 60) + 1
            cooldown_msg = f"⏳ โควต้าคำถามของนายหมดแล้ว (20 ครั้ง/ชม.) รออีกประมาณ {wait_time} นาทีแล้วค่อยมาถามผมใหม่"
            await message.reply(cooldown_msg, mention_author=False)
            return

        # Input sanitization
        cleaned = sanitize_user_input(message.content)
        if cleaned is None:
            await message.reply(REJECTED_MSG, mention_author=False)
            return

        # Manage Memory
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        history = self.conversation_history[user_id]

        # Process the message
        start_time = time.monotonic()
        async with message.channel.typing():
            response_text, cache_hit, tokens_used = await self._generate_response(cleaned, history)

        latency_ms = int((time.monotonic() - start_time) * 1000)

        # Update Memory
        self.conversation_history[user_id].append({"role": "user", "content": cleaned})
        self.conversation_history[user_id].append({"role": "assistant", "content": response_text})
        if len(self.conversation_history[user_id]) > 10:
            self.conversation_history[user_id] = self.conversation_history[user_id][-10:]

        # Send response (handle Discord's 2000 char limit)
        await self._send_response(message, response_text)

        # Audit log
        log_interaction(
            user_id=message.author.id,
            channel_id=message.channel.id,
            input_length=len(cleaned),
            response_length=len(response_text),
            cache_hit=cache_hit,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )

    async def _generate_response(self, question: str, history: list[dict] | None = None) -> tuple[str, bool, int]:
        """Generate a response, checking cache first.

        Returns:
            (response_text, cache_hit, tokens_used)
        """
        # Check answer cache
        cached = self.answer_cache.get(question)
        if cached is not None:
            logger.debug("Cache HIT")
            return cached, True, 0

        # Retrieve context chunks
        context_chunks = []
        if self.context_retriever:
            try:
                # 1. Expand query (HyDE)
                expanded_query = await self.llm.generate_hyde_query(question)
                
                # 2. Retrieve using expanded query (fetch more chunks initially)
                raw_chunks = await self.context_retriever.retrieve(expanded_query, top_k=10)
                
                # 3. Filter/Re-rank retrieved chunks based on original question
                context_chunks = await self.llm.filter_context_chunks(question, raw_chunks)
            except Exception as e:
                logger.error(f"Context retrieval/filtering failed: {e}")

        # Generate via LLM
        result = await self.llm.generate(question, context_chunks, history)

        # Cache the answer
        self.answer_cache.set(question, result.text, ttl=self.config.cache_ttl_seconds)

        return result.text, False, result.tokens_used

    async def _send_response(self, message: discord.Message, text: str) -> None:
        """Send response, splitting if it exceeds Discord's limit."""
        if len(text) <= MAX_DISCORD_LENGTH:
            await message.reply(text, mention_author=False)
            return

        # Split into chunks at word boundaries
        parts = []
        while text:
            if len(text) <= MAX_DISCORD_LENGTH:
                parts.append(text)
                break
            split_at = text.rfind(" ", 0, MAX_DISCORD_LENGTH)
            if split_at == -1:
                split_at = MAX_DISCORD_LENGTH
            parts.append(text[:split_at])
            text = text[split_at:].lstrip()

        for part in parts:
            await message.reply(part, mention_author=False)
            await asyncio.sleep(0.5)
