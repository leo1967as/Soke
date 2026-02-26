"""Integration tests for Notion fetcher — uses mocked Notion client."""

from unittest.mock import MagicMock

import pytest

from core.ai_support_bot.rag.notion_fetcher import (
    NotionFetcher,
    _extract_text_from_block,
    _extract_title,
)


class TestExtractTextFromBlock:
    """Test block text extraction helpers."""

    def test_paragraph_block(self):
        block = {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"plain_text": "Hello "},
                    {"plain_text": "world"},
                ]
            },
        }
        assert _extract_text_from_block(block) == "Hello world"

    def test_heading_block(self):
        block = {
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"plain_text": "My Title"}]
            },
        }
        assert _extract_text_from_block(block) == "My Title"

    def test_todo_checked(self):
        block = {
            "type": "to_do",
            "to_do": {
                "checked": True,
                "rich_text": [{"plain_text": "Buy milk"}],
            },
        }
        result = _extract_text_from_block(block)
        assert "✅" in result
        assert "Buy milk" in result

    def test_todo_unchecked(self):
        block = {
            "type": "to_do",
            "to_do": {
                "checked": False,
                "rich_text": [{"plain_text": "Do homework"}],
            },
        }
        result = _extract_text_from_block(block)
        assert "☐" in result

    def test_empty_block(self):
        block = {"type": "divider", "divider": {}}
        assert _extract_text_from_block(block) == ""

    def test_bulleted_list(self):
        block = {
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"plain_text": "Item one"}]
            },
        }
        assert _extract_text_from_block(block) == "Item one"


class TestExtractTitle:
    """Test page title extraction."""

    def test_extracts_title(self):
        page = {
            "properties": {
                "Name": {
                    "type": "title",
                    "title": [{"plain_text": "My Page"}],
                }
            }
        }
        assert _extract_title(page) == "My Page"

    def test_untitled_when_no_title_property(self):
        page = {"properties": {}}
        assert _extract_title(page) == "Untitled"

    def test_multi_part_title(self):
        page = {
            "properties": {
                "Title": {
                    "type": "title",
                    "title": [
                        {"plain_text": "Part "},
                        {"plain_text": "One"},
                    ],
                }
            }
        }
        assert _extract_title(page) == "Part One"


class TestNotionFetcherWithMock:
    """Test NotionFetcher with a mocked Notion client."""

    def _make_mock_client(self, blocks_response, page_response=None):
        """Create a mock Notion client."""
        client = MagicMock()

        if page_response is None:
            page_response = {
                "id": "page-123",
                "url": "https://notion.so/page-123",
                "properties": {
                    "Name": {
                        "type": "title",
                        "title": [{"plain_text": "Test Page"}],
                    }
                },
            }

        client.pages.retrieve.return_value = page_response
        client.blocks.children.list.return_value = blocks_response
        return client

    def test_fetch_page_content(self):
        mock_client = self._make_mock_client({
            "results": [
                {
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"plain_text": "Hello from Notion!"}]
                    },
                },
                {
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"plain_text": "Second paragraph."}]
                    },
                },
            ],
            "has_more": False,
        })

        fetcher = NotionFetcher(mock_client)
        page = fetcher.fetch_page_content("page-123")

        assert page.title == "Test Page"
        assert "Hello from Notion!" in page.content
        assert "Second paragraph." in page.content
        assert page.id == "page-123"

    def test_fetch_empty_page(self):
        mock_client = self._make_mock_client({
            "results": [],
            "has_more": False,
        })

        fetcher = NotionFetcher(mock_client)
        page = fetcher.fetch_page_content("empty-page")
        assert page.content == ""
