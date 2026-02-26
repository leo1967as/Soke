import discord
import asyncio

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

class PermissionSetupClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        guild = self.get_guild(GUILD_ID)
        
        if not guild:
            print(f"Error: Guild with ID {GUILD_ID} not found.")
            await self.close()
            return

        unverified_role = guild.get_role(UNVERIFIED_ROLE_ID)
        member_role = guild.get_role(MEMBER_ROLE_ID)
        everyone_role = guild.default_role
        verify_channel = guild.get_channel(VERIFY_CHAN_ID)

        print(f"unverified_role: {unverified_role}")
        print(f"member_role: {member_role}")
        print(f"everyone_role: {everyone_role}")
        print(f"verify_channel: {verify_channel}")

        if not all([unverified_role, member_role, verify_channel, everyone_role]):
            print("Error: Missing one or more roles or channels. Please check IDs.")
            await self.close()
            return

        print("Setting up channel permissions...")
        
        for channel in guild.channels:
            # Skip adjusting threads, just focus on Text/Voice/Category
            if isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel)):
                try:
                    is_verify_channel_or_category = (
                        channel.id == VERIFY_CHAN_ID or 
                        (hasattr(channel, 'category') and channel.category and channel.category.id == verify_channel.category_id)
                    )
                    
                    if is_verify_channel_or_category:
                        # Inside Verification Category
                        await channel.set_permissions(everyone_role, view_channel=False)
                        await channel.set_permissions(unverified_role, view_channel=True, send_messages=False, add_reactions=False)
                        await channel.set_permissions(member_role, view_channel=False) # Hide from verified members to keep it clean, optional
                    else:
                        # Regular Channels (Main, Social, etc.)
                        await channel.set_permissions(everyone_role, view_channel=False)
                        await channel.set_permissions(unverified_role, view_channel=False)
                        await channel.set_permissions(member_role, view_channel=True)
                        
                    print(f"Updated permissions for: {channel.name}")
                    
                except discord.errors.Forbidden:
                    print(f"Missing permissions to update: {channel.name}")
                except Exception as e:
                    print(f"Error updating {channel.name}: {e}")

        print("Finished setting up permissions via script.")
        await self.close()

if __name__ == "__main__":
    client = PermissionSetupClient()
    client.run(TOKEN)
