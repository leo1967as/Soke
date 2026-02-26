"""Main Security Bot - Entry point for the modular Discord bot."""
import discord
from discord.ext import commands
from discord import Embed
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

from .config import BotConfig
from .cogs import setup_verification_cog, setup_security_cog, setup_member_sync_cog
from .views import VerifyView
from .constants import EmbedColor, LogMessages
from .logger import setup_logger

logger = setup_logger("security_bot", log_to_file=True)


class SecurityBot(commands.Bot):
    """Main Security Bot class with modular cog loading."""
    
    def __init__(self, config: BotConfig):
        self.config = config
        
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.guilds = True
        intents.moderation = True
        
        super().__init__(command_prefix="!", intents=intents)
    
    async def setup_hook(self):
        """Setup hook for registering cogs and views."""
        logger.info(LogMessages.BOT_STARTING)
        
        try:
            await setup_verification_cog(self, self.config)
            logger.info(LogMessages.COG_LOADED.format(cog_name="VerificationCog"))
        except Exception as e:
            logger.error(LogMessages.COG_FAILED.format(cog_name="VerificationCog", error=e))
        
        try:
            await setup_security_cog(self, self.config)
            logger.info(LogMessages.COG_LOADED.format(cog_name="SecurityLoggingCog"))
        except Exception as e:
            logger.error(LogMessages.COG_FAILED.format(cog_name="SecurityLoggingCog", error=e))
        
        try:
            await setup_member_sync_cog(self, self.config)
            logger.info(LogMessages.COG_LOADED.format(cog_name="MemberSyncCog"))
        except Exception as e:
            logger.error(LogMessages.COG_FAILED.format(cog_name="MemberSyncCog", error=e))
        
        view = VerifyView(
            member_role_id=self.config.member_role_id,
            unverified_role_id=self.config.unverified_role_id,
            log_channel_id=self.config.log_channel_id
        )
        self.add_view(view)
        logger.info(LogMessages.VIEW_REGISTERED.format(view_name="VerifyView"))
    
    async def on_ready(self):
        """Called when bot is ready."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")
        logger.info(LogMessages.BOT_READY)
        
        # Send online notification to log channel
        guild = self.get_guild(self.config.guild_id)
        if guild:
            log_channel = guild.get_channel(self.config.log_channel_id)
            if log_channel:
                embed = Embed(
                    title="🟢 Bot Online",
                    description=f"**{self.user.name}** is now online and monitoring the server.",
                    color=EmbedColor.BOT_STATUS,
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="Bot ID", value=str(self.user.id), inline=True)
                embed.add_field(name="Guilds", value=str(len(self.guilds)), inline=True)
                embed.set_thumbnail(url=self.user.display_avatar.url)
                await log_channel.send(embed=embed)
                logger.info("Sent online notification to log channel")
    
    async def on_error(self, event_method: str, *args, **kwargs):
        """Global error handler."""
        logger.error(f"Error in {event_method}: {sys.exc_info()}")
    
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Command error handler."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้!")
        elif isinstance(error, commands.CommandNotFound):
            pass
        else:
            logger.error(f"Command error: {error}")
            await ctx.send(f"❌ เกิดข้อผิดพลาด: {error}")


async def run_bot(config: BotConfig):
    """Run the security bot with given configuration."""
    bot = SecurityBot(config)
    
    try:
        await bot.start(config.token)
    except KeyboardInterrupt:
        logger.info(LogMessages.BOT_SHUTDOWN)
        
        # Send offline notification
        try:
            guild = bot.get_guild(config.guild_id)
            if guild:
                log_channel = guild.get_channel(config.log_channel_id)
                if log_channel:
                    embed = Embed(
                        title="🔴 Bot Offline",
                        description=f"**{bot.user.name}** is going offline.",
                        color=EmbedColor.ERROR,
                        timestamp=datetime.now(timezone.utc)
                    )
                    await log_channel.send(embed=embed)
        except:
            pass
        
        await bot.close()
    except Exception as e:
        logger.error(f"Bot error: {e}")
        
        # Send error notification
        try:
            guild = bot.get_guild(config.guild_id)
            if guild:
                log_channel = guild.get_channel(config.log_channel_id)
                if log_channel:
                    embed = Embed(
                        title="⚠️ Bot Error",
                        description=f"**{bot.user.name}** encountered an error and is shutting down.\n\n```{str(e)[:500]}```",
                        color=EmbedColor.ERROR,
                        timestamp=datetime.now(timezone.utc)
                    )
                    await log_channel.send(embed=embed)
        except:
            pass
        
        await bot.close()
        raise


def main():
    """Main entry point."""
    try:
        config = BotConfig.load_from_env()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    try:
        asyncio.run(run_bot(config))
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
