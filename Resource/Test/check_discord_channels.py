import discord
import asyncio
import sys
import os

# Get token from environment or hardcode for test script
TOKEN = "MTQ3NjE4MzYyMTI1NjYwOTgzNA.Gx8a4k.lHDEi4VlVdL_xyDRkuaaz1Yp-xxwKcpMBikNmA"
GUILD_ID = 1475450344334037063

async def check_channels():
    intents = discord.Intents.default()
    # Guilds intent is usually enough to list channels if joined
    intents.guilds = True 
    
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"--- Logged in as {client.user} ---")
        try:
            guild = client.get_guild(GUILD_ID)
            if not guild:
                print(f"Guild {GUILD_ID} not found in cache, fetching...")
                guild = await client.fetch_guild(GUILD_ID)
            
            print(f"Guild Name: {guild.name}")
            print(f"Listing channels for Guild ID: {GUILD_ID}")
            
            channels = await guild.fetch_channels()
            
            # Sort channels by type and position
            channels = sorted(channels, key=lambda x: (str(x.type), x.position))
            
            categories = [c for c in channels if isinstance(c, discord.CategoryChannel)]
            other_channels = [c for c in channels if not isinstance(c, discord.CategoryChannel)]
            
            print("\nCategories:")
            for cat in categories:
                print(f"[Category] {cat.name} (ID: {cat.id})")
            
            print("\nChannels:")
            for ch in other_channels:
                category_name = ch.category.name if ch.category else "No Category"
                print(f"[{ch.type}] {ch.name} (ID: {ch.id}) - Category: {category_name}")
                
        except discord.Forbidden:
            print(f"Error: No permission to access guild {GUILD_ID} or its channels.")
        except discord.NotFound:
            print(f"Error: Guild {GUILD_ID} not found.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await client.close()

    try:
        await client.start(TOKEN)
    except discord.LoginFailure:
        print("Error: Invalid Token.")
    except Exception as e:
        print(f"Login Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_channels())
