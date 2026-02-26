"""Integration tests for Google Sheets fetcher — uses mocked Sheets API."""

from unittest.mock import MagicMock, patch

import pytest

from core.ai_support_bot.rag.sheets_fetcher import SheetsFetcher, SheetRow


class TestSheetsFetcherWithMock:
    """Test SheetsFetcher with a mocked Google Sheets API."""

    def _make_fetcher_with_mock_data(self, values: list[list[str]]):
        """Create a SheetsFetcher with mocked API response."""
        fetcher = SheetsFetcher(credentials=MagicMock(), spreadsheet_id="test-sheet-id")

        mock_service = MagicMock()
        mock_values = MagicMock()
        mock_get = MagicMock()

        mock_get.execute.return_value = {"values": values}
        mock_values.get.return_value = mock_get
        mock_service.spreadsheets.return_value.values.return_value = mock_values

        fetcher._service = mock_service
        return fetcher

    def test_fetch_sheet_with_data(self):
        values = [
            ["Name", "Price", "Plan"],
            ["Basic", "$10", "Monthly"],
            ["Pro", "$30", "Monthly"],
            ["Enterprise", "Custom", "Annual"],
        ]
        fetcher = self._make_fetcher_with_mock_data(values)
        rows = fetcher.fetch_sheet("Plans")

        assert len(rows) == 3
        assert all(isinstance(r, SheetRow) for r in rows)
        assert "Name: Basic" in rows[0].text
        assert "Price: $10" in rows[0].text
        assert rows[0].row_number == 2
        assert rows[0].sheet_name == "Plans"

    def test_fetch_empty_sheet(self):
        fetcher = self._make_fetcher_with_mock_data([])
        rows = fetcher.fetch_sheet("Empty")
        assert rows == []

    def test_fetch_header_only(self):
        values = [["Name", "Price"]]
        fetcher = self._make_fetcher_with_mock_data(values)
        rows = fetcher.fetch_sheet("HeaderOnly")
        assert rows == []

    def test_row_with_missing_columns(self):
        """Row shorter than headers should be padded."""
        values = [
            ["Name", "Price", "Plan"],
            ["Basic"],  # Missing Price and Plan
        ]
        fetcher = self._make_fetcher_with_mock_data(values)
        rows = fetcher.fetch_sheet("Sparse")

        assert len(rows) == 1
        assert "Name: Basic" in rows[0].text
        # Empty columns should be excluded from text
        assert "Price:" not in rows[0].text

    def test_row_ids_unique(self):
        values = [
            ["Name"],
            ["A"],
            ["B"],
            ["C"],
        ]
        fetcher = self._make_fetcher_with_mock_data(values)
        rows = fetcher.fetch_sheet("Sheet1")
        ids = [r.id for r in rows]
        assert len(ids) == len(set(ids))

    def test_fetch_all_rows_multiple_sheets(self):
        fetcher = self._make_fetcher_with_mock_data([
            ["Col1"],
            ["Val1"],
            ["Val2"],
        ])
        rows = fetcher.fetch_all_rows(["Sheet1", "Sheet2"])
        # Each sheet call returns 2 rows, 2 sheets = 4 total
        assert len(rows) == 4
