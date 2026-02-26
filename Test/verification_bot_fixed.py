import discord
from discord.ext import commands
from discord.ui import Button, View
import os

# Config
TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
GUILD_ID = 1475450344334037063
MEMBER_ROLE_ID = 1476201135898493049 # Updated from previous PASS log
VERIFY_CHAN_ID = 1476201306598150274

def load_token(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if "=" in content:
            return content.split("=")[1].strip()
        return content

TOKEN = load_token(TOKEN_FILE)

class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None) # Permanent view

    @discord.ui.button(label="✅ ยืนยันตัวตน (Verify)", style=discord.ButtonStyle.green, custom_id="verify_button")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(MEMBER_ROLE_ID)
        if role in interaction.user.roles:
            await interaction.response.send_message("คุณยืนยันตัวตนเรียบร้อยแล้ว!", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("ยืนยันตัวตนสำเร็จ! ยินดีต้อนรับสู่ Sokeberlnwza ครับ", ephemeral=True)

class VerificationBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(VerifyView())

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")
        # Direct setup on startup to ensure message exists
        channel = self.get_channel(VERIFY_CHAN_ID)
        if channel:
            # Clear old messages to avoid confusion
            try:
                await channel.purge(limit=10)
            except:
                pass
                
            embed = discord.Embed(
                title="🛡️ ระบบยืนยันตัวตน (Verification System)",
                description=(
                    "ยินดีต้อนรับเข้าสู่ **Sokeberlnwza** ครับ!\n\n"
                    "เพื่อความปลอดภัยและความเป็นระเบียบของ Server\n"
                    "รบกวนกดปุ่มด้านล่างเพื่อรับบทบาท **Member** และเข้าถึงห้องอื่นๆ ครับ\n\n"
                    "⚖️ *การกดปุ่มหมายถึงคุณยอมรับกฎของ Server เรียบร้อยแล้ว*"
                ),
                color=0x2ecc71
            )
            await channel.send(embed=embed, view=VerifyView())
            print(f"Verification message sent to {channel.name}")

bot = VerificationBot()

if __name__ == "__main__":
    bot.run(TOKEN)
