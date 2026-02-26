"""Test script for bot commands."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import discord
from discord.ext import commands
from core.security_bot.config import BotConfig
from core.security_bot.cogs import setup_verification_cog, setup_security_cog

config = BotConfig.load_from_env()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')
    
    # Load cogs
    await setup_verification_cog(bot, config)
    await setup_security_cog(bot, config)
    
    print('\n📋 Available Commands:')
    print('  !setup_verify (or !sv) - Send verification message')
    print('  !verify_status (or !vs) - Show verification status')
    print('  !security_status (or !ss) - Show security monitoring status')
    print('  !verify_all (or !va) - Verify all unverified members (admin)')
    print('\n🧪 Test these commands in Discord!')
    print('⚠️  Bot will keep running. Press Ctrl+C to stop.\n')

if __name__ == "__main__":
    print("🧪 Testing Bot Commands...")
    bot.run(config.token)
