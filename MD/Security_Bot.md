# Security Bot - Sokeber Discord Bot

## ภาพรวม (Overview)

Security Bot เป็น Discord Bot ที่ออกแบบมาเพื่อดูแลความปลอดภัยและระบบยืนยันตัวตนของ Discord Server "Sokeberlnwza" บอททำงานอัตโนมัติในการตรวจสอบสมาชิก บันทึกกิจกรรมต่างๆ และจัดการการยืนยันตัวตน

---

## ความสามารถหลัก (Features)

### 1. ระบบแจกยศอัตโนมัติ (Auto Role Assignment)

**เมื่อสมาชิกใหม่เข้าร่วม Server:**
- บอทจะตรวจจับ event `on_member_join`
- แจกยศ **Unverified** ให้อัตโนมัติ (ID: 1476208022945530090)
- สมาชิกใหม่จะเห็นเฉพาะห้องยืนยันตัวตนเท่านั้น

**โค้ดที่เกี่ยวข้อง:**
```python
async def on_member_join(self, member):
    unverified_role = member.guild.get_role(UNVERIFIED_ROLE_ID)
    if unverified_role:
        await member.add_roles(unverified_role)
```

---

### 2. ระบบยืนยันตัวตน (Verification System)

**ขั้นตอนการยืนยัน:**
1. สมาชิกกดปุ่ม "✅ ยืนยันตัวตน (Verify)" ในห้อง 🏮𝐕𝐞𝐫𝐢𝐟𝐲-𝐡𝐞𝐫𝐞『✅』
2. บอทจะแจกยศ **Member** ให้ทันที (ID: 1476201135898493049)
3. ส่งข้อความต้อนรับแบบ ephemeral (เฉพาะผู้ใช้เห็น)
4. บันทึกการยืนยันลงใน Bot Logs

**โค้ดที่เกี่ยวข้อง:**
```python
@discord.ui.button(label="✅ ยืนยันตัวตน (Verify)", 
                   style=discord.ButtonStyle.green, 
                   custom_id="verify_button")
async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
    role = interaction.guild.get_role(MEMBER_ROLE_ID)
    if role in interaction.user.roles:
        await interaction.response.send_message("คุณยืนยันตัวตนเรียบร้อยแล้ว!", ephemeral=True)
    else:
        await interaction.user.add_roles(role)
        await interaction.response.send_message("ยืนยันตัวตนสำเร็จ! ยินดีต้อนรับสู่ Sokeberlnwza ครับ", ephemeral=True)
```

---

### 3. ระบบบันทึกกิจกรรม (Activity Logging)

#### 3.1 บันทึกการเข้า-ออกของสมาชิก

**เมื่อสมาชิกเข้าร่วม:**
- แสดงข้อมูล User, Mention, Account Age
- สีแดง (0xe74c3c) หาก Account อายุน้อยกว่า 7 วัน (เตือนความเสี่ยง)
- แสดง Avatar ของผู้ใช้

**เมื่อสมาชิกออก:**
- แสดงข้อมูล User และ ID
- สีเทา (0x95a5a6)

**โค้ดที่เกี่ยวข้อง:**
```python
async def on_member_join(self, member):
    diff = datetime.now().astimezone() - member.created_at
    is_new = diff.days < 7
    embed = Embed(title="📥 Member Joined", color=0x3498db, timestamp=datetime.now())
    embed.add_field(name="User", value=f"{member.mention} ({member})")
    embed.add_field(name="Account Age", value=f"{diff.days} days", inline=True)
    if is_new:
        embed.description = "⚠️ **Warning: This account is less than 7 days old!**"
        embed.color = 0xe74c3c
```

---

#### 3.2 บันทึกการลบข้อความ

**เมื่อข้อความถูกลบ:**
- แสดงข้อมูล Author, Channel, เนื้อหาที่ถูกลบ
- ไม่บันทึกข้อความจาก Bot
- สีส้ม (0xe67e22)

**โค้ดที่เกี่ยวข้อง:**
```python
async def on_message_delete(self, message):
    if message.author.bot: return
    embed = Embed(title="🗑️ Message Deleted", color=0xe67e22, timestamp=datetime.now())
    embed.add_field(name="Author", value=f"{message.author.mention} ({message.author})")
    embed.add_field(name="Channel", value=message.channel.mention)
    embed.add_field(name="Content", value=message.content or "[Empty/Attachment]", inline=False)
```

---

#### 3.3 บันทึกการแก้ไขข้อความ

**เมื่อข้อความถูกแก้ไข:**
- แสดง Before และ After
- ข้ามข้อความจาก Bot และข้อความที่ไม่เปลี่ยนแปลง
- สีเหลือง (0xf1c40f)

**โค้ดที่เกี่ยวข้อง:**
```python
async def on_message_edit(self, before, after):
    if before.author.bot or before.content == after.content: return
    embed = Embed(title="📝 Message Edited", color=0xf1c40f, timestamp=datetime.now())
    embed.add_field(name="Author", value=f"{before.author.mention} ({before.author})")
    embed.add_field(name="Before", value=before.content or "[Empty]", inline=False)
    embed.add_field(name="After", value=after.content or "[Empty]", inline=False)
```

---

#### 3.4 บันทึกการเปลี่ยนแปลงยศ

**เมื่อยศถูกแก้ไข:**
- แสดงชื่อยศที่ถูกเปลี่ยน
- ตรวจสอบการเปลี่ยนแปลง Permissions
- สีม่วง (0x9b59b6)

**โค้ดที่เกี่ยวข้อง:**
```python
async def on_guild_role_update(self, before, after):
    embed = Embed(title="🛡️ Role Updated", color=0x9b59b6, timestamp=datetime.now())
    embed.add_field(name="Role", value=after.name)
    if before.permissions != after.permissions:
        embed.add_field(name="Changes", value="Permissions were modified", inline=False)
```

---

## การตั้งค่า (Configuration)

```python
# Config
TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
GUILD_ID = 1475450344334037063
LOG_CHAN_ID = 1476202910005334118 # Bot Logs
MEMBER_ROLE_ID = 1476201135898493049 # Role to give on verify
UNVERIFIED_ROLE_ID = 1476208022945530090 # Role to assign on join
VERIFY_CHAN_ID = 1476201306598150274
```

| ตัวแปร | คำอธิบาย | ID |
|--------|----------|-----|
| `GUILD_ID` | ID ของ Server | 1475450344334037063 |
| `LOG_CHAN_ID` | ห้อง Bot Logs | 1476202910005334118 |
| `MEMBER_ROLE_ID` | ยศ Member (หลังยืนยัน) | 1476201135898493049 |
| `UNVERIFIED_ROLE_ID` | ยศ Unverified (ตอนเข้าใหม่) | 1476208022945530090 |
| `VERIFY_CHAN_ID` | ห้องยืนยันตัวตน | 1476201306598150274 |

---

## การทำงานของ Intents

บอทใช้ Intents ดังนี้:

```python
intents = discord.Intents.default()
intents.members = True      # ต้องการสำหรับ on_member_join
intents.message_content = True  # ต้องการสำหรับ on_message_delete/edit
intents.guilds = True      # ต้องการสำหรับ guild operations
intents.moderation = True   # ต้องการสำหรับ audit logs
```

---

## การติดตั้งและรัน (Installation & Running)

### ติดตั้ง Dependencies:
```bash
uv pip install discord.py
```

### รันบอท:
```bash
uv run Test/security_bot.py
```

### ตรวจสอบสถานะ:
```
Logged in as OREO_MM#6257 (ID: 1476183621256609834)
--- Security Monitoring Active ---
```

---

## ขั้นตอนการทำงานเมื่อสมาชิกใหม่เข้าร่วม

```
1. Member เข้าร่วม Server
         ↓
2. on_member_join event ถูกเรียก
         ↓
3. บอทแจกยศ Unverified
         ↓
4. บอทส่ง Log ไป Bot Logs
         ↓
5. Member เห็นเฉพาะห้อง Verify
         ↓
6. Member กดปุ่ม Verify
         ↓
7. บอทแจกยศ Member
         ↓
8. Member เข้าถึงห้องทั้งหมดได้
```

---

## ช่องทางการบันทึก (Logging Channels)

| Event | ชื่อ Embed | สี |
|-------|------------|-----|
| Member Join | 📥 Member Joined | 0x3498db (น้ำเงิน) |
| Member Leave | 📤 Member Left | 0x95a5a6 (เทา) |
| Message Delete | 🗑️ Message Deleted | 0xe67e22 (ส้ม) |
| Message Edit | 📝 Message Edited | 0xf1c40f (เหลือง) |
| Role Update | 🛡️ Role Updated | 0x9b59b6 (ม่วง) |
| Verified | ✅ Member Verified | 0x2ecc71 (เขียว) |

---

## หมายเหตุ (Notes)

- บอทใช้ Persistent View สำหรับปุ่ม Verify (`timeout=None`)
- ปุ่ม Verify ใช้ `custom_id="verify_button"` เพื่อให้ทำงานได้แม้บอท restart
- มีการหน่วงเวลา 0.5 วินาทีระหว่างการแก้ไขยศเพื่อป้องกัน Rate Limit
- ข้อความ Verification เป็นแบบ Ephemeral (เฉพาะผู้ใช้เห็น)

---

## อัปเดตล่าสุด

**วันที่:** 2026-02-25  
**เวลา:** 20:59 UTC+07:00  
**การเปลี่ยนแปลง:** เพิ่มระบบแจกยศ Unverified อัตโนมัติเมื่อสมาชิกใหม่เข้าร่วม
