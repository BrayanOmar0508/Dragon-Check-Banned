import discord
import os
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from flask import Flask
import threading
from utils import check_ban

# Flask setup
app = Flask(__name__)

@app.route('/')
def home():
    return f"Bot {bot.user} is working" if bot.user else "Bot not ready."

def run_flask():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_flask).start()

# Load environment
load_dotenv()
TOKEN = os.getenv("TOKEN")
APPLICATION_ID = os.getenv("APPLICATION_ID")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

DEFAULT_LANG = "en"
user_languages = {}

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot connected as {bot.user}")

@tree.command(name="lang", description="Change your preferred language (en/fr)")
@app_commands.describe(lang_code="Language code: en or fr")
async def change_language(interaction: discord.Interaction, lang_code: str):
    lang_code = lang_code.lower()
    if lang_code not in ["en", "fr"]:
        await interaction.response.send_message("❌ Invalid language. Available: `en`, `fr`", ephemeral=True)
        return

    user_languages[interaction.user.id] = lang_code
    message = "✅ Language set to English." if lang_code == 'en' else "✅ Langue définie sur le français."
    await interaction.response.send_message(f"{interaction.user.mention} {message}")

@tree.command(name="check", description="Check if a user ID is banned")
@app_commands.describe(user_id="The player's UID to check")
async def check_ban_slash(interaction: discord.Interaction, user_id: str):
    lang = user_languages.get(interaction.user.id, "en")
    print(f"Commande fait par {interaction.user} (lang={lang})")

    if not user_id.isdigit():
        message = {
            "en": f"{interaction.user.mention} ❌ **Invalid UID!**\n➡️ Please use: `/check 123456789`",
            "fr": f"{interaction.user.mention} ❌ **UID invalide !**\n➡️ Veuillez fournir un UID valide sous la forme : `/check 123456789`"
        }
        await interaction.response.send_message(message[lang], ephemeral=True)
        return

    await interaction.response.defer()

    try:
        ban_status = await check_ban(user_id)
    except Exception as e:
        await interaction.followup.send(f"{interaction.user.mention} ⚠️ Error:\n```{str(e)}```")
        return

    if ban_status is None:
        message = {
            "en": f"{interaction.user.mention} ❌ **Could not get information. Please try again later.**",
            "fr": f"{interaction.user.mention} ❌ **Impossible d'obtenir les informations.**\nVeuillez réessayer plus tard."
        }
        await interaction.followup.send(message[lang])
        return

    is_banned = int(ban_status.get("is_banned", 0))
    period = ban_status.get("period", "N/A")
    nickname = ban_status.get("nickname", "NA")
    region = ban_status.get("region", "N/A")
    id_str = f"`{user_id}`"

    if isinstance(period, int):
        period_str = f"more than {period} months" if lang == "en" else f"plus de {period} mois"
    else:
        period_str = "unavailable" if lang == "en" else "indisponible"

    embed = discord.Embed(
        color=0xFF0000 if is_banned else 0x00FF00,
    )

    if is_banned:
        embed.title = "**▌ Banned Account 🛑 **" if lang == "en" else "**▌ Compte banni 🛑 **"
        embed.description = (
            f"**• {'Reason' if lang == 'en' else 'Raison'} :** "
            f"{'This account was confirmed for using cheats.' if lang == 'en' else 'Ce compte a été confirmé comme utilisant des hacks.'}\n"
            f"**• {'Suspension duration' if lang == 'en' else 'Durée de la suspension'} :** {period_str}\n"
            f"**• {'Nickname' if lang == 'en' else 'Pseudo'} :** `{nickname}`\n"
            f"**• {'Player ID' if lang == 'en' else 'ID du joueur'} :** `{id_str}`\n"
            f"**• {'Region' if lang == 'en' else 'Région'} :** `{region}`"
        )
        embed.set_image(url="https://i.ibb.co/wFxTy8TZ/banned.gif")
    else:
        embed.title = "**▌ Clean Account ✅ **" if lang == "en" else "**▌ Compte non banni ✅ **"
        embed.description = (
            f"**• {'Status' if lang == 'en' else 'Statut'} :** "
            f"{'No sufficient evidence of cheat usage on this account.' if lang == 'en' else 'Aucune preuve suffisante pour confirmer l’utilisation de hacks sur ce compte.'}\n"
            f"**• {'Nickname' if lang == 'en' else 'Pseudo'} :** `{nickname}`\n"
            f"**• {'Player ID' if lang == 'en' else 'ID du joueur'} :** `{id_str}`\n"
            f"**• {'Region' if lang == 'en' else 'Région'} :** `{region}`"
        )
        embed.set_image(url="https://i.ibb.co/Kx1RYVKZ/notbanned.gif")

    embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
    embed.set_footer(text="📌  Garena Free Fire")

    await interaction.followup.send(interaction.user.mention, embed=embed)

bot.run(TOKEN)
