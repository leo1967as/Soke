import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SPREADSHEET_ID = '166jyYS0YPGVzHtV6CEfLILtmgjEX1McNK4BgxXkeyPg'
# IDs for specific sheets
ORDER_SHEET_ID = 1344923037
HELPER_SHEET_ID = 2089411906

# Paths to the service account credentials relative to this script
CREDENTIALS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'Resource', 'project-manager-88467-50206ef33cb0.json'
)

def update_data_validation():
    # Attempt to authenticate
    creds = Credentials.from_service_account_file(
        CREDENTIALS_PATH, scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    service = build('sheets', 'v4', credentials=creds)

    print("Building bulk request for 1000 rows...")
    requests = []
    
    # 0. Append 1000 rows to Helper_V5 so it can support validation up to row 2000
    requests.append({
        "appendDimension": {
            "sheetId": HELPER_SHEET_ID,
            "dimension": "ROWS",
            "length": 1050
        }
    })

    # 1. Expand Helper_V5 formulas to 1000 rows
    # Rows 2 to 1001 (index 1 to 1000) for Job Categories
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": HELPER_SHEET_ID,
                "startRowIndex": 1,
                "endRowIndex": 1001,
                "startColumnIndex": 0,
                "endColumnIndex": 1
            },
            "cell": {
                "userEnteredValue": {
                    "formulaValue": "=IFERROR(TRANSPOSE(UNIQUE(FILTER(Settings_V5!$B$2:$B$100,Settings_V5!$A$2:$A$100='รับออเดอร์ (V5)'!$E2))),\"\")"
                }
            },
            "fields": "userEnteredValue"
        }
    })

    # Rows 1002 to 2001 (index 1001 to 2000) for Packages
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": HELPER_SHEET_ID,
                "startRowIndex": 1001,
                "endRowIndex": 2001,
                "startColumnIndex": 0,
                "endColumnIndex": 1
            },
            "cell": {
                "userEnteredValue": {
                    "formulaValue": "=IFERROR(TRANSPOSE(UNIQUE(FILTER(Settings_V5!$C$2:$C$100,(Settings_V5!$A$2:$A$100='รับออเดอร์ (V5)'!E2)*(Settings_V5!$B$2:$B$100='รับออเดอร์ (V5)'!F2)))),\"\")"
                }
            },
            "fields": "userEnteredValue"
        }
    })

    # 2. Add validations for 1000 rows in order sheet (Rows 2 to 1001 => index 1 to 1000)
    # With 'คนทำ' inserted at C and 'สถานะ' at D... Game is E (index 4). Job is F (index 5). Package is G (index 6)
    
    print("Generating validation rules...")
    for r in range(1, 1001):  # r is row index in Order Sheet (1 to 1000)
        # Job Validation (Column F, index 5). Links to Helper row r+1
        requests.append({
            "setDataValidation": {
                "range": {
                    "sheetId": ORDER_SHEET_ID,
                    "startRowIndex": r,
                    "endRowIndex": r + 1,
                    "startColumnIndex": 5, # Column F
                    "endColumnIndex": 6
                },
                "rule": {
                    "condition": {
                        "type": "ONE_OF_RANGE",
                        "values": [{"userEnteredValue": f"=Helper_V5!$A${r+1}:$Z${r+1}"}]
                    },
                    "showCustomUi": True,
                    "strict": True
                }
            }
        })

        # Package Validation (Column G, index 6). Links to Helper row r + 1001
        requests.append({
            "setDataValidation": {
                "range": {
                    "sheetId": ORDER_SHEET_ID,
                    "startRowIndex": r,
                    "endRowIndex": r + 1,
                    "startColumnIndex": 6, # Column G
                    "endColumnIndex": 7
                },
                "rule": {
                    "condition": {
                        "type": "ONE_OF_RANGE",
                        "values": [{"userEnteredValue": f"=Helper_V5!$A${r+1001}:$Z${r+1001}"}]
                    },
                    "showCustomUi": True,
                    "strict": True
                }
            }
        })

    print(f"Applying {len(requests)} updates in a batch request...")
    
    chunk_size = 500
    for i in range(0, len(requests), chunk_size):
        chunk = requests[i:i + chunk_size]
        body = {'requests': chunk}
        
        # We need to wrap it in a try-except to debug any issues in specific chunks
        try:
            response = service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body=body
            ).execute()
        except Exception as e:
            # We catch errors here so we can see which chunk failed, or if it's the appendRows
            print(f"Error executing chunk {i//chunk_size + 1}/{len(requests)//chunk_size + 1}: {e}")
            
            # If the append dimension fails because it's already big enough, we can ignore it
            # and continue with the next chunks.
            if i == 0 and "appendDimension" in str(e):
                print("appendDimension failed (probably already expanded). Continuing...")
                # Try the chunk again without the first 3 requests
                if len(chunk) > 3:
                     body = {'requests': chunk[3:]}
                     try:
                         service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
                         print("Retroactive chunk 1 passed.")
                     except Exception as e2:
                         print(f"Retroactive chunk 1 failed: {e2}")
            continue

        print(f"Executed chunk {i//chunk_size + 1}/{len(requests)//chunk_size + 1}")

    print("Successfully updated Helper_V5 formulas and Order Data Validations for 1000 rows!")

if __name__ == '__main__':
    update_data_validation()
