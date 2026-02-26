"""Entry point for running the AI Support Bot as a module.

Usage: python -m core.ai_support_bot
"""

import asyncio
import logging
import signal
import sys

from core.ai_support_bot.ai.openrouter import OpenRouterEngine
from core.ai_support_bot.bot.client import SokeberSupportBot
from core.ai_support_bot.bot.commands import AdminCommands
from core.ai_support_bot.cache.memory_cache import MemoryCache
from core.ai_support_bot.config import load_config
from core.ai_support_bot.audit_logging.audit import log_event, setup_audit_logger
from core.ai_support_bot.rag.retriever import ContextRetriever
from core.ai_support_bot.rag.notion_fetcher import NotionFetcher
from core.ai_support_bot.rag.sheets_fetcher import SheetsFetcher
from core.ai_support_bot.rag.ingestion import DataIngestionTask
from core.ai_support_bot.ai.embedding import EmbeddingEngine
from core.ai_support_bot.rag.vector_store import VectorStore

logger = logging.getLogger("ai_support_bot")


def main():
    # Load config
    try:
        config = load_config()
    except OSError as e:
        print(f"[FATAL] Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    # Setup logging
    setup_audit_logger(config.log_level)
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="[%(asctime)s] %(name)s | %(levelname)s | %(message)s",
    )

    log_event("bot_starting", environment=config.environment)

    # Initialize components
    answer_cache = MemoryCache(default_ttl=config.cache_ttl_seconds)

    llm_engine = None
    if config.openrouter_api_key:
        llm_engine = OpenRouterEngine(
            api_key=config.openrouter_api_key,
            model=config.llm_model,
            provider=config.llm_provider,
        )
        logger.info(f"{config.llm_provider} engine initialized: {config.llm_model}")
    else:
        logger.warning("OPENROUTER_API_KEY not set — AI responses disabled")
        # Create a dummy engine that returns a fixed message
        llm_engine = _DummyLLMEngine()

    # Initialize data fetchers
    notion_fetcher = None
    sheets_fetcher = None
    
    if config.notion_token:
        try:
            from notion_client import Client
            notion_client = Client(auth=config.notion_token)
            notion_fetcher = NotionFetcher(notion_client)
            logger.info("Notion fetcher initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Notion: {e}")
    
    if config.google_sa_base64:
        try:
            sheets_fetcher = SheetsFetcher.from_base64_sa(config.google_sa_base64)
            logger.info("Google Sheets fetcher initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Sheets: {e}")
    
    # Initialize Vector components
    embedding_engine = None
    if config.openrouter_api_key:
        embedding_engine = EmbeddingEngine(
            api_key=config.openrouter_api_key,
            model=config.embedding_model
        )
    
    vector_store = VectorStore()

    # Create context retriever
    context_retriever = ContextRetriever(
        embedding_engine=embedding_engine,
        vector_store=vector_store,
        notion_fetcher=notion_fetcher,
        sheets_fetcher=sheets_fetcher,
    )
    logger.info("Context retriever initialized")

    # Create ingestion task
    ingestion_task = DataIngestionTask(
        embedding_engine=embedding_engine,
        vector_store=vector_store,
        notion_fetcher=notion_fetcher,
        sheets_fetcher=sheets_fetcher,
        interval_seconds=config.ingestion_interval_seconds,
        notion_page_ids=config.notion_page_ids,
        notion_database_ids=config.notion_database_ids,
        sheets_spreadsheet_ids=config.sheets_spreadsheet_ids,
    )

    # Create bot
    bot = SokeberSupportBot(
        config=config,
        llm_engine=llm_engine,
        answer_cache=answer_cache,
        context_retriever=context_retriever,
    )
    bot.ingestion_task = ingestion_task
    ingestion_task.context_retriever = context_retriever

    # Register admin commands
    admin_cmds = AdminCommands(bot)
    bot.tree.add_command(admin_cmds)
    
    # Setup hook to start ingestion task when bot is ready
    async def setup_hook():
        await ingestion_task.start()
        logger.info("Ingestion task started")
    
    bot.setup_hook = setup_hook

    # Graceful shutdown
    async def shutdown():
        log_event("bot_shutting_down")
        await ingestion_task.stop()
        await bot.close()

    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        bot.loop.create_task(shutdown())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run
    logger.info("Starting bot...")
    bot.run(config.discord_token, log_handler=None)


class _DummyLLMEngine:
    """Fallback engine when no API key is configured."""

    async def generate(self, question, context_chunks):
        from core.ai_support_bot.ai.openrouter import LLMResponse
        return LLMResponse(
            text="⚠️ AI engine is not configured. Please set OPENROUTER_API_KEY.",
            tokens_used=0,
            model="none",
        )


if __name__ == "__main__":
    main()
