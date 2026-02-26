import discord
from discord.ext import commands
from discord import Embed
import os
from datetime import datetime

# Config
TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
GUILD_ID = 1475450344334037063
LOG_CHAN_ID = 1476202910005334118 # Bot Logs
MEMBER_ROLE_ID = 1476201135898493049 # Role to give on verify
UNVERIFIED_ROLE_ID = 1476208022945530090 # Role to assign on join
VERIFY_CHAN_ID = 1476201306598150274

def load_token(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if "=" in content:
            return content.split("=")[1].strip()
        return content

TOKEN = load_token(TOKEN_FILE)

class VerifyView(discord.ui.View):
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
            # Log successful verification
            log_chan = interaction.guild.get_channel(LOG_CHAN_ID)
            if log_chan:
                embed = Embed(title="✅ Member Verified", color=0x2ecc71, timestamp=datetime.now())
                embed.add_field(name="User", value=f"{interaction.user.mention} ({interaction.user})")
                embed.add_field(name="ID", value=interaction.user.id)
                await log_chan.send(embed=embed)

class SecurityBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.guilds = True 
        intents.moderation = True # Required for audit logs access if using them directly, but events work too
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(VerifyView())

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("--- Security Monitoring Active ---")

    # 1. Member Join/Leave Logging
    async def on_member_join(self, member):
        log_chan = self.get_channel(LOG_CHAN_ID)
        if not log_chan: return
        
        # Assign Unverified role to new member
        unverified_role = member.guild.get_role(UNVERIFIED_ROLE_ID)
        if unverified_role:
            try:
                await member.add_roles(unverified_role)
                print(f"Assigned Unverified role to {member.name}")
            except Exception as e:
                print(f"Failed to assign Unverified role to {member.name}: {e}")
        
        # Check Account Age for security
        diff = datetime.now().astimezone() - member.created_at
        is_new = diff.days < 7
        
        embed = Embed(title="📥 Member Joined", color=0x3498db, timestamp=datetime.now())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="User", value=f"{member.mention} ({member})")
        embed.add_field(name="Account Age", value=f"{diff.days} days", inline=True)
        if is_new:
            embed.description = "⚠️ **Warning: This account is less than 7 days old!**"
            embed.color = 0xe74c3c
        await log_chan.send(embed=embed)

    async def on_member_remove(self, member):
        log_chan = self.get_channel(LOG_CHAN_ID)
        if not log_chan: return
        embed = Embed(title="📤 Member Left", color=0x95a5a6, timestamp=datetime.now())
        embed.add_field(name="User", value=f"{member} ({member.id})")
        await log_chan.send(embed=embed)

    # 2. Message Audit
    async def on_message_delete(self, message):
        if message.author.bot: return
        log_chan = self.get_channel(LOG_CHAN_ID)
        if not log_chan: return
        
        embed = Embed(title="🗑️ Message Deleted", color=0xe67e22, timestamp=datetime.now())
        embed.add_field(name="Author", value=f"{message.author.mention} ({message.author})")
        embed.add_field(name="Channel", value=message.channel.mention)
        embed.add_field(name="Content", value=message.content or "[Empty/Attachment]", inline=False)
        await log_chan.send(embed=embed)

    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content: return
        log_chan = self.get_channel(LOG_CHAN_ID)
        if not log_chan: return
        
        embed = Embed(title="📝 Message Edited", color=0xf1c40f, timestamp=datetime.now())
        embed.add_field(name="Author", value=f"{before.author.mention} ({before.author})")
        embed.add_field(name="Channel", value=before.channel.mention)
        embed.add_field(name="Before", value=before.content or "[Empty]", inline=False)
        embed.add_field(name="After", value=after.content or "[Empty]", inline=False)
        await log_chan.send(embed=embed)

    # 3. Role/Permission Changes
    async def on_guild_role_update(self, before, after):
        log_chan = self.get_channel(LOG_CHAN_ID)
        if not log_chan: return
        
        embed = Embed(title="🛡️ Role Updated", color=0x9b59b6, timestamp=datetime.now())
        embed.add_field(name="Role", value=after.name)
        if before.permissions != after.permissions:
            embed.add_field(name="Changes", value="Permissions were modified", inline=False)
        await log_chan.send(embed=embed)

if __name__ == "__main__":
    bot = SecurityBot()
    bot.run(TOKEN)
