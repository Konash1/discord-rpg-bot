import discord
from discord.ext import commands
import os
import asyncio
from pymongo import MongoClient

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- MONGODB CONNECTION ---
MONGO_URI = "mongodb+srv://lol369756_db_user:IpKu376J5NfGvDrX@cluster0.gfuarhe.mongodb.net/?appName=Cluster0"
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
            "pet": None,
            "last_daily": 0,
            "last_work": 0,
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

# Attach helpers to bot instance for Cogs access
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

# Register Cogs / Modules
async def main():
    async with bot:
        await bot.load_extension("cogs.economy")
        await bot.load_extension("cogs.combat") # <--- Loaded Combat Cog
        await bot.start(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    asyncio.run(main())
