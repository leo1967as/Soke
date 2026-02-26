/**
 * ============================================================
 *  📋 AUTO CHANGE LOG + 🔔 DISCORD ALERT — Sokeber Finance V5
 * ============================================================
 *
 * 📌 วิธีติดตั้ง:
 *  1. Extensions > Apps Script
 *  2. ลบโค้ดเดิม → paste โค้ดนี้
 *  3. Save (Ctrl+S)
 *  4. เลือก setupTrigger → ▶ Run → Allow Permission
 *  5. เสร็จ! ✅
 * ============================================================
 */

const LOG_SHEET_NAME   = "📋 Change Log";
const IGNORED_SHEETS   = ["📋 Change Log", "Helper_V5"];
const DISCORD_WEBHOOK  = "https://discord.com/api/webhooks/1475957484312068106/VeOzVzkgwECCEOY08YKsOvXqxAK0gtzJsYEpL1f3qA7BtFQAtrsNkp6QmZvdNqxVbVXo";

// ชีตไหนแจ้ง Discord บ้าง (ลบออกถ้าไม่อยากแจ้ง)
const DISCORD_ALERT_SHEETS = [
  "รับออเดอร์ (V5)",
  "เบิกกองกลาง",
  "ถอนเงินส่วนตัว",
  "Settings_V5"
];

// Emoji + สีต่อชีต
const SHEET_CONFIG = {
  "รับออเดอร์ (V5)":  { emoji: "📋", color: 0xe74c3c },  // แดง
  "เบิกกองกลาง":       { emoji: "🏦", color: 0x9b59b6 },  // ม่วง
  "ถอนเงินส่วนตัว":    { emoji: "💸", color: 0x2ecc71 },  // เขียว
  "Settings_V5":       { emoji: "⚙️", color: 0x3498db },  // น้ำเงิน
};

// ========================================================
//  SETUP — รันครั้งเดียวเท่านั้น
// ========================================================
function setupTrigger() {
  // ลบ trigger เก่า
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === "onEditInstallable") {
      ScriptApp.deleteTrigger(t);
    }
  });
  // สร้างใหม่
  ScriptApp.newTrigger("onEditInstallable")
    .forSpreadsheet(SpreadsheetApp.getActive())
    .onEdit()
    .create();

  SpreadsheetApp.getUi().alert("✅ ติดตั้งสำเร็จ!\nระบบจะ Log + แจ้ง Discord อัตโนมัติ");
}

// ========================================================
//  MAIN — ทำงานทุกครั้งที่มีการแก้ไข
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
    const headerRow = sheet.getRange(1, range.getColumn()).getValue();

    // 1. เขียน Change Log
    writeToLog(timestamp, user, sheetName, headerRow || cellRef, cellRef, oldValue, newValue);

    // 2. ส่ง Discord
    if (DISCORD_ALERT_SHEETS.includes(sheetName)) {
      sendDiscordAlert(sheetName, cellRef, headerRow, oldValue, newValue, user, timestamp);
    }

  } catch (err) {
    console.error("ChangeLog Error:", err);
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

  // สีแถว
  const cfg = SHEET_CONFIG[sheetName];
  if (cfg) {
    const hexColor = "#" + cfg.color.toString(16).padStart(6, "0");
    // เปลี่ยนให้มืดลงสำหรับ background
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

// ========================================================
//  HELPER — ทำสีมืดลง ~40%
// ========================================================
function darkenHex(hex) {
  const r = Math.floor(parseInt(hex.slice(1,3), 16) * 0.35);
  const g = Math.floor(parseInt(hex.slice(3,5), 16) * 0.35);
  const b = Math.floor(parseInt(hex.slice(5,7), 16) * 0.35);
  return "#" + [r,g,b].map(v => v.toString(16).padStart(2,"0")).join("");
}

// ========================================================
//  RESET — ลบ trigger ทั้งหมด (ถ้าต้องการรีเซ็ต)
// ========================================================
function removeTrigger() {
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));
  SpreadsheetApp.getUi().alert("🗑️ ลบ Trigger ทั้งหมดแล้ว");
}

// ========================================================
//  TEST — ทดสอบส่ง Discord โดยไม่ต้องแก้ชีต
// ========================================================
function testDiscord() {
  sendDiscordAlert(
    "รับออเดอร์ (V5)", "E5", "แพ็กเกจ",
    "BF - 140", "BF - 500+",
    "narawhich2547@gmail.com",
    Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "dd/MM/yyyy HH:mm:ss")
  );
  SpreadsheetApp.getUi().alert("📨 ส่ง Discord แล้ว! เช็คช่องใน Discord ได้เลย");
}
