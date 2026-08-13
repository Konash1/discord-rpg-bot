import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
from pymongo import MongoClient
from dotenv import load_dotenv

# Load local environment variables from .env file
load_dotenv()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- MONGODB CONNECTION ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["rpg_bot_db"]
bot.db_players = db["players"]
bot.db_guilds = db["guilds"]

def get_player(user_id):
    uid = str(user_id)
    player = bot.db_players.find_one({"_id": uid})
    if not player:
        default_player = {
            "_id": uid,
            "gold": 200,
            "bank": 0,
            "exp": 0,
            "level": 1,
            "hp": 100,
            "max_hp": 100,
            "base_atk": 10,
            "bonus_atk": 5,
            "weapon": "Wooden Sword (+5 ATK)",
            "weapon_level": 0,
            "armor": "Cloth Armor (+5 HP)",
            "inventory": ["Health Potion"],
            "fish_count": 0,
            "ore_count": 0,
            "crafted_potions": 0,
            "coinflip_wins": 0,
            "dice_wins": 0,
            "slots_played": 0,
            "jackpots": 0,
            "gold_given": 0,
            "commands_used": 0,
            "unlocked_achievements": [],
            "pet": None,
            "last_daily": 0,
            "last_work": 0,
            "last_quest_claim": 0,
            "bounty": 0,
            "guild": None,
            "wins": 0,
            "losses": 0
        }
        bot.db_players.insert_one(default_player)
        return default_player
    return player

def save_player(player):
    bot.db_players.replace_one({"_id": player["_id"]}, player)

bot.get_player = get_player
bot.save_player = save_player

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s) across all modules!")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# --- /info COMMAND ---
@bot.tree.command(name="info", description="View RPG Bot information and system stats")
async def info(interaction: discord.Interaction):
    total_players = bot.db_players.count_documents({})
    active_guilds = bot.db_guilds.count_documents({})
    connected_servers = len(bot.guilds)

    embed = discord.Embed(title="RPG Bot Info", color=0x3498db)
    
    embed.add_field(
        name="Developer",
        value="`Created by k0nash1`",
        inline=False
    )
    
    embed.add_field(
        name="System & Hosting",
        value="• Powered by **Bot Hosting**\n• Database: **Mongo database**",
        inline=False
    )

    embed.add_field(name="Registered Players", value=f"`{total_players}`", inline=True)
    embed.add_field(name="Active Guilds", value=f"`{active_guilds}`", inline=True)
    embed.add_field(name="Connected Servers", value=f"`{connected_servers}`", inline=True)

    await interaction.response.send_message(embed=embed)

# Register Cogs / Modules
async def main():
    async with bot:
        await bot.load_extension("cogs.economy")
        await bot.load_extension("cogs.combat")
        await bot.load_extension("cogs.guilds")
        await bot.load_extension("cogs.minigames")
        await bot.load_extension("cogs.quests")
        
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise ValueError("DISCORD_TOKEN is missing in environment variables!")
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
