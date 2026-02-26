/**
 * ============================================================
 *  📋 AUTO CHANGE LOG + 🔔 DISCORD ALERT + 🔒 AUTO-LOCK
 *  Sokeber Finance V5
 * ============================================================
 *
 * 📌 วิธีติดตั้ง:
 *  1. Extensions > Apps Script
 *  2. ลบโค้ดเดิม → paste โค้ดนี้
 *  3. Save (Ctrl+S)
 *  4. เลือก setupTrigger → ▶ Run → Allow Permission
 *  5. กลับไปที่หน้าจอ Google Sheet ระบบจะขึ้นเมนู "Admin" ให้ใช้งาน
 * ============================================================
 */

const LOG_SHEET_NAME   = "📋 Change Log";
const IGNORED_SHEETS   = ["📋 Change Log", "Helper_V5"];
const DISCORD_WEBHOOK  = "https://discord.com/api/webhooks/1475957484312068106/VeOzVzkgwECCEOY08YKsOvXqxAK0gtzJsYEpL1f3qA7BtFQAtrsNkp6QmZvdNqxVbVXo";

const DISCORD_ALERT_SHEETS = [
  "รับออเดอร์ (V5)",
  "เบิกกองกลาง",
  "ถอนเงินส่วนตัว",
  "Settings_V5"
];

const SHEET_CONFIG = {
  "รับออเดอร์ (V5)":  { emoji: "📋", color: 0xe74c3c },
  "เบิกกองกลาง":       { emoji: "🏦", color: 0x9b59b6 },
  "ถอนเงินส่วนตัว":    { emoji: "💸", color: 0x2ecc71 },
  "Settings_V5":       { emoji: "⚙️", color: 0x3498db },
};

// ========================================================
//  UI MENU
// ========================================================
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('👑 Admin')
      .addItem('🔓 ปลดล็อคออเดอร์แถวนี้', 'unlockCurrentRow')
      .addToUi();
}

// ========================================================
//  SETUP
// ========================================================
function setupTrigger() {
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === "onEditInstallable") {
      ScriptApp.deleteTrigger(t);
    }
  });
  ScriptApp.newTrigger("onEditInstallable")
    .forSpreadsheet(SpreadsheetApp.getActive())
    .onEdit()
    .create();

  SpreadsheetApp.getUi().alert("✅ ติดตั้งสำเร็จ!\nระบบจะ Log + แจ้ง Discord + ล็อคแถวอัตโนมัติ");
  onOpen(); // เรียกสร้างเมนูด้วยเลยครั้งแรก
}

// ========================================================
//  MAIN
// ========================================================
function onEditInstallable(e) {
  try {
    const sheet     = e.range.getSheet();
    const sheetName = sheet.getName();

    if (IGNORED_SHEETS.includes(sheetName)) return;

    const range    = e.range;
    const oldValue = e.oldValue !== undefined ? e.oldValue : "-";
    const newValue = range.getValue();

    if (String(oldValue) === String(newValue)) return;

    const user      = Session.getActiveUser().getEmail() || "Unknown";
    const timestamp = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "dd/MM/yyyy HH:mm:ss");
    const cellRef   = range.getA1Notation();
    
    // Check if header row because inserted range doesn't always hit exactly, fallback safely
    let headerRow = "";
    if (range.getRow() > 1 && range.getColumn() <= sheet.getLastColumn()) {
       headerRow = sheet.getRange(1, range.getColumn()).getValue();
    }

    // 1. เขียน Change Log
    writeToLog(timestamp, user, sheetName, headerRow || cellRef, cellRef, oldValue, newValue);

    // 2. ส่ง Discord
    if (DISCORD_ALERT_SHEETS.includes(sheetName)) {
      sendDiscordAlert(sheetName, cellRef, headerRow, oldValue, newValue, user, timestamp);
    }

    // 3. ระบบ Auto-Lock ถ้าเป็นชีตรับออเดอร์ และแก้คอลัมน์ D (สถานะ - Index 4)
    if (sheetName === "รับออเดอร์ (V5)" && range.getColumn() === 4 && range.getRow() > 1) {
      if (String(newValue).trim() === "เรียบร้อย") {
        lockRow(sheet, range.getRow(), user);
      }
    }

  } catch (err) {
    console.error("ChangeLog Error:", err);
  }
}

// ========================================================
//  AUTO LOCK (Color handled by Conditional Formatting)
// ========================================================
function lockRow(sheet, rowIdx, triggerUser) {
  const lastCol = sheet.getLastColumn();
  const rowRange = sheet.getRange(rowIdx, 1, 1, lastCol);
  
  // 1. ลบพื้นหลัง Manual ออก (ให้ Conditional Formatting ทำงานแทน)
  rowRange.setBackground(null); 

  // 2. ตั้ง Protect Range ล็อค
  const protections = sheet.getProtections(SpreadsheetApp.ProtectionType.RANGE);
  
  // ถ้าบังเอิญมี Protect เก่าอยู่ ให้ลบแล้วสร้างใหม่
  protections.forEach(p => {
    if (p.getRange().getRow() === rowIdx && p.getRange().getNumRows() === 1) {
      p.remove();
    }
  });

  const protection = rowRange.protect().setDescription(`ล็อคออเดอร์แถวที่ ${rowIdx} (สำเร็จ)`);
  
  // ให้สิทธิ์คนเดียวคือ Owner ลบคนอื่นออกหมด
  const me = Session.getEffectiveUser();
  protection.addEditor(me);
  protection.removeEditors(protection.getEditors().map(u => u.getEmail()));
}

// ========================================================
//  UNLOCK ROW (ADMIN ONLY)
// ========================================================
function unlockCurrentRow() {
  const sheet = SpreadsheetApp.getActiveSheet();
  
  if (sheet.getName() !== "รับออเดอร์ (V5)") {
    SpreadsheetApp.getUi().alert("❗ กรุณาใช้ในชีต 'รับออเดอร์ (V5)'");
    return;
  }

  const row = sheet.getActiveCell().getRow();
  if (row <= 1) return;

  const protections = sheet.getProtections(SpreadsheetApp.ProtectionType.RANGE);
  let removedCount = 0;
  
  protections.forEach(p => {
    if (p.getRange().getRow() === row) {
      p.remove();
      removedCount++;
    }
  });

  if (removedCount > 0) {
    // เปลี่ยนสถานะเป็นว่าง (กำลังทำ) ไปเลยเพื่อความเคลียร์ (คอลัมน์ D - Index 4)
    sheet.getRange(row, 4).setValue("กำลังทำ");
    // ล้างสีออกให้เหมือนปกติ 
    sheet.getRange(row, 1, 1, sheet.getLastColumn()).setBackground(null); 

    SpreadsheetApp.getUi().alert(`🔓 ปลดล็อคออเดอร์แถวที่ ${row} เรียบร้อยแล้ว`);
  } else {
    SpreadsheetApp.getUi().alert(`แถวที่ ${row} ไม่ได้ถูกล็อคอยู่ครับ`);
  }
}

// ========================================================
//  WRITE LOG
// ========================================================
function writeToLog(timestamp, user, sheetName, column, cell, oldVal, newVal) {
  const ss       = SpreadsheetApp.getActive();
  const logSheet = ss.getSheetByName(LOG_SHEET_NAME);
  if (!logSheet) return;

  const lastRow = Math.max(logSheet.getLastRow(), 1) + 1;
  logSheet.getRange(lastRow, 1, 1, 8).setValues([[
    timestamp, user, sheetName, column, cell, oldVal, newVal, ""
  ]]);

  const cfg = SHEET_CONFIG[sheetName];
  if (cfg) {
    const hexColor = "#" + cfg.color.toString(16).padStart(6, "0");
    logSheet.getRange(lastRow, 1, 1, 8)
            .setBackground(darkenHex(hexColor))
            .setFontColor("#eeeeee")
            .setFontSize(9);
  }
}

// ========================================================
//  DISCORD WEBHOOK
// ========================================================
function sendDiscordAlert(sheetName, cell, column, oldVal, newVal, user, timestamp) {
  const cfg   = SHEET_CONFIG[sheetName] || { emoji: "📝", color: 0x95a5a6 };
  const label = column && column !== cell ? `${column} (${cell})` : cell;

  const payload = {
    embeds: [{
      title:       `${cfg.emoji}  แก้ไขใน "${sheetName}"`,
      description: `**${label}**`,
      color:       cfg.color,
      fields: [
        { name: "👤 ผู้แก้",   value: user,           inline: true  },
        { name: "📍 เซล",      value: cell,           inline: true  },
        { name: "🗑️ ค่าเก่า", value: String(oldVal) || "-", inline: true  },
        { name: "✅ ค่าใหม่", value: String(newVal) || "-", inline: true  },
      ],
      footer:    { text: "Sokeber Finance V5 — Auto Log" },
      timestamp: new Date().toISOString()
    }]
  };

  UrlFetchApp.fetch(DISCORD_WEBHOOK, {
    method:      "post",
    contentType: "application/json",
    payload:     JSON.stringify(payload),
    muteHttpExceptions: true
  });
}

function darkenHex(hex) {
  const r = Math.floor(parseInt(hex.slice(1,3), 16) * 0.35);
  const g = Math.floor(parseInt(hex.slice(3,5), 16) * 0.35);
  const b = Math.floor(parseInt(hex.slice(5,7), 16) * 0.35);
  return "#" + [r,g,b].map(v => v.toString(16).padStart(2,"0")).join("");
}
