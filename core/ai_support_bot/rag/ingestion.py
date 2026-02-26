"""Background task for ingesting data from Notion and Google Sheets."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.ai_support_bot.rag.notion_fetcher import NotionFetcher
    from core.ai_support_bot.rag.sheets_fetcher import SheetsFetcher
    from core.ai_support_bot.ai.embedding import EmbeddingEngine
    from core.ai_support_bot.rag.vector_store import VectorStore

logger = logging.getLogger("ai_support_bot.rag.ingestion")

# Sheets that are useful for customer support knowledge
# Everything else (Change Log, Settings, Helper, Dropdown) is noise
SHEETS_WHITELIST = [
    "📊 Dashboard",
    "รับออเดอร์ (V5)",
]

MIN_CONTENT_LENGTH = 10  # Skip documents shorter than this


class DataIngestionTask:
    """Background task that periodically fetches data from sources."""

    def __init__(
        self,
        embedding_engine: 'EmbeddingEngine' | None = None,
        vector_store: 'VectorStore' | None = None,
        notion_fetcher: 'NotionFetcher' | None = None,
        sheets_fetcher: 'SheetsFetcher' | None = None,
        interval_seconds: int = 3600,
        notion_page_ids: list[str] | None = None,
        notion_database_ids: list[str] | None = None,
        sheets_spreadsheet_ids: list[str] | None = None,
    ):
        """Initialize ingestion task.
        
        Args:
            notion_fetcher: Notion data fetcher
            sheets_fetcher: Google Sheets data fetcher
            interval_seconds: How often to refresh data (default: 1 hour)
            notion_page_ids: List of specific Notion page IDs to fetch
            notion_database_ids: List of Notion database IDs to fetch
            sheets_spreadsheet_ids: List of Google Sheets IDs to fetch
        """
        self.embedding_engine = embedding_engine
        self.vector_store = vector_store
        self.notion_fetcher = notion_fetcher
        self.sheets_fetcher = sheets_fetcher
        self.interval_seconds = interval_seconds
        self.notion_page_ids = notion_page_ids or []
        self.notion_database_ids = notion_database_ids or []
        self.sheets_spreadsheet_ids = sheets_spreadsheet_ids or []
        self._task = None
        self._running = False

    async def start(self):
        """Start the background ingestion task."""
        if self._running:
            logger.warning("Ingestion task already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info(f"Started data ingestion task (interval: {self.interval_seconds}s)")

    async def stop(self):
        """Stop the background ingestion task."""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped data ingestion task")

    async def _run(self):
        """Main ingestion loop."""
        # Give Discord time to establish connection
        await asyncio.sleep(5.0)
        
        # Run initial ingestion on start
        await self._ingest_all()
        
        # Then run periodically (but at a slower pace)
        while self._running:
            try:
                await asyncio.sleep(self.interval_seconds)
                await self._ingest_all()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in ingestion loop: {e}", exc_info=True)

    # ─── Core fetch helpers ───────────────────────────────────────────

    async def _fetch_notion_docs(self) -> tuple[list[str], list[dict]]:
        """Fetch all Notion pages and return (texts, metadatas)."""
        texts, metas = [], []
        if not self.notion_fetcher:
            return texts, metas

        self.notion_fetcher._cached_pages = []
        try:
            await asyncio.to_thread(self.notion_fetcher.fetch_all)
            for page in self.notion_fetcher._cached_pages:
                doc = f"[{page.title}]\n{page.content}"
                if len(page.content.strip()) < MIN_CONTENT_LENGTH:
                    continue  # Skip empty / near-empty pages
                texts.append(doc)
                metas.append({"source": "notion", "title": page.title, "id": page.id})
            logger.info(f"Fetched {len(texts)} useful Notion pages (skipped {len(self.notion_fetcher._cached_pages) - len(texts)} empty)")
        except Exception as e:
            logger.error(f"Failed to fetch Notion pages: {e}")
        return texts, metas

    async def _fetch_sheets_docs(self) -> tuple[list[str], list[dict]]:
        """Fetch whitelisted Google Sheets and return (texts, metadatas)."""
        texts, metas = [], []
        if not self.sheets_fetcher:
            return texts, metas

        for sheet_id in self.sheets_spreadsheet_ids:
            try:
                sheet_names = await asyncio.to_thread(self.sheets_fetcher.get_sheet_names, sheet_id)
                for name in sheet_names:
                    # Only index whitelisted sheets
                    if SHEETS_WHITELIST and name not in SHEETS_WHITELIST:
                        logger.debug(f"Skipping non-whitelisted sheet: {name}")
                        continue
                    rows = await asyncio.to_thread(self.sheets_fetcher.fetch_sheet_rows, sheet_id, name)
                    for row in rows:
                        if len(row.content.strip()) < MIN_CONTENT_LENGTH:
                            continue
                        texts.append(f"[{row.title}]\n{row.content}")
                        metas.append({"source": "sheets", "title": row.title})
                    logger.info(f"Fetched {len(rows)} rows from Sheets (Sheet: {name})")
            except Exception as e:
                logger.error(f"Failed to fetch Sheets {sheet_id}: {e}")
        return texts, metas

    async def _rebuild_index(self, texts: list[str], metadatas: list[dict]):
        """Embed texts and rebuild the ChromaDB vector index."""
        if not texts:
            logger.warning("No documents to index.")
            return
        if not self.embedding_engine or not self.vector_store:
            logger.warning("Embedding engine or vector store not available.")
            return

        try:
            await asyncio.to_thread(self.vector_store.reset_collection)

            batch_size = 50
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_metas = metadatas[i:i + batch_size]
                if not batch_texts:
                    continue

                embeddings = await self.embedding_engine.embed(batch_texts)
                await asyncio.to_thread(
                    self.vector_store.add_documents,
                    batch_texts,
                    embeddings,
                    batch_metas
                )
                await asyncio.sleep(0.01)
            logger.info(f"✅ Rebuilt vector index with {len(texts)} documents.")
        except Exception as e:
            logger.error(f"Failed to rebuild vector index: {e}")

    # ─── Public sync methods ──────────────────────────────────────────

    async def _ingest_all(self):
        """Full sync: fetch Notion + Sheets, rebuild index."""
        logger.info("Starting FULL data ingestion...")
        notion_texts, notion_metas = await self._fetch_notion_docs()
        sheets_texts, sheets_metas = await self._fetch_sheets_docs()

        all_texts = notion_texts + sheets_texts
        all_metas = notion_metas + sheets_metas

        await self._rebuild_index(all_texts, all_metas)
        logger.info("Full ingestion complete.")

    async def ingest_notion_only(self):
        """Sync only Notion pages."""
        logger.info("Starting NOTION-ONLY ingestion...")
        notion_texts, notion_metas = await self._fetch_notion_docs()
        # We still need sheets data already in the store, so fetch both
        sheets_texts, sheets_metas = await self._fetch_sheets_docs()
        all_texts = notion_texts + sheets_texts
        all_metas = notion_metas + sheets_metas
        await self._rebuild_index(all_texts, all_metas)
        logger.info("Notion-only ingestion complete.")

    async def ingest_sheets_only(self):
        """Sync only Google Sheets."""
        logger.info("Starting SHEETS-ONLY ingestion...")
        notion_texts, notion_metas = await self._fetch_notion_docs()
        sheets_texts, sheets_metas = await self._fetch_sheets_docs()
        all_texts = notion_texts + sheets_texts
        all_metas = notion_metas + sheets_metas
        await self._rebuild_index(all_texts, all_metas)
        logger.info("Sheets-only ingestion complete.")

    async def ingest_now(self):
        """Trigger immediate full ingestion (for manual refresh)."""
        logger.info("Manual full ingestion triggered")
        await self._ingest_all()
