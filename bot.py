import discord
import os
from discord import app_commands
from discord.ext import commands
import random
import json

intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Sync slash commands with Discord on startup
        await self.tree.sync()
        print("⚡ Slash commands synced!")

bot = MyBot()

DATA_FILE = "data.json"
players = {}

# 1. Load Data
def load_data():
    global players
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            players = {int(k): v for k, v in data.items()}
            print("💾 Player data loaded!")
    else:
        players = {}

# 2. Save Data
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(players, f, indent=4)

WEAPONS = {
    "Iron Sword": {"cost": 100, "attack": 25},
    "Dragon Slayer": {"cost": 300, "attack": 60},
    "Excalibur": {"cost": 750, "attack": 120}
}

def get_player(user_id):
    if user_id not in players:
        players[user_id] = {
            "hp": 100, 
            "max_hp": 100, 
            "gold": 50, 
            "weapon": "Fists", 
            "attack": 10,
            "level": 1,
            "exp": 0
        }
        save_data()
    
    # Ensure existing players get level/exp keys if missing
    player = players[user_id]
    if "level" not in player: player["level"] = 1
    if "exp" not in player: player["exp"] = 0
    return player

def add_exp(player, amount):
    """Handles leveling up and increasing stats."""
    player["exp"] += amount
    exp_needed = player["level"] * 50  # Level 1 needs 50 EXP, Level 2 needs 100 EXP, etc.
    
    leveled_up = False
    if player["exp"] >= exp_needed:
        player["level"] += 1
        player["exp"] -= exp_needed
        player["max_hp"] += 20
        player["hp"] = player["max_hp"]  # Full heal on level up
        player["attack"] += 5
        leveled_up = True
        
    return leveled_up

@bot.event
async def on_ready():
    load_data()
    print(f"Logged in as {bot.user.name}")
    print("Bot with Slash Commands & EXP is online!")

# --- SLASH COMMANDS ---

@bot.tree.command(name="stats", description="View your player RPG stats")
async def stats(interaction: discord.Interaction):
    player = get_player(interaction.user.id)
    exp_needed = player["level"] * 50
    
    embed = discord.Embed(title=f"⚔️ {interaction.user.name}'s Profile", color=discord.Color.gold())
    embed.add_field(name="⭐ Level", value=f"{player['level']}", inline=True)
    embed.add_field(name="✨ EXP", value=f"{player['exp']}/{exp_needed}", inline=True)
    embed.add_field(name="❤️ HP", value=f"{player['hp']}/{player['max_hp']}", inline=True)
    embed.add_field(name="💰 Gold", value=f"{player['gold']}", inline=True)
    embed.add_field(name="🗡️ Weapon", value=f"{player['weapon']} (+{player['attack']} ATK)", inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="shop", description="View the weapon shop")
async def shop(interaction: discord.Interaction):
    embed = discord.Embed(title="🏪 Weapon Shop", description="Use `/buy <weapon_name>` to purchase!", color=discord.Color.blue())
    for name, info in WEAPONS.items():
        embed.add_field(name=f"🗡️ {name}", value=f"Cost: **{info['cost']} Gold** | ATK: **+{info['attack']}**", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="buy", description="Buy a weapon from the shop")
async def buy(interaction: discord.Interaction, weapon_name: str):
    player = get_player(interaction.user.id)
    formatted_name = weapon_name.title()
    
    if formatted_name not in WEAPONS:
        await interaction.response.send_message("❌ That weapon doesn't exist!", ephemeral=True)
        return
        
    weapon = WEAPONS[formatted_name]
    if player["gold"] < weapon["cost"]:
        await interaction.response.send_message(f"❌ You need **{weapon['cost']} Gold**!", ephemeral=True)
        return
        
    player["gold"] -= weapon["cost"]
    player["weapon"] = formatted_name
    player["attack"] = weapon["attack"]
    save_data()
    
    await interaction.response.send_message(f"🎉 {interaction.user.mention} bought **{formatted_name}**!")

@bot.tree.command(name="hunt", description="Hunt wild monsters for Gold and EXP")
async def hunt(interaction: discord.Interaction):
    player = get_player(interaction.user.id)
    if player["hp"] <= 0:
        await interaction.response.send_message("💀 You are dead! Use `/heal` first.")
        return

    monsters = ["Goblin", "Slime", "Wild Boar"]
    monster = random.choice(monsters)
    
    damage_taken = random.randint(5, 15)
    gold_earned = random.randint(15, 35) + (player["attack"] // 2)
    exp_earned = random.randint(15, 25)
    
    player["hp"] -= damage_taken
    
    if player["hp"] <= 0:
        player["hp"] = 0
        save_data()
        await interaction.response.send_message(f"⚔️ Fought a **{monster}** and got knocked out! 💀")
    else:
        player["gold"] += gold_earned
        leveled_up = add_exp(player, exp_earned)
        save_data()
        
        msg = f"⚔️ Defeated **{monster}**!\n💰 Earned **{gold_earned} Gold** | ✨ **+{exp_earned} EXP**\n❤️ HP left: {player['hp']}/{player['max_hp']}"
        if leveled_up:
            msg += f"\n\n🎉 **LEVEL UP!** You are now **Level {player['level']}**! (+20 Max HP, +5 Base ATK)"
        
        await interaction.response.send_message(msg)

@bot.tree.command(name="boss", description="Fight the Red Dragon Boss")
async def boss(interaction: discord.Interaction):
    player = get_player(interaction.user.id)
    if player["hp"] <= 0:
        await interaction.response.send_message("💀 You are dead! Use `/heal` first.")
        return

    boss_hp = 150
    boss_name = "🔥 Red Dragon"
    boss_damage = random.randint(30, 60)
    player_damage = player["attack"] + random.randint(10, 30)
    
    player["hp"] -= boss_damage
    
    if player_damage >= boss_hp:
        reward = 300
        exp_reward = 100
        player["gold"] += reward
        leveled_up = add_exp(player, exp_reward)
        save_data()
        
        msg = f"🏆 **BOSS DEFEATED!** Slayed **{boss_name}**!\n💰 +{reward} Gold | ✨ +{exp_reward} EXP"
        if leveled_up:
            msg += f"\n🎉 **LEVEL UP!** You reached **Level {player['level']}**!"
        await interaction.response.send_message(msg)
    else:
        if player["hp"] <= 0:
            player["hp"] = 0
            save_data()
            await interaction.response.send_message(f"🔥 **{boss_name}** incinerated you for **{boss_damage}** damage! 💀")
        else:
            save_data()
            await interaction.response.send_message(f"🛡️ Fought **{boss_name}**! Dealt **{player_damage}/{boss_hp}** DMG, took **{boss_damage}** DMG.")

@bot.tree.command(name="heal", description="Restore full HP for 30 Gold")
async def heal(interaction: discord.Interaction):
    player = get_player(interaction.user.id)
    cost = 30
    if player["gold"] < cost:
        await interaction.response.send_message(f"❌ You need **{cost} Gold** to heal!", ephemeral=True)
        return
    player["gold"] -= cost
    player["hp"] = player["max_hp"]
    save_data()
    await interaction.response.send_message(f"✨ {interaction.user.mention} restored full health!")

# Get token securely from environment variable
TOKEN = os.getenv("DISCORD_TOKEN")

bot.run(TOKEN)