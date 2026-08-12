import discord
from discord import app_commands
from discord.ext import commands
import random
import json
import os

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Simple JSON Database Loader/Saver
DATA_FILE = "player_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

player_data = load_data()

def get_player(user_id):
    uid = str(user_id)
    if uid not in player_data:
        player_data[uid] = {
            "gold": 100,
            "exp": 0,
            "level": 1,
            "hp": 100,
            "max_hp": 100,
            "atk": 10,
            "def": 5,
            "weapon": "Wooden Sword (+5 ATK)",
            "inventory": ["Health Potion"],
            "guild": None
        }
        save_data(player_data)
    return player_data[uid]

# Boss Event Storage
global_boss = {"name": "Dragon King", "hp": 500, "max_hp": 500, "reward": 1000}
guilds = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

# --- 1. HUNT FEATURE ---
@bot.tree.command(name="hunt", description="Hunt monsters for EXP, Gold, and Loot!")
async def hunt(interaction: discord.Interaction):
    p = get_player(interaction.user.id)
    
    monsters = [
        {"name": "Wild Slime", "min_gold": 10, "max_gold": 25, "exp": 15},
        {"name": "Goblin Scout", "min_gold": 20, "max_gold": 45, "exp": 30},
        {"name": "Forest Wolf", "min_gold": 35, "max_gold": 70, "exp": 50}
    ]
    
    monster = random.choice(monsters)
    earned_gold = random.randint(monster["min_gold"], monster["max_gold"])
    earned_exp = monster["exp"]
    
    p["gold"] += earned_gold
    p["exp"] += earned_exp
    
    # Level Up Logic
    level_up_msg = ""
    if p["exp"] >= p["level"] * 100:
        p["level"] += 1
        p["atk"] += 5
        p["max_hp"] += 20
        p["hp"] = p["max_hp"]
        level_up_msg = f"\n🎉 **LEVEL UP!** You reached **Level {p['level']}**! (+5 ATK, +20 Max HP)"
    
    save_data(player_data)
    
    embed = discord.Embed(title="⚔️ Monster Hunt", color=discord.Color.green())
    embed.description = (
        f"You encountered a **{monster['name']}** and defeated it!\n"
        f"💰 Earned: **{earned_gold} Gold**\n"
        f"⭐ Earned: **{earned_exp} EXP**"
        f"{level_up_msg}"
    )
    await interaction.response.send_message(embed=embed)

# --- 2. EQUIPMENT, SHOP & INVENTORY ---
@bot.tree.command(name="inventory", description="Check your RPG stats, gear & inventory")
async def inventory(interaction: discord.Interaction):
    p = get_player(interaction.user.id)
    embed = discord.Embed(title=f"🎒 {interaction.user.name}'s Profile & Inventory", color=discord.Color.blue())
    embed.add_field(name="📊 Level & EXP", value=f"Lvl {p['level']} ({p['exp']} EXP)", inline=True)
    embed.add_field(name="💰 Gold", value=f"{p['gold']} G", inline=True)
    embed.add_field(name="⚔️ Weapon", value=p['weapon'], inline=True)
    embed.add_field(name="🛡️ Guild", value=p['guild'] if p['guild'] else "None", inline=True)
    embed.add_field(name="🎒 Items", value=", ".join(p['inventory']) if p['inventory'] else "Empty", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="shop_list", description="View all available items in the Shop")
async def shop_list(interaction: discord.Interaction):
    embed = discord.Embed(title="🛒 RPG Shop Catalog", color=discord.Color.gold())
    embed.add_field(name="🗡️ Iron Sword", value="**Price:** 200 Gold\n**Effect:** +15 ATK", inline=False)
    embed.add_field(name="🧪 Health Potion", value="**Price:** 50 Gold\n**Effect:** Restores HP", inline=False)
    embed.set_footer(text="Use /shop [item] to buy!")
    await interaction.response.send_message(embed=embed)

# Added Slash Choices for auto-completion!
@bot.tree.command(name="shop", description="Buy weapons and potions")
@app_commands.choices(item=[
    app_commands.Choice(name="Iron Sword (200 Gold)", value="iron_sword"),
    app_commands.Choice(name="Health Potion (50 Gold)", value="potion")
])
async def shop(interaction: discord.Interaction, item: app_commands.Choice[str]):
    p = get_player(interaction.user.id)
    shop_items = {
        "iron_sword": {"name": "Iron Sword (+15 ATK)", "price": 200, "atk": 15},
        "potion": {"name": "Health Potion", "price": 50, "type": "potion"}
    }
    
    item_key = item.value
    selected = shop_items[item_key]
    
    if p["gold"] < selected["price"]:
        await interaction.response.send_message("❌ You don't have enough gold!")
        return
        
    p["gold"] -= selected["price"]
    if "atk" in selected:
        p["weapon"] = selected["name"]
        p["atk"] += selected["atk"]
    else:
        p["inventory"].append(selected["name"])
        
    save_data(player_data)
    await interaction.response.send_message(f"🛒 Bought **{selected['name']}**!")

# --- 3. GAMBLING ---
@bot.tree.command(name="coinflip", description="Gamble gold on a coinflip")
@app_commands.choices(choice=[
    app_commands.Choice(name="Heads", value="heads"),
    app_commands.Choice(name="Tails", value="tails")
])
async def coinflip(interaction: discord.Interaction, bet: int, choice: app_commands.Choice[str]):
    p = get_player(interaction.user.id)
    user_choice = choice.value
    
    if bet <= 0 or bet > p["gold"]:
        await interaction.response.send_message("❌ Invalid bet amount!")
        return
        
    outcome = random.choice(["heads", "tails"])
    if user_choice == outcome:
        p["gold"] += bet
        res = f"🎉 It was **{outcome}**! You won **{bet} Gold**!"
    else:
        p["gold"] -= bet
        res = f"💀 It was **{outcome}**! You lost **{bet} Gold**!"
        
    save_data(player_data)
    await interaction.response.send_message(res)

# --- 4. BOSS RAIDS ---
@bot.tree.command(name="boss_attack", description="Raid the server World Boss")
async def boss_attack(interaction: discord.Interaction):
    p = get_player(interaction.user.id)
    if global_boss["hp"] <= 0:
        await interaction.response.send_message("🏆 The boss is already defeated! Wait for respawn.")
        return
        
    damage = random.randint(p["atk"], p["atk"] + 20)
    global_boss["hp"] -= damage
    
    if global_boss["hp"] <= 0:
        global_boss["hp"] = 0
        p["gold"] += global_boss["reward"]
        msg = f"💥 You dealt **{damage} DMG** and landed the **FINAL BLOW** on {global_boss['name']}! You received **{global_boss['reward']} Gold**! 🏆"
        global_boss["hp"] = global_boss["max_hp"] # Respawn
    else:
        msg = f"⚔️ You dealt **{damage} DMG** to {global_boss['name']}! Remaining Boss HP: **{global_boss['hp']}/{global_boss['max_hp']}**"
        
    save_data(player_data)
    await interaction.response.send_message(msg)

# --- 5. GUILD SYSTEM ---
@bot.tree.command(name="guild_create", description="Create a new Guild")
async def guild_create(interaction: discord.Interaction, guild_name: str):
    p = get_player(interaction.user.id)
    if p["guild"]:
        await interaction.response.send_message("❌ You are already in a guild!")
        return
        
    if guild_name in guilds:
        await interaction.response.send_message("❌ Guild name already exists!")
        return
        
    guilds[guild_name] = {"owner": interaction.user.id, "members": [interaction.user.id]}
    p["guild"] = guild_name
    save_data(player_data)
    await interaction.response.send_message(f"🏰 Guild **{guild_name}** created successfully!")

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
