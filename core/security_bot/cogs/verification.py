"""Verification Cog - Handles member verification system."""
import discord
from discord.ext import commands
from discord import Embed
from datetime import datetime, timezone
from typing import Optional
import logging

from ..config import BotConfig
from ..constants import EmbedColor, LogMessages
from ..views import VerifyView

logger = logging.getLogger(__name__)


class VerificationCog(commands.Cog):
    """Cog for managing member verification."""
    
    def __init__(self, bot: commands.Bot, config: BotConfig):
        self.bot = bot
        self.config = config
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Assign Unverified role when member joins."""
        unverified_role = member.guild.get_role(self.config.unverified_role_id)
        
        if not unverified_role:
            logger.warning(f"Unverified role {self.config.unverified_role_id} not found")
            return
        
        try:
            await member.add_roles(unverified_role)
            logger.info(LogMessages.ROLE_ASSIGNED.format(
                role_name="Unverified",
                user_name=member.name,
                user_id=member.id
            ))
        except Exception as e:
            logger.error(LogMessages.ROLE_FAILED.format(
                role_name="Unverified",
                user_name=member.name,
                error=e
            ))
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Register verification view on bot ready."""
        view = VerifyView(
            member_role_id=self.config.member_role_id,
            unverified_role_id=self.config.unverified_role_id,
            log_channel_id=self.config.log_channel_id
        )
        self.bot.add_view(view)
        logger.info(LogMessages.VIEW_REGISTERED.format(view_name="VerifyView (Cog)"))
    
    @commands.command(name="setup_verify", aliases=["sv"])
    @commands.has_permissions(administrator=True)
    async def setup_verify(self, ctx: commands.Context):
        """Send verification message to verify channel."""
        channel = self.bot.get_channel(self.config.verify_channel_id)
        
        if not channel:
            await ctx.send("❌ ไม่พบห้องยืนยันตัวตน!")
            return
        
        embed = Embed(
            title="🛡️ ระบบยืนยันตัวตน (Verification System)",
            description=(
                "ยินดีต้อนรับเข้าสู่ **Sokeberlnwza** ครับ!\n\n"
                "เพื่อความปลอดภัยและความเป็นระเบียบของ Server\n"
                "รบกวนกดปุ่มด้านล่างเพื่อรับบทบาท **Member** และเข้าถึงห้องอื่นๆ ครับ\n\n"
                "⚖️ *การกดปุ่มหมายถึงคุณยอมรับกฎของ Server เรียบร้อยแล้ว*"
            ),
            color=EmbedColor.VERIFIED
        )
        
        view = VerifyView(
            member_role_id=self.config.member_role_id,
            unverified_role_id=self.config.unverified_role_id,
            log_channel_id=self.config.log_channel_id
        )
        
        await channel.send(embed=embed, view=view)
        await ctx.send(f"✅ ส่งข้อความ Verify ไปยังห้อง <#{self.config.verify_channel_id}> เรียบร้อย!")
    
    @commands.command(name="verify_status", aliases=["vs"])
    @commands.has_permissions(administrator=True)
    async def verify_status(self, ctx: commands.Context):
        """Show verification system status."""
        guild = ctx.guild
        unverified_role = guild.get_role(self.config.unverified_role_id)
        member_role = guild.get_role(self.config.member_role_id)
        
        if not unverified_role or not member_role:
            await ctx.send("❌ ไม่พบยศที่ต้องการ!")
            return
        
        unverified_count = len([m for m in guild.members if unverified_role in m.roles])
        member_count = len([m for m in guild.members if member_role in m.roles])
        
        embed = Embed(
            title="📊 Verification System Status",
            color=EmbedColor.MEMBER_JOIN
        )
        embed.add_field(name="Unverified Members", value=str(unverified_count), inline=True)
        embed.add_field(name="Verified Members", value=str(member_count), inline=True)
        embed.add_field(name="Total Members", value=str(guild.member_count), inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="verify_all", aliases=["va"])
    @commands.has_permissions(administrator=True)
    async def verify_all(self, ctx: commands.Context, *, reason: str = "Manual verification"):
        """Verify all unverified members (admin only)."""
        guild = ctx.guild
        unverified_role = guild.get_role(self.config.unverified_role_id)
        member_role = guild.get_role(self.config.member_role_id)
        
        if not unverified_role or not member_role:
            await ctx.send("❌ ไม่พบยศที่ต้องการ!")
            return
        
        unverified_members = [
            m for m in guild.members 
            if unverified_role in m.roles and member_role not in m.roles
        ]
        
        if not unverified_members:
            await ctx.send("✅ ไม่มีสมาชิกที่ต้องยืนยันตัวตน!")
            return
        
        confirm_embed = Embed(
            title="⚠️ Confirm Action",
            description=f"ยืนยันตัวตนให้ {len(unverified_members)} คน?\nเหตุผล: {reason}",
            color=EmbedColor.WARNING
        )
        
        await ctx.send(embed=confirm_embed)


async def setup_verification_cog(bot: commands.Bot, config: BotConfig):
    """Setup function for the verification cog."""
    await bot.add_cog(VerificationCog(bot, config))
