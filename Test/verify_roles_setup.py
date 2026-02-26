import discord
import asyncio

TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
GUILD_ID = 1475450344334037063

def load_token(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if "=" in content:
            return content.split("=")[1].strip()
        return content

TOKEN = load_token(TOKEN_FILE)

class RoleSetupClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        guild = self.get_guild(GUILD_ID)
        
        if not guild:
            print(f"Error: Guild with ID {GUILD_ID} not found.")
            await self.close()
            return

        print(f"Found Guild: {guild.name}")
        
        # Check for Unverified role
        unverified_role = discord.utils.get(guild.roles, name="Unverified")
        
        if not unverified_role:
            print("Role 'Unverified' not found. Creating it now...")
            try:
                # Create the role with no permissions by default
                unverified_role = await guild.create_role(
                    name="Unverified",
                    color=discord.Color.default(),
                    reason="Created for 2-step verification system"
                )
                print(f"Successfully created 'Unverified' role! ID: {unverified_role.id}")
            except Exception as e:
                print(f"Failed to create role: {e}")
        else:
            print(f"Found 'Unverified' role! ID: {unverified_role.id}")

        await self.close()

if __name__ == "__main__":
    client = RoleSetupClient()
    client.run(TOKEN)
