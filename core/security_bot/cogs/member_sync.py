"""Member Sync Cog - Periodic verification of member roles."""
import discord
from discord.ext import commands, tasks
from discord import Embed
from datetime import datetime, timezone
from typing import Optional
import logging

from ..config import BotConfig
from ..constants import EmbedColor
from ..member_tracker import MemberTracker

logger = logging.getLogger(__name__)


class MemberSyncCog(commands.Cog):
    """Cog for syncing and verifying member roles."""
    
    def __init__(self, bot: commands.Bot, config: BotConfig):
        self.bot = bot
        self.config = config
        self.tracker = MemberTracker()
        self.sync_members.start()
    
    def cog_unload(self):
        """Stop tasks when cog is unloaded."""
        self.sync_members.cancel()
    
    @tasks.loop(hours=6)
    async def sync_members(self):
        """Sync tracked members with actual guild members every 6 hours."""
        try:
            guild = self.bot.get_guild(self.config.guild_id)
            if not guild:
                logger.error(f"Guild {self.config.guild_id} not found")
                return
            
            member_role = guild.get_role(self.config.member_role_id)
            if not member_role:
                logger.error(f"Member role {self.config.member_role_id} not found")
                return
            
            # Collect all members with their role status
            guild_members = []
            for member in guild.members:
                if not member.bot:
                    has_role = member_role in member.roles
                    guild_members.append((member.id, str(member), has_role))
            
            # Sync with tracker
            results = self.tracker.sync_with_guild(guild_members)
            
            logger.info(f"Member sync completed: {results}")
            
            # Send sync report to log channel
            log_channel = guild.get_channel(self.config.log_channel_id)
            if log_channel and (results['added'] > 0 or results['removed'] > 0):
                embed = Embed(
                    title="🔄 Member Sync Report",
                    color=EmbedColor.MEMBER_JOIN,
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="Added to tracking", value=str(results['added']), inline=True)
                embed.add_field(name="Removed from tracking", value=str(results['removed']), inline=True)
                embed.add_field(name="Total verified", value=str(results['total']), inline=True)
                await log_channel.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error during member sync: {e}")
    
    @sync_members.before_loop
    async def before_sync(self):
        """Wait until bot is ready before starting sync."""
        await self.bot.wait_until_ready()
        logger.info("Member sync task started")
    
    @commands.command(name="sync_members", aliases=["sm"])
    @commands.has_permissions(administrator=True)
    async def manual_sync(self, ctx: commands.Context):
        """Manually trigger member sync."""
        await ctx.send("🔄 กำลังซิงค์สมาชิก...")
        
        guild = ctx.guild
        member_role = guild.get_role(self.config.member_role_id)
        
        if not member_role:
            await ctx.send("❌ ไม่พบยศ Member!")
            return
        
        # Collect all members
        guild_members = []
        for member in guild.members:
            if not member.bot:
                has_role = member_role in member.roles
                guild_members.append((member.id, str(member), has_role))
        
        # Sync
        results = self.tracker.sync_with_guild(guild_members)
        
        embed = Embed(
            title="✅ Member Sync Complete",
            color=EmbedColor.VERIFIED,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Added", value=str(results['added']), inline=True)
        embed.add_field(name="Removed", value=str(results['removed']), inline=True)
        embed.add_field(name="Verified", value=str(results['verified']), inline=True)
        embed.add_field(name="Total Tracked", value=str(results['total']), inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="member_stats", aliases=["ms"])
    @commands.has_permissions(administrator=True)
    async def member_stats(self, ctx: commands.Context):
        """Show member tracking statistics."""
        stats = self.tracker.get_stats()
        all_members = self.tracker.get_all_members()
        
        embed = Embed(
            title="📊 Member Tracking Statistics",
            color=EmbedColor.MEMBER_JOIN,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Total Tracked Members", value=str(stats['total_members']), inline=True)
        embed.add_field(name="Last Updated", value=stats['last_updated'] or "Never", inline=True)
        embed.add_field(name="Data File", value=f"`{stats['data_file']}`", inline=False)
        
        # Show recent verifications
        if all_members:
            recent = sorted(
                all_members.items(),
                key=lambda x: x[1].get('last_verified', ''),
                reverse=True
            )[:5]
            
            recent_text = "\n".join([
                f"• {data['username']} (x{data.get('verification_count', 1)})"
                for _, data in recent
            ])
            embed.add_field(name="Recent Verifications", value=recent_text or "None", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="check_member", aliases=["cm"])
    @commands.has_permissions(administrator=True)
    async def check_member(self, ctx: commands.Context, member: discord.Member):
        """Check if a specific member is tracked."""
        member_data = self.tracker.get_member(member.id)
        member_role = ctx.guild.get_role(self.config.member_role_id)
        
        has_role = member_role in member.roles if member_role else False
        
        embed = Embed(
            title=f"🔍 Member Check: {member}",
            color=EmbedColor.VERIFIED if has_role else EmbedColor.WARNING,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="User ID", value=str(member.id), inline=True)
        embed.add_field(name="Has Member Role", value="✅ Yes" if has_role else "❌ No", inline=True)
        embed.add_field(name="Is Tracked", value="✅ Yes" if member_data else "❌ No", inline=True)
        
        if member_data:
            embed.add_field(name="First Verified", value=member_data.get('first_verified', 'Unknown'), inline=True)
            embed.add_field(name="Last Verified", value=member_data.get('last_verified', 'Unknown'), inline=True)
            embed.add_field(name="Verification Count", value=str(member_data.get('verification_count', 0)), inline=True)
        
        await ctx.send(embed=embed)


async def setup_member_sync_cog(bot: commands.Bot, config: BotConfig):
    """Setup function for the member sync cog."""
    await bot.add_cog(MemberSyncCog(bot, config))
