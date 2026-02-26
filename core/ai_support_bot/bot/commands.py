"""Admin commands for the support bot."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord import app_commands

if TYPE_CHECKING:
    from core.ai_support_bot.bot.client import SokeberSupportBot

logger = logging.getLogger("ai_support_bot.bot.commands")


class AdminCommands(app_commands.Group):
    """Admin-only slash commands for bot management.

    Commands:
        /admin refresh_kb  — Force re-index the knowledge base.
        /admin clear_cache — Clear the answer cache.
        /admin status      — Show bot health status.
    """

    def __init__(self, bot: SokeberSupportBot):
        super().__init__(name="admin", description="Bot administration commands")
        self.bot = bot

    @app_commands.command(name="refresh_kb", description="Force re-index the knowledge base")
    @app_commands.checks.has_permissions(administrator=True)
    async def refresh_kb(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if self.bot.context_retriever and hasattr(self.bot.context_retriever, "force_refresh"):
            try:
                await self.bot.context_retriever.force_refresh()
                await interaction.followup.send("✅ Knowledge base refreshed.", ephemeral=True)
                logger.info(f"KB refresh triggered by {interaction.user}")
            except Exception as e:
                await interaction.followup.send(f"❌ Refresh failed: {e}", ephemeral=True)
                logger.error(f"KB refresh failed: {e}")
        else:
            await interaction.followup.send("⚠️ Context retriever not configured.", ephemeral=True)

    @app_commands.command(name="clear_cache", description="Clear the answer cache")
    @app_commands.checks.has_permissions(administrator=True)
    async def clear_cache(self, interaction: discord.Interaction):
        count = self.bot.answer_cache.clear()
        await interaction.response.send_message(
            f"✅ Cache cleared ({count} entries removed).",
            ephemeral=True,
        )
        logger.info(f"Cache cleared by {interaction.user}: {count} entries")

    @app_commands.command(name="status", description="Show bot health status")
    @app_commands.checks.has_permissions(administrator=True)
    async def status(self, interaction: discord.Interaction):
        cache_size = self.bot.answer_cache.size()
        guilds = len(self.bot.guilds)
        latency = round(self.bot.latency * 1000, 1)

        embed = discord.Embed(
            title="🤖 Bot Status",
            color=discord.Color.green(),
        )
        embed.add_field(name="Latency", value=f"{latency}ms", inline=True)
        embed.add_field(name="Servers", value=str(guilds), inline=True)
        embed.add_field(name="Cache Size", value=str(cache_size), inline=True)
        embed.add_field(name="Environment", value=self.bot.config.environment, inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)
