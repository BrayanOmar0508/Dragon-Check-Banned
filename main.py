import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
import os
from dotenv import load_dotenv
from flask import Flask
import threading

load_dotenv()

TOKEN = os.getenv("TOKEN")
GUILD_ID = discord.Object(id=int(os.getenv("1323126226759450634")))  # Optional: For faster slash command registration

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Flask setup
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# Run Flask in a separate thread
threading.Thread(target=run_flask).start()

# Your async check_ban function
async def check_ban(uid: str):
    api_url = f"https://api-check-ban.up.railway.app/check_ban/{uid}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status != 200:
                    print(f"[WARN] API returned status code {response.status}")
                    return None

                response_data = await response.json()

                if response_data.get("status") == 200:
                    data = response_data.get("data", {})
                    return {
                        "is_banned": data.get("is_banned", 0),
                        "nickname": data.get("nickname", ""),
                        "period": data.get("period", 0),
                        "region": data.get("region", 0)
                    }
                else:
                    print(f"[INFO] API error: {response_data.get('message', 'Unknown error')}")
                    return None

    except aiohttp.ClientError as e:
        print(f"[ERROR] HTTP request failed: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

    return None

# Slash command
@bot.tree.command(name="check", description="Check if a UID is banned")
@app_commands.describe(uid="The user ID to check")
async def check(interaction: discord.Interaction, uid: str):
    await interaction.response.defer()

    result = await check_ban(uid)
    
    if result is None:
        await interaction.followup.send("❌ Unable to check ban status or invalid UID.")
        return

    if result["is_banned"]:
        message = (
            f"🚫 **User is BANNED**\n"
            f"**Nickname:** {result['nickname']}\n"
            f"**Region:** {result['region']}\n"
            f"**Ban Period:** {result['period']} days"
        )
    else:
        message = (
            f"✅ **User is NOT banned**\n"
            f"**Nickname:** {result['nickname']}\n"
            f"**Region:** {result['region']}"
        )

    await interaction.followup.send(message)

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")
    try:
        await bot.tree.sync(guild=GUILD_ID)  # Faster dev sync, optional
        print("Slash commands synced.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# Run the bot
bot.run(TOKEN)
