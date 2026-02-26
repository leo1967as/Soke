# Notion Sample Data for Testing

## สร้าง Notion Database สำหรับทดสอบ

### 1. สร้าง Database ชื่อ "Sokeber FAQ"

ใน Notion workspace ของคุณ:

1. สร้าง Page ใหม่ชื่อ **"Sokeber FAQ"**
2. เลือก Database → Table
3. เพิ่ม Properties:
   - **Name** (Title) - ชื่อคำถาม
   - **Category** (Select) - หมวดหมู่
   - **Answer** (Text) - คำตอบ

### 2. ข้อมูลตัวอย่างที่ควรใส่

#### คำถามที่ 1: ราคาแพ็คเกจ
- **Name**: ราคาแพ็คเกจต่างๆ เท่าไหร่
- **Category**: Pricing
- **Answer**: 
```
Sokeber มีแพ็คเกจดังนี้:
- Basic Plan: 299 บาท/เดือน (รองรับ 5 users)
- Pro Plan: 899 บาท/เดือน (รองรับ 20 users + Advanced Analytics)
- Enterprise Plan: ติดต่อเรา (Custom features + Dedicated support)
```

#### คำถามที่ 2: นโยบายคืนเงิน
- **Name**: นโยบายการคืนเงิน
- **Category**: Policy
- **Answer**:
```
Sokeber มีนโยบายคืนเงิน 30 วัน
- สามารถขอคืนเงินได้ภายใน 30 วันหลังจากซื้อ
- ไม่มีค่าธรรมเนียมใดๆ
- ติดต่อทีมงานที่ support@sokeber.com
```

#### คำถามที่ 3: เวลาทำการ
- **Name**: เวลาทำการของทีมงาน
- **Category**: Support
- **Answer**:
```
ทีมงาน Sokeber ให้บริการ:
- จันทร์-ศุกร์: 9:00-18:00 น. (เวลาไทย)
- เสาร์-อาทิตย์: ปิดทำการ
- ติดต่อฉุกเฉิน: Line @sokeber (24/7)
```

#### คำถามที่ 4: วิธีการชำระเงิน
- **Name**: ชำระเงินได้ยังไง
- **Category**: Payment
- **Answer**:
```
รับชำระผ่าน:
- บัตรเครดิต/เดบิต (Visa, Mastercard)
- PromptPay
- โอนเงินธนาคาร (กสิกร, ไทยพาณิชย์, กรุงเทพ)
- TrueMoney Wallet
```

#### คำถามที่ 5: ฟีเจอร์หลัก
- **Name**: Sokeber มีฟีเจอร์อะไรบ้าง
- **Category**: Features
- **Answer**:
```
ฟีเจอร์หลักของ Sokeber:
✅ Financial Dashboard - ภาพรวมการเงินแบบ Real-time
✅ Expense Tracking - บันทึกรายจ่ายอัตโนมัติ
✅ Budget Planning - วางแผนงบประมาณ
✅ Report Generation - สร้างรายงานทางการเงิน
✅ Multi-currency Support - รองรับหลายสกุลเงิน
```

### 3. Share Database กับ Notion Integration

1. คลิกที่ **Share** ด้านบนขวาของ Database
2. คลิก **Add connections**
3. เลือก Integration ที่คุณสร้างไว้
4. คลิก **Invite**

### 4. คัดลอก Database ID

จาก URL ของ Notion page:
```
https://www.notion.so/workspace/DATABASE_ID?v=...
                              └─────────────┘
                              คัดลอกส่วนนี้
```

### 5. เพิ่ม Database ID ใน .env

```env
NOTION_DATABASE_ID=your_database_id_here
```

## ทดสอบการดึงข้อมูล

หลังจากสร้างข้อมูลแล้ว ให้ทดสอบว่า bot สามารถดึงข้อมูลจาก Notion ได้:

```python
# Test script
from core.ai_support_bot.config import load_config
from core.ai_support_bot.rag.notion_fetcher import NotionFetcher
from notion_client import Client

config = load_config()
client = Client(auth=config.notion_token)
fetcher = NotionFetcher(client)

# ทดสอบดึง database
pages = fetcher.fetch_database_pages("YOUR_DATABASE_ID")
for page in pages:
    print(f"Title: {page.title}")
    print(f"Content: {page.content[:100]}...")
    print("---")
```
