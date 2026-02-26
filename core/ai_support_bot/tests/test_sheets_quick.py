"""Quick test to verify Google Sheets connection and access."""

import sys
from pathlib import Path

# Add root directory to python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from core.ai_support_bot.config import load_config
from core.ai_support_bot.rag.sheets_fetcher import SheetsFetcher

print("=" * 60)
print("Google Sheets Connection Test")
print("=" * 60)
print()

try:
    print("[1/2] Loading Configuration and initializing Sheets Fetcher...")
    config = load_config(str(Path(__file__).parent.parent / ".env"))
    if not config.google_sa_base64:
        print("✗ No GOOGLE_SA_BASE64 found in .env")
        sys.exit(1)
        
    fetcher = SheetsFetcher.from_base64_sa(config.google_sa_base64)
    print("✓ Initialized Google Sheets Client")
    
    print()
    print("[2/2] Fetching Spreadsheet IDs...")
    if config.sheets_spreadsheet_ids:
        for sid in config.sheets_spreadsheet_ids:
            print(f"  - Spreadsheet ID: {sid}")
            try:
                service = fetcher._get_service()
                sheet_metadata = service.spreadsheets().get(spreadsheetId=sid).execute()
                sheets = sheet_metadata.get('sheets', '')
                print(f"    ✓ Success - Found {len(sheets)} sheets in spreadsheet.")
                for sheet in sheets[:2]: # grab first 2 sheets to not overwhelm
                    title = sheet.get("properties", {}).get("title", "")
                    print(f"      > Sheet: {title}")
                    rows = fetcher.fetch_sheet_rows(spreadsheet_id=sid, sheet_name=title)
                    print(f"        ✓ Fetched {len(rows)} rows from {title}")
            except Exception as e:
                print(f"    ✗ Failed to access spreadsheet: {e}")
    else:
        print("  - No SPREADSHEET IDs configured.")

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"✗ Failed: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("✓ Test script execution finished!")
print("=" * 60)
print()
