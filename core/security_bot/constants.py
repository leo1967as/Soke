"""Constants and enums for Security Bot."""
from enum import IntEnum


class EmbedColor(IntEnum):
    """Embed colors for different event types."""
    MEMBER_JOIN = 0x3498db      # Blue
    MEMBER_LEAVE = 0x95a5a6     # Gray
    MESSAGE_DELETE = 0xe67e22   # Orange
    MESSAGE_EDIT = 0xf1c40f     # Yellow
    ROLE_UPDATE = 0x9b59b6      # Purple
    VERIFIED = 0x2ecc71         # Green
    WARNING = 0xe74c3c          # Red
    BOT_STATUS = 0x00ff00       # Bright Green
    ERROR = 0xff0000            # Bright Red


class CustomID:
    """Custom IDs for persistent UI components."""
    VERIFY_BUTTON = "security_bot:verify_button"


class ErrorMessages:
    """Error messages for user feedback."""
    ROLE_NOT_FOUND = "❌ ไม่พบยศที่ต้องการ! กรุณาแจ้ง Admin"
    ALREADY_VERIFIED = "✅ คุณยืนยันตัวตนเรียบร้อยแล้ว!"
    VERIFICATION_SUCCESS = "✅ ยืนยันตัวตนสำเร็จ! ยินดีต้อนรับสู่ Sokeberlnwza ครับ"
    VERIFICATION_FAILED = "❌ เกิดข้อผิดพลาดในการยืนยันตัวตน กรุณาลองใหม่อีกครั้ง"
    NO_PERMISSION = "❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้!"
    COMMAND_ERROR = "❌ เกิดข้อผิดพลาด: {error}"


class LogMessages:
    """Log messages for console output."""
    BOT_STARTING = "Starting Security Bot..."
    BOT_READY = "Bot is ready and monitoring"
    BOT_SHUTDOWN = "Bot is shutting down..."
    COG_LOADED = "Loaded {cog_name}"
    COG_FAILED = "Failed to load {cog_name}: {error}"
    VIEW_REGISTERED = "Registered {view_name}"
    ROLE_ASSIGNED = "Assigned {role_name} to {user_name} ({user_id})"
    ROLE_FAILED = "Failed to assign {role_name} to {user_name}: {error}"
