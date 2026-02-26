"""Test script for verification button functionality."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import discord
from discord import Embed
from core.security_bot.config import BotConfig
from core.security_bot.views import VerifyView
from core.security_bot.constants import EmbedColor

config = BotConfig.load_from_env()
intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}')
    guild = client.get_guild(config.guild_id)
    channel = guild.get_channel(config.verify_channel_id)
    
    # Send test verify message
    view = VerifyView(
        member_role_id=config.member_role_id,
        unverified_role_id=config.unverified_role_id,
        log_channel_id=config.log_channel_id
    )
    
    embed = Embed(
        title='🛡️ ระบบยืนยันตัวตน (Verification System)',
        description=(
            'ยินดีต้อนรับเข้าสู่ **Sokeberlnwza** ครับ!\n\n'
            'เพื่อความปลอดภัยและความเป็นระเบียบของ Server\n'
            'รบกวนกดปุ่มด้านล่างเพื่อรับบทบาท **Member** และเข้าถึงห้องอื่นๆ ครับ\n\n'
            '⚖️ *การกดปุ่มหมายถึงคุณยอมรับกฎของ Server เรียบร้อยแล้ว*'
        ),
        color=EmbedColor.VERIFIED
    )
    
    await channel.send(embed=embed, view=view)
    print('✅ Sent verify message with button')
    print('🧪 Test: Click the verify button in Discord')
    await client.close()

if __name__ == "__main__":
    print("🧪 Testing Verify Button...")
    client.run(config.token)
