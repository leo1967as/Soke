"""Check roles in the server."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import discord
from core.security_bot.config import BotConfig

config = BotConfig.load_from_env()
intents = discord.Intents.default()
intents.guilds = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    guild = client.get_guild(config.guild_id)
    print(f'Guild: {guild.name}')
    print(f'\nSearching for Member role...')
    
    # Find Member role
    member_roles = [r for r in guild.roles if 'member' in r.name.lower()]
    print(f'\nRoles with "member" in name:')
    for role in member_roles:
        print(f'  - {role.name} (ID: {role.id})')
    
    print(f'\nCurrent config:')
    print(f'  BOT_MEMBER_ROLE_ID={config.member_role_id}')
    print(f'  BOT_UNVERIFIED_ROLE_ID={config.unverified_role_id}')
    
    # Check if roles exist
    member_role = guild.get_role(config.member_role_id)
    unverified_role = guild.get_role(config.unverified_role_id)
    
    print(f'\nRole check:')
    print(f'  Member role found: {member_role.name if member_role else "NOT FOUND"}')
    print(f'  Unverified role found: {unverified_role.name if unverified_role else "NOT FOUND"}')
    
    await client.close()

if __name__ == "__main__":
    client.run(config.token)
