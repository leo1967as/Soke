"""Notion page fetcher — retrieves and parses pages into plain text."""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("ai_support_bot.rag.notion")


@dataclass
class NotionPage:
    """Represents a parsed Notion page."""
    id: str
    title: str
    content: str
    url: str = ""
    last_edited_time: str = ""


def _extract_rich_text(rich_text_list: list[dict]) -> str:
    """Helper to extract plain text from rich_text array."""
    if not rich_text_list:
        return ""
    return "".join(rt.get("plain_text", "") for rt in rich_text_list)


def _extract_title(page: dict) -> str:
    """Extract title from a Notion page properties."""
    properties = page.get("properties", {})
    for prop in properties.values():
        if prop.get("type") == "title":
            title_arr = prop.get("title", [])
            return _extract_rich_text(title_arr)
    return "Untitled"


class NotionFetcher:
    """Fetches pages from Notion and converts to plain text."""

    def __init__(self, client):
        """Initialize with a Notion client."""
        self._client = client
        self._cached_pages = []

    def _get_block_text(self, block: dict, depth: int = 0) -> str:
        """Extract plain text from a block and its children recursively."""
        block_type = block.get("type", "")
        block_data = block.get(block_type, {})
        indent = "  " * depth
        lines = []

        # 1. Extract text from current block
        text = ""
        if block_type == "to_do":
            checked = "✅" if block_data.get("checked") else "☐"
            text = f"{checked} {_extract_rich_text(block_data.get('rich_text', []))}"
        elif block_type == "callout":
            emoji = block_data.get("icon", {}).get("emoji", "💡")
            text = f"{emoji} {_extract_rich_text(block_data.get('rich_text', []))}"
        elif block_type == "quote":
            text = f"> {_extract_rich_text(block_data.get('rich_text', []))}"
        elif block_type == "toggle":
            text = f"▼ {_extract_rich_text(block_data.get('rich_text', []))}"
        elif block_type == "table_row":
            # table_row has 'cells' (list of rich_text arrays)
            cells = [_extract_rich_text(cell) for cell in block_data.get("cells", [])]
            text = " | ".join(cells)
        elif "rich_text" in block_data:
            text = _extract_rich_text(block_data.get("rich_text", []))
        
        if text.strip():
            lines.append(f"{indent}{text}")

        # 2. Extract children if any (recursion)
        if block.get("has_children"):
            # Exclude child_page/child_database from recursion inside page content
            # (they are handled by the tree crawler separately)
            if block_type not in ["child_page", "child_database"]:
                children = self._fetch_all_blocks(block["id"])
                for child in children:
                    child_text = self._get_block_text(child, depth + 1)
                    if child_text.strip():
                        lines.append(child_text)

        return "\n".join(lines)

    def fetch_page_content(self, page_id: str) -> NotionPage:
        """Fetch a single page and all its block children as plain text."""
        page = self._client.pages.retrieve(page_id=page_id)
        title = _extract_title(page)
        url = page.get("url", "")

        blocks = self._fetch_all_blocks(page_id)
        content_parts = []
        for block in blocks:
            text = self._get_block_text(block)
            if text.strip():
                content_parts.append(text)

        content = "\n".join(content_parts)
        logger.info(f"Fetched Notion page '{title}' ({len(content)} chars)")
        return NotionPage(id=page_id, title=title, content=content, url=url)

    def _fetch_all_blocks(self, block_id: str) -> list[dict]:
        """Paginate through all children of a block."""
        all_blocks: list[dict] = []
        cursor = None

        while True:
            kwargs = {"block_id": block_id, "page_size": 100}
            if cursor:
                kwargs["start_cursor"] = cursor

            response = self._client.blocks.children.list(**kwargs)
            all_blocks.extend(response.get("results", []))

            if not response.get("has_more"):
                break
            cursor = response.get("next_cursor")

        return all_blocks

    def fetch_database_pages(self, database_id: str) -> list[NotionPage]:
        """Fetch all pages from a Notion database."""
        pages: list[NotionPage] = []
        cursor = None

        while True:
            # Build request params
            params = {"page_size": 100}
            if cursor:
                params["start_cursor"] = cursor

            try:
                # Use the official python SDK method for querying databases if available
                if hasattr(self._client, "databases") and hasattr(self._client.databases, "query"):
                    response = self._client.databases.query(
                        database_id=database_id,
                        **params
                    )
                else:
                    res = self._client.client.post(
                        f"databases/{database_id}/query",
                        json=params,
                        headers={"Notion-Version": "2022-06-28"}
                    )
                    res.raise_for_status()
                    response = res.json()
            except Exception as e:
                logger.error(f"Failed to query database {database_id}: {e}")
                break

            for result in response.get("results", []):
                page_id = result["id"]
                try:
                    page = self.fetch_page_content(page_id)
                    pages.append(page)
                except Exception as e:
                    logger.error(f"Failed to fetch page {page_id}: {e}")

            if not response.get("has_more"):
                break
            cursor = response.get("next_cursor")

        logger.info(f"Fetched {len(pages)} pages from database {database_id}")
        
        # Cache the pages
        for page in pages:
            if not any(p.id == page.id for p in self._cached_pages):
                self._cached_pages.append(page)
        
        return pages

    def fetch_tree(self, start_page_ids: list[str], start_database_ids: list[str]):
        """Recursively fetch pages and databases, caching all discovered content."""
        visited_pages = set()
        visited_databases = set()
        
        pages_to_visit = list(start_page_ids)
        databases_to_visit = list(start_database_ids)

        while pages_to_visit or databases_to_visit:
            # Process all pending databases first, which yield more pages
            while databases_to_visit:
                db_id = databases_to_visit.pop(0)
                # Normalize ID (remove hyphens to ensure consistent tracking)
                norm_db_id = db_id.replace('-', '')
                if norm_db_id in visited_databases:
                    continue
                visited_databases.add(norm_db_id)
                
                try:
                    logger.info(f"Fetching database tree node: {db_id}")
                    # fetch_database_pages calls fetch_page_content for its entries
                    pages = self.fetch_database_pages(db_id)
                    # Add newly discovered child pages to our crawl queue
                    for p in pages:
                        norm_pid = p.id.replace('-', '')
                        if norm_pid not in visited_pages:
                            pages_to_visit.append(p.id)
                except Exception as e:
                    logger.error(f"Error fetching database tree node {db_id}: {e}")

            # Process pending pages
            while pages_to_visit:
                page_id = pages_to_visit.pop(0)
                norm_page_id = page_id.replace('-', '')
                if norm_page_id in visited_pages:
                    continue
                visited_pages.add(norm_page_id)
                
                try:
                    logger.info(f"Fetching page tree node: {page_id}")
                    # 1. Fetch the page itself
                    page = self.fetch_page_content(page_id)
                    
                    # Ensure it's in the cache
                    if not any(p.id == page.id for p in self._cached_pages):
                        self._cached_pages.append(page)

                    # 2. Inspect its blocks for children
                    blocks = self._fetch_all_blocks(page_id)
                    for block in blocks:
                        b_type = block.get("type", "")
                        b_id = block.get("id", "")
                        
                        if b_type == "child_page":
                            pages_to_visit.append(b_id)
                        elif b_type == "child_database":
                            databases_to_visit.append(b_id)
                        elif b_type == "link_to_page":
                            link_data = block.get("link_to_page", {})
                            if link_data.get("type") == "page_id":
                                pages_to_visit.append(link_data.get("page_id"))
                            elif link_data.get("type") == "database_id":
                                databases_to_visit.append(link_data.get("database_id"))

                except Exception as e:
                    logger.error(f"Error fetching page tree node {page_id}: {e}")

    def fetch_all(self):
        """Fetch all pages and databases accessible to the integration using search."""
        logger.info("Searching workspace for all accessible Notion pages and databases...")
        cursor = None
        all_results = []
        
        while True:
            kwargs = {}
            if cursor:
                kwargs["start_cursor"] = cursor
            try:
                response = self._client.search(**kwargs)
                all_results.extend(response.get("results", []))
                if not response.get("has_more"):
                    break
                cursor = response.get("next_cursor")
            except Exception as e:
                logger.error(f"Failed to search workspace: {e}")
                break

        pages_to_visit = []
        databases_to_visit = []

        for result in all_results:
            obj_type = result.get("object")
            obj_id = result.get("id")
            if obj_type == "page":
                pages_to_visit.append(obj_id)
            elif obj_type == "database":
                databases_to_visit.append(obj_id)

        logger.info(f"Search found {len(pages_to_visit)} pages and {len(databases_to_visit)} databases. Fetching contents...")
        
        # Reuse fetch_tree but pass all discovered pages & databases as seeds.
        self.fetch_tree(pages_to_visit, databases_to_visit)
