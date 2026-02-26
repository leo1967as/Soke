"""Security Logging Cog - Handles all security-related event logging."""
import discord
from discord.ext import commands
from discord import Embed
from datetime import datetime, timezone
from typing import Optional
import logging

from ..config import BotConfig
from ..constants import EmbedColor
from ..utils import get_account_age, is_new_account, format_user_info

logger = logging.getLogger(__name__)


class SecurityLoggingCog(commands.Cog):
    """Cog for logging security events."""
    
    def __init__(self, bot: commands.Bot, config: BotConfig):
        self.bot = bot
        self.config = config
    
    def get_log_channel(self, guild: discord.Guild) -> Optional[discord.TextChannel]:
        """Get the log channel from config."""
        return guild.get_channel(self.config.log_channel_id)
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Log member join with security checks."""
        log_channel = self.get_log_channel(member.guild)
        if not log_channel:
            return
        
        account_age = get_account_age(member.created_at)
        is_new = is_new_account(member.created_at, self.config.new_account_threshold_days)
        
        embed = Embed(
            title="📥 Member Joined",
            color=EmbedColor.MEMBER_JOIN if not is_new else EmbedColor.WARNING,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="User", value=format_user_info(member), inline=True)
        embed.add_field(name="Account Age", value=f"{account_age} days", inline=True)
        
        if is_new:
            embed.description = f"⚠️ **Warning: Account is less than {self.config.new_account_threshold_days} days old!**"
        
        await log_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Log member leave."""
        log_channel = self.get_log_channel(member.guild)
        if not log_channel:
            return
        
        embed = Embed(
            title="📤 Member Left",
            color=EmbedColor.MEMBER_LEAVE,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=True)
        
        await log_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Log deleted messages."""
        if message.author.bot:
            return
        
        log_channel = self.get_log_channel(message.guild)
        if not log_channel:
            return
        
        embed = Embed(
            title="🗑️ Message Deleted",
            color=EmbedColor.MESSAGE_DELETE,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Author", value=format_user_info(message.author), inline=True)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="Content", value=message.content or "[Empty/Attachment]", inline=False)
        
        await log_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Log edited messages."""
        if before.author.bot or before.content == after.content:
            return
        
        log_channel = self.get_log_channel(before.guild)
        if not log_channel:
            return
        
        embed = Embed(
            title="📝 Message Edited",
            color=EmbedColor.MESSAGE_EDIT,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Author", value=format_user_info(before.author), inline=True)
        embed.add_field(name="Channel", value=before.channel.mention, inline=True)
        embed.add_field(name="Before", value=before.content or "[Empty]", inline=False)
        embed.add_field(name="After", value=after.content or "[Empty]", inline=False)
        
        await log_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        """Log role permission changes."""
        log_channel = self.get_log_channel(before.guild)
        if not log_channel:
            return
        
        embed = Embed(
            title="🛡️ Role Updated",
            color=EmbedColor.ROLE_UPDATE,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Role", value=after.name, inline=True)
        
        if before.permissions != after.permissions:
            embed.add_field(name="Changes", value="Permissions were modified", inline=False)
        
        await log_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Log role changes for members."""
        log_channel = self.get_log_channel(before.guild)
        if not log_channel:
            return
        
        before_roles = set(before.roles)
        after_roles = set(after.roles)
        
        added_roles = after_roles - before_roles
        removed_roles = before_roles - after_roles
        
        if not added_roles and not removed_roles:
            return
        
        embed = Embed(
            title="👥 Member Roles Updated",
            color=EmbedColor.MEMBER_JOIN,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="User", value=format_user_info(before), inline=True)
        
        if added_roles:
            embed.add_field(name="Added Roles", value=", ".join(r.name for r in added_roles), inline=False)
        if removed_roles:
            embed.add_field(name="Removed Roles", value=", ".join(r.name for r in removed_roles), inline=False)
        
        await log_channel.send(embed=embed)
    
    @commands.command(name="security_status", aliases=["ss"])
    @commands.has_permissions(administrator=True)
    async def security_status(self, ctx: commands.Context):
        """Show security monitoring status."""
        embed = Embed(
            title="🛡️ Security Monitoring Status",
            color=EmbedColor.MEMBER_JOIN,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Log Channel", value=f"<#{self.config.log_channel_id}>", inline=True)
        embed.add_field(name="New Account Threshold", value=f"{self.config.new_account_threshold_days} days", inline=True)
        embed.add_field(name="Unverified Role", value=f"<@&{self.config.unverified_role_id}>", inline=True)
        embed.add_field(name="Member Role", value=f"<@&{self.config.member_role_id}>", inline=True)
        
        await ctx.send(embed=embed)


async def setup_security_cog(bot: commands.Bot, config: BotConfig):
    """Setup function for the security logging cog."""
    await bot.add_cog(SecurityLoggingCog(bot, config))
