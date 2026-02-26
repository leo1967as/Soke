# ปัญหาปัจจุบัน - Current Problems

## สถานะ: Bot รันได้ แต่ยังไม่มี Knowledge Base

---

## 1. Notion - ปัญหา Database ID

### สาเหตุ
URL ที่ให้มา: `https://www.notion.so/Sokeberlnwza-Roblox-3127c3141829801b83afce25c9dcb17c`

นี่คือ **Page** ไม่ใช่ **Database**!

Notion มี 2 แบบ:
- **Page** - หน้าธรรมดา ไม่สามารถ query ได้ (ใช้ API ต่างกัน)
- **Database** - ตาราง/Board/List สามารถ query ได้

### Error ที่ได้
```
Invalid request URL.
'DatabasesEndpoint' object has no attribute 'query'
```

### วิธีแก้ไข

**ตัวเลือก A: สร้าง Database ใหม่**
1. เปิด Notion
2. สร้าง Database ใหม่ (Table/Board/List)
3. ใส่ข้อมูลเกี่ยวกับ Roblox boosting service
4. คลิก Share → Add connections → เลือก Integration
5. คัดลอก Database ID จาก URL (รูปแบบ: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

**ตัวเลือก B: ใช้ Page ID (แก้โค้ดแล้ว)**
- แก้โค้ดให้รองรับ Page แล้ว
- ใช้ `NOTION_PAGE_IDS` แทน `NOTION_DATABASE_IDS`
- แต่ต้องตรวจสอบว่า Integration มีสิทธิ์เข้าถึง Page นั้นหรือไม่

### ต้องทำ
```env
# ใน .env
NOTION_PAGE_IDS=3127c314-1829-801b-83af-ce25c9dcb17c
```

---

## 2. Google Sheets - ปัญหา Service Account

### สาเหตุ
ไฟล์ `Resource/service-account-key.json` มีแค่:
```json
key=AIzaSyBRWXYOygLmYWqk2PE-51AE4WbsDUG06c8
```

นี่คือ **API Key ธรรมดา** ไม่ใช่ **Service Account JSON**

Service Account JSON ต้องมีโครงสร้างแบบนี้:
```json
{
  "type": "service_account",
  "project_id": "...",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----...",
  "client_email": "...",
  ...
}
```

### Error ที่ได้
```
Expecting value: line 1 column 1 (char 0)
```

### วิธีแก้ไข

1. ไป Google Cloud Console: https://console.cloud.google.com/
2. เลือก Project
3. ไป Service Accounts (APIs & Services → Credentials)
4. สร้าง Service Account ใหม่ หรือใช้ existing
5. สร้าง Key (Create new key → JSON)
6. ดาวน์โหลดไฟล์ JSON
7. แปลงเป็น base64:
   ```powershell
   [Convert]::ToBase64String([IO.File]::ReadAllBytes("path/to/key.json"))
   ```
8. ใส่ใน `.env`:
   ```env
   GOOGLE_SA_BASE64=...
   ```

### ต้องทำ
```env
# ใน .env
GOOGLE_SA_BASE64=<ใส่ base64 ของ service account JSON>
SHEETS_SPREADSHEET_IDS=166jyYS0YPGVzHtV6CEfLILtmgjEX1McNK4BgxXkeyPg
   ```

---

## 3. Notion Integration Permission

### ปัญหา
แม้จะมี Page ID ถูกต้อง ก็ต้องตรวจสอบว่า Integration มีสิทธิ์เข้าถึง

### วิธีตรวจสอบ
1. เปิด Notion Page/Database
2. คลิก **Share** (มุมบนขวา)
3. ดูว่า Integration อยู่ในรายชื่อ **Connections** หรือไม่
4. ถ้าไม่มี → คลิก **Add connections** → เลือก Integration

### ต้องทำ
- เปิด Page: `https://www.notion.so/Sokeberlnwza-Roblox-3127c3141829801b83afce25c9dcb17c`
- คลิก Share
- Add connections → เลือก Integration ที่มี token: `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`

---

## 4. สรุปสิ่งที่ต้องทำ

### Priority 1 (สำคัญ)
- [ ] ตรวจสอบว่า Notion Integration มีสิทธิ์เข้าถึง Page
- [ ] ทดสอบด้วย `python test_notion_quick.py`

### Priority 2 (ถ้าต้องการ Google Sheets)
- [ ] สร้าง Service Account ใน Google Cloud Console
- [ ] ดาวน์โหลด JSON key
- [ ] แปลงเป็น base64 และใส่ใน `.env`

### Priority 3 (ปรับปรุง)
- [ ] สร้าง Database ใน Notion (ถ้าต้องการ query แบบ database)
- [ ] เพิ่มข้อมูลใน Notion/Sheets เพิ่มเติม

---

## คำสั่งทดสอบ

### ทดสอบ Notion
```bash
cd core/ai_support_bot
python test_notion_quick.py
```

### รัน Bot
```bash
cd core/ai_support_bot
run.bat
```

### ดู Logs
```bash
type logs\audit.jsonl
```

---

## อัพเดตล่าสุด
- 26 กุมภาพันธ์ 2026, 06:35 ICT
