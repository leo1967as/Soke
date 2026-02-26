# วิธีหา Database ID และ Spreadsheet ID

## 🔍 หา Notion Database ID

### ขั้นตอน:

1. **เปิด Notion Database** ที่ต้องการใช้
2. **คลิกที่ปุ่ม Share** ด้านบนขวา
3. **คลิก "Copy link"**
4. **Paste URL** จะได้แบบนี้:

```
https://www.notion.so/workspace/1a2b3c4d5e6f7g8h9i0j1k2l?v=...
                              └──────────────────────────┘
                                    Database ID (32 ตัวอักษร)
```

5. **คัดลอก Database ID** (ส่วนที่อยู่ระหว่าง workspace/ และ ?v=)

### ตัวอย่าง:

```
URL: https://www.notion.so/myworkspace/1a2b3c4d5e6f7g8h9i0j1k2l?v=abc123
Database ID: 1a2b3c4d5e6f7g8h9i0j1k2l
```

---

## 📊 หา Google Sheets Spreadsheet ID

### ขั้นตอน:

1. **เปิด Google Sheets** ที่ต้องการใช้
2. **ดูที่ URL** บนแถบ address bar
3. **คัดลอก Spreadsheet ID** จาก URL:

```
https://docs.google.com/spreadsheets/d/1ABC-xyz123_456DEF/edit#gid=0
                                       └──────────────┘
                                       Spreadsheet ID
```

### ตัวอย่าง:

```
URL: https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
Spreadsheet ID: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
```

---

## ⚙️ ใส่ใน .env

หลังจากได้ ID แล้ว ให้เพิ่มใน `.env`:

```env
# ── Notion ───────────────────────────────────
NOTION_TOKEN=secret_your_notion_token_here
NOTION_DATABASE_IDS=1a2b3c4d5e6f7g8h9i0j1k2l

# ── Google Sheets ────────────────────────────
GOOGLE_SA_BASE64=a2V5PUFJemFTeUJSV1hZT3lnTG1ZV3FrMlBFLTUxQUU0V2JzRFVHMDZjOA==
SHEETS_SPREADSHEET_IDS=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
```

### หลายแหล่งข้อมูล:

ถ้ามีหลาย database หรือ spreadsheet ให้คั่นด้วย comma:

```env
NOTION_DATABASE_IDS=id1,id2,id3
SHEETS_SPREADSHEET_IDS=sheet1,sheet2,sheet3
```

---

## ✅ ตรวจสอบว่า Integration มีสิทธิ์

### Notion:

1. เปิด Database
2. คลิก **Share**
3. ตรวจสอบว่า Integration ของคุณอยู่ในรายชื่อ
4. ถ้าไม่มี ให้คลิก **Add connections** → เลือก Integration

### Google Sheets:

1. เปิด Spreadsheet
2. คลิก **Share**
3. เพิ่ม email ของ Service Account (จากไฟล์ service-account-key.json)
4. ให้สิทธิ์ **Viewer** หรือ **Editor**

---

## 🧪 ทดสอบการเชื่อมต่อ

หลังจากใส่ ID แล้ว ให้รัน:

```bash
cd core/ai_support_bot
python test_notion.py
```

หรือ

```bash
python test_sheets.py  # (ถ้ามี)
```

---

## 🚀 รัน Bot

เมื่อใส่ ID ครบแล้ว:

```bash
cd core/ai_support_bot
run.bat
```

Bot จะดึงข้อมูลจาก Notion และ Sheets อัตโนมัติทุก 1 ชั่วโมง (หรือตามที่ตั้งค่าใน `INGESTION_INTERVAL_SECONDS`)
