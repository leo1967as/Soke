"""Google Sheets data fetcher — retrieves rows and converts to searchable text."""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("ai_support_bot.rag.sheets")


@dataclass
class SheetRow:
    """Represents a single row as a searchable text document."""
    id: str
    text: str
    sheet_name: str
    row_number: int

    @property
    def title(self) -> str:
        """Return sheet name as title for compatibility with retriever."""
        return f"{self.sheet_name} - Row {self.row_number}"
    
    @property
    def content(self) -> str:
        """Return text as content for compatibility with retriever."""
        return self.text

    def to_text(self) -> str:
        return self.text


class SheetsFetcher:
    """Fetches data from Google Sheets and converts rows to plain text.

    Args:
        credentials: google.oauth2 Credentials object.
        spreadsheet_id: The ID of the target spreadsheet.
    """

    def __init__(self, credentials):
        self._credentials = credentials
        self._service = None
        self._cached_rows = []

    @classmethod
    def from_base64_sa(cls, base64_sa: str):
        """Create fetcher from base64-encoded service account JSON.
        
        Args:
            base64_sa: Base64-encoded service account JSON string.
            
        Returns:
            SheetsFetcher instance.
        """
        import base64
        import json
        from google.oauth2 import service_account
        
        # Decode base64
        sa_json = base64.b64decode(base64_sa).decode('utf-8')
        sa_dict = json.loads(sa_json)
        
        # Create credentials
        credentials = service_account.Credentials.from_service_account_info(
            sa_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
        
        return cls(credentials)

    def _get_service(self):
        """Lazy-initialize the Sheets API service."""
        if self._service is None:
            from googleapiclient.discovery import build
            self._service = build("sheets", "v4", credentials=self._credentials)
        return self._service

    def get_sheet_names(self, spreadsheet_id: str) -> list[str]:
        """Fetch all sheet (tab) names from a spreadsheet."""
        service = self._get_service()
        try:
            spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheets = spreadsheet.get("sheets", [])
            return [s.get("properties", {}).get("title", "Sheet1") for s in sheets]
        except Exception as e:
            logger.error(f"Failed to list sheets for {spreadsheet_id}: {e}")
            return []

    def fetch_sheet_rows(self, spreadsheet_id: str, sheet_name: str, range_notation: str = "") -> list[SheetRow]:
        """Fetch all rows from a sheet and convert to SheetRow objects.

        Args:
            spreadsheet_id: The spreadsheet ID to fetch from.
            sheet_name: Name of the sheet tab.
            range_notation: Optional A1 range (e.g. "A1:Z100"). If empty, fetches all.

        Returns:
            List of SheetRow objects.
        """
        service = self._get_service()
        full_range = f"{sheet_name}!{range_notation}" if range_notation else sheet_name

        try:
            result = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=full_range)
                .execute()
            )
        except Exception as e:
            logger.error(f"Failed to fetch sheet '{sheet_name}': {e}")
            return []

        values = result.get("values", [])
        if not values:
            return []

        # First row = headers
        headers = values[0]
        rows: list[SheetRow] = []

        for i, row_data in enumerate(values[1:], start=2):
            # Pad row to match headers length
            padded = row_data + [""] * (len(headers) - len(row_data))
            # Convert to "header: value" pairs
            pairs = [f"{h}: {v}" for h, v in zip(headers, padded, strict=False) if v]
            text = " | ".join(pairs)

            if text.strip():
                rows.append(
                    SheetRow(
                        id=f"sheets_{sheet_name}_row{i}",
                        text=text,
                        sheet_name=sheet_name,
                        row_number=i,
                    )
                )

        logger.info(f"Fetched {len(rows)} rows from sheet '{sheet_name}'")
        
        # Cache the rows
        self._cached_rows.extend(rows)
        
        return rows

    def fetch_all_rows(self, sheet_names: list[str]) -> list[SheetRow]:
        """Fetch rows from multiple sheets."""
        all_rows: list[SheetRow] = []
        for name in sheet_names:
            all_rows.extend(self.fetch_sheet(name))
        return all_rows
