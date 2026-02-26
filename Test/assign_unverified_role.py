import discord
import asyncio

TOKEN_FILE = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
GUILD_ID = 1475450344334037063
MEMBER_ROLE_ID = 1476201289129132092
UNVERIFIED_ROLE_ID = 1476208022945530090

def load_token(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if "=" in content:
            return content.split("=")[1].strip()
        return content

TOKEN = load_token(TOKEN_FILE)

class RetroVerifyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True # Required to iterate over all members
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

        if not unverified_role or not member_role:
            print("Error: Could not find Unverified or Member role. Check IDs.")
            await self.close()
            return

        print("Fetching all members (this might take a few seconds)...")
        
        assigned_count = 0
        skipped_count = 0
        processed_count = 0
        
        print("Starting to scan members and assign Unverified role to those without Member role...")

        try:
            async for member in guild.fetch_members(limit=None):
                processed_count += 1
                if processed_count % 10 == 0:
                    print(f"Processed {processed_count} members so far...")

                if member.bot:
                    continue # Skip bots

                # If they don't have the Member role, they need to be verified
                if member_role not in member.roles:
                    # If they already have Unverified, skip
                    if unverified_role in member.roles:
                        skipped_count += 1
                    else:
                        try:
                            await member.add_roles(unverified_role)
                            print(f"Assigned Unverified to: {member.name} ({member.id})")
                            assigned_count += 1
                            await asyncio.sleep(0.5) # Prevent ratelimits
                        except Exception as e:
                            print(f"Failed to assign role to {member.name}: {e}")
                else:
                    # They are a verified member. Ensure they don't have the Unverified role by accident.
                    if unverified_role in member.roles:
                        try:
                            await member.remove_roles(unverified_role)
                            print(f"Removed Unverified from fully verified member: {member.name}")
                            await asyncio.sleep(0.5)
                        except Exception as e:
                            print(f"Failed to remove role from {member.name}: {e}")
        except Exception as e:
            print(f"Error fetching members: {e}")

        print("\n--- Summary ---")
        print(f"Successfully assigned Unverified to: {assigned_count} users")
        print(f"Skipped (already have Unverified): {skipped_count} users")
        print("Script finished!")
        await self.close()

if __name__ == "__main__":
    client = RetroVerifyClient()
    client.run(TOKEN)
