import discord
from discord.ext import commands
from discord.ui import Button, View
import os

# Config
TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
GUILD_ID = 1475450344334037063
MEMBER_ROLE_ID = 1476201289129132092
UNVERIFIED_ROLE_ID = 1476208022945530090
VERIFY_CHAN_ID = 1476201306598150274

def load_token(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if "=" in content:
            return content.split("=")[1].strip()
        return content

TOKEN = load_token(TOKEN_FILE)

class VerifyModal(discord.ui.Modal, title="ยืนยันตัวตน (2-Step Verification)"):
    answer = discord.ui.TextInput(
        label="พิมพ์คำว่า 'Sokeber' เพื่อยืนยัน",
        style=discord.TextStyle.short,
        placeholder="Sokeber",
        required=True,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        if self.answer.value.strip().lower() == "sokeber":
            member_role = interaction.guild.get_role(MEMBER_ROLE_ID)
            unverified_role = interaction.guild.get_role(UNVERIFIED_ROLE_ID)
            
            await interaction.user.add_roles(member_role)
            if unverified_role in interaction.user.roles:
                await interaction.user.remove_roles(unverified_role)
                
            await interaction.response.send_message("✅ ยืนยันตัวตนสำเร็จ! ยินดีต้อนรับสู่ Sokeberlnwza ครับ", ephemeral=True)
        else:
            await interaction.response.send_message("❌ คำตอบไม่ถูกต้อง กรุณาลองใหม่อีกครั้งครับ", ephemeral=True)

class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None) # Permanent view

    @discord.ui.button(label="✅ ยืนยันตัวตน (Verify)", style=discord.ButtonStyle.green, custom_id="verify_button")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(MEMBER_ROLE_ID)
        if role in interaction.user.roles:
            await interaction.response.send_message("คุณยืนยันตัวตนเรียบร้อยแล้ว!", ephemeral=True)
        else:
            await interaction.response.send_modal(VerifyModal())

class VerificationBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(VerifyView())

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")
        
    async def on_member_join(self, member):
        unverified_role = member.guild.get_role(UNVERIFIED_ROLE_ID)
        if unverified_role:
            try:
                await member.add_roles(unverified_role)
                print(f"Assigned Unverified role to {member.name}")
            except Exception as e:
                print(f"Failed to assign Unverified role to {member.name}: {e}")

bot = VerificationBot()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    channel = bot.get_channel(VERIFY_CHAN_ID)
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
    await ctx.send(f"ส่งข้อความ Verify ไปยังห้อง <#{VERIFY_CHAN_ID}> เรียบร้อยครับ!")

if __name__ == "__main__":
    bot.run(TOKEN)
