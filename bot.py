import discord
from discord import app_commands
from discord.ext import commands
import random
import os
import time
from pymongo import MongoClient

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- MONGODB SETUP ---
# ⚠️ REPLACE <db_password> WITH YOUR ACTUAL DATABASE PASSWORD BELOW ⚠️
MONGO_URI = "mongodb+srv://lol369756_db_user:IpKu376J5NfGvDrX@cluster0.gfuarhe.mongodb.net/?appName=Cluster0"

client = MongoClient(MONGO_URI)
db = client["rpg_bot_db"]
players_col = db["players"]

def get_player(user_id):
    uid = str(user_id)
    player = players_col.find_one({"_id": uid})
    
    if not player:
        default_player = {
            "_id": uid,
            "gold": 100,
            "exp": 0,
            "level": 1,
            "hp": 100,
            "max_hp": 100,
            "atk": 10,
            "def": 5,
            "weapon": "Wooden Sword (+5 ATK)",
            "weapon_level": 0,
            "inventory": ["Health Potion"],
            "fish_count": 0,
            "pet": None,
            "last_daily": 0,
            "bounty": 0,
            "guild": None
        }
        players_col.insert_one(default_player)
        return default_player
    return player

def save_player(player):
    players_col.replace_one({"_id": player["_id"]}, player)

global_boss = {"name": "Dragon King", "hp": 500, "max_hp": 500, "reward": 1000}

# Visual HP Bar Generator
def make_hp_bar(current, max_val, length=10):
    percent = max(0, min(1.0, current / max_val))
    filled = int(length * percent)
    return "█" * filled + "░" * (length - filled)

# --- CLEAN EMBED GENERATORS ---
def build_hunt_embed(user_id, username):
    p = get_player(user_id)
    
    monsters = [
        {"name": "Wild Slime 🧪", "min_gold": 10, "max_gold": 25, "exp": 15},
        {"name": "Goblin Scout 👺", "min_gold": 20, "max_gold": 45, "exp": 30},
        {"name": "Forest Wolf 🐺", "min_gold": 35, "max_gold": 70, "exp": 50}
    ]
    
    monster = random.choice(monsters)
    earned_gold = random.randint(monster["min_gold"], monster["max_gold"])
    earned_exp = monster["exp"]
    
    if p["pet"]:
        earned_exp = int(earned_exp * 1.5)

    p["gold"] += earned_gold
    p["exp"] += earned_exp
    
    lvl_up_text = ""
    if p["exp"] >= p["level"] * 100:
        p["level"] += 1
        p["atk"] += 5
        p["max_hp"] += 20
        p["hp"] = p["max_hp"]
        lvl_up_text = f"\n\n🎉 **LEVEL UP!** You are now **Level {p['level']}**! *(+5 ATK, +20 HP)*"
    
    save_player(p)
    
    embed = discord.Embed(
        title="⚔️ Monster Encounter",
        description=f"**{username}** engaged in battle and defeated a **{monster['name']}**!{lvl_up_text}",
        color=0x2ecc71
    )
    embed.add_field(name="💰 Gold Earned", value=f"`+{earned_gold} G`", inline=True)
    embed.add_field(name="⭐ EXP Earned", value=f"`+{earned_exp} EXP`", inline=True)
    embed.set_footer(text=f"Level {p['level']}  •  Total Gold: {p['gold']} G")
    return embed

def build_profile_embed(user_id, username):
    p = get_player(user_id)
    embed = discord.Embed(
        title=f"🛡️ Character Profile — {username}",
        color=0x3498db
    )
    embed.add_field(name="📊 Stats", value=f"**Level:** {p['level']}\n**EXP:** {p['exp']}/{p['level']*100}\n**ATK:** {p['atk']}", inline=True)
    embed.add_field(name="💼 Economy", value=f"**Gold:** {p['gold']} G\n**Bounty:** {p['bounty']} G\n**Guild:** {p['guild'] or 'None'}", inline=True)
    embed.add_field(name="⚔️ Equipment", value=f"**Weapon:** {p['weapon']} `(+{p['weapon_level']})`\n**Pet:** {p['pet'] or 'None'}\n**Fish:** {p['fish_count']} 🐟", inline=False)
    
    items = ", ".join([f"`{i}`" for i in p['inventory']]) if p['inventory'] else "*Empty*"
    embed.add_field(name="🎒 Backpack", value=items, inline=False)
    return embed

def build_boss_embed():
    hp_pct = int((global_boss['hp'] / global_boss['max_hp']) * 100)
    bar = make_hp_bar(global_boss['hp'], global_boss['max_hp'])
    embed = discord.Embed(
        title=f"🔥 World Boss: {global_boss['name']}",
        description=f"**Health:** `{global_boss['hp']}/{global_boss['max_hp']}` ({hp_pct}%)\n`[{bar}]`\n\nUse `/boss_attack` to join the raid!",
        color=0xe74c3c
    )
    embed.add_field(name="🏆 Bounty Reward", value=f"`{global_boss['reward']} Gold` for the final blow!", inline=False)
    return embed

# --- INTERACTIVE UI ---
class RPGNavSelect(discord.ui.Select):
    def __init__(self, owner_id):
        self.owner_id = owner_id
        options = [
            discord.SelectOption(label="Hunt Again", value="hunt", emoji="⚔️", description="Fight another monster"),
            discord.SelectOption(label="Profile & Gear", value="profile", emoji="🎒", description="View stats and inventory"),
            discord.SelectOption(label="World Boss", value="boss", emoji="🔥", description="Check World Boss health"),
        ]
        super().__init__(placeholder="📂 Navigate RPG Menu...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Start your own session with `/hunt`!", ephemeral=True)
            return

        val = self.values[0]
        if val == "hunt":
            embed = build_hunt_embed(interaction.user.id, interaction.user.name)
        elif val == "profile":
            embed = build_profile_embed(interaction.user.id, interaction.user.name)
        elif val == "boss":
            embed = build_boss_embed()

        await interaction.response.edit_message(embed=embed)

class RPGMenuView(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=120)
        self.add_item(RPGNavSelect(owner_id))

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

# --- COMMANDS ---
@bot.tree.command(name="hunt", description="Hunt monsters with interactive menu")
async def hunt(interaction: discord.Interaction):
    embed = build_hunt_embed(interaction.user.id, interaction.user.name)
    view = RPGMenuView(owner_id=interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="profile", description="Check your RPG character profile")
async def profile(interaction: discord.Interaction):
    embed = build_profile_embed(interaction.user.id, interaction.user.name)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="dungeon", description="Explore dungeon floors")
async def dungeon(interaction: discord.Interaction, floor: int):
    p = get_player(interaction.user.id)
    if floor < 1 or floor > 5:
        await interaction.response.send_message("❌ Floor must be between 1 and 5!", ephemeral=True)
        return
        
    success_rate = 90 - (floor * 15)
    if random.randint(1, 100) <= success_rate:
        reward = floor * 150
        p["gold"] += reward
        save_player(p)
        embed = discord.Embed(title=f"🏰 Dungeon Floor {floor} Cleared!", description=f"You successfully cleared the floor and retrieved **+{reward} Gold**!", color=0x2ecc71)
    else:
        embed = discord.Embed(title=f"💀 Dungeon Floor {floor} Failed!", description="The monsters overwhelmed you! You escaped back to safety empty-handed.", color=0xe74c3c)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="daily", description="Claim daily Gold reward")
async def daily(interaction: discord.Interaction):
    p = get_player(interaction.user.id)
    now = time.time()
    if now - p["last_daily"] < 86400:
        await interaction.response.send_message("⏳ Daily reward is available once every 24 hours!", ephemeral=True)
        return
        
    p["gold"] += 250
    p["last_daily"] = now
    save_player(p)
    embed = discord.Embed(title="🎁 Daily Reward Claimed", description="You received **+250 Gold**!", color=0xf1c40f)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="pet_buy", description="Buy a pet companion (+50% EXP boost)")
async def pet_buy(interaction: discord.Interaction):
    p = get_player(interaction.user.id)
    if p["gold"] < 500:
        await interaction.response.send_message("❌ Pets cost 500 Gold!", ephemeral=True)
        return
    p["gold"] -= 500
    p["pet"] = "Baby Dragon 🐉"
    save_player(p)
    embed = discord.Embed(title="🐶 New Pet Adopted!", description="You adopted a **Baby Dragon 🐉**! Grants **+50% bonus EXP** from hunts.", color=0x9b59b6)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="skill", description="Use Fireball spell")
async def skill(interaction: discord.Interaction):
    p = get_player(interaction.user.id)
    dmg = p["atk"] * 2
    embed = discord.Embed(title="🔥 Skill Activated: Fireball", description=f"You cast Fireball dealing **{dmg} Damage**!", color=0xe67e22)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="fish", description="Go fishing for raw materials")
async def fish(interaction: discord.Interaction):
    p = get_player(interaction.user.id)
    p["fish_count"] += 1
    save_player(p)
    embed = discord.Embed(title="🎣 Fishing", description=f"You caught a fresh fish! Total Fish: **{p['fish_count']}**", color=0x3498db)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="craft", description="Craft a Health Potion using 3 Fish")
async def craft(interaction: discord.Interaction):
    p = get_player(interaction.user.id)
    if p["fish_count"] < 3:
        await interaction.response.send_message("❌ You need 3 Fish to craft a Potion!", ephemeral=True)
        return
    p["fish_count"] -= 3
    p["inventory"].append("Health Potion")
    save_player(p)
    embed = discord.Embed(title="🧪 Crafting Complete", description="Crafted **1x Health Potion** from 3 Fish!", color=0x2ecc71)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="forge", description="Upgrade your weapon")
async def forge(interaction: discord.Interaction):
    p = get_player(interaction.user.id)
    cost = (p["weapon_level"] + 1) * 100
    if p["gold"] < cost:
        await interaction.response.send_message(f"❌ You need **{cost} Gold** to forge an upgrade!", ephemeral=True)
        return
        
    p["gold"] -= cost
    if random.randint(1, 100) <= 75:
        p["weapon_level"] += 1
        p["atk"] += 5
        embed = discord.Embed(title="✨ Forge Success!", description=f"Weapon upgraded to **+{p['weapon_level']}** *(+5 ATK)*!", color=0xf1c40f)
    else:
        embed = discord.Embed(title="💥 Forge Failed!", description="The upgrade failed and your materials were consumed.", color=0xe74c3c)
    save_player(p)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="pvp", description="Duel another member for gold")
async def pvp(interaction: discord.Interaction, opponent: discord.User, bet: int):
    p1 = get_player(interaction.user.id)
    p2 = get_player(opponent.id)
    if p1["gold"] < bet or p2["gold"] < bet:
        await interaction.response.send_message("❌ One of you doesn't have enough gold for that bet!", ephemeral=True)
        return
    
    winner = random.choice([interaction.user, opponent])
    loser = opponent if winner == interaction.user else interaction.user
    
    w_p = get_player(winner.id)
    l_p = get_player(loser.id)
    w_p["gold"] += bet
    l_p["gold"] -= bet
    save_player(w_p)
    save_player(l_p)
    
    embed = discord.Embed(title="⚔️ PvP Duel Results", description=f"**{winner.name}** defeated **{loser.name}** in combat and took **{bet} Gold**!", color=0x9b59b6)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="bounty", description="Set a bounty on a player")
async def bounty(interaction: discord.Interaction, target: discord.User, amount: int):
    p1 = get_player(interaction.user.id)
    p2 = get_player(target.id)
    if p1["gold"] < amount:
        await interaction.response.send_message("❌ You don't have enough gold!", ephemeral=True)
        return
    p1["gold"] -= amount
    p2["bounty"] += amount
    save_player(p1)
    save_player(p2)
    embed = discord.Embed(title="🎯 Bounty Placed", description=f"Placed a **{amount} Gold** bounty on {target.name}!", color=0xe74c3c)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="leaderboard", description="View top richest players")
async def leaderboard(interaction: discord.Interaction):
    top_players = list(players_col.find().sort("gold", -1).limit(5))
    text = ""
    for idx, data in enumerate(top_players, 1):
        text += f"**#{idx}** <@{data['_id']}> — `{data['gold']} G` *(Lvl {data['level']})*\n"
    embed = discord.Embed(title="🏆 Gold Leaderboard", description=text or "No data yet.", color=0xf1c40f)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="shop", description="Buy items")
@app_commands.choices(item=[
    app_commands.Choice(name="Iron Sword (200 Gold)", value="iron_sword"),
    app_commands.Choice(name="Health Potion (50 Gold)", value="potion")
])
async def shop(interaction: discord.Interaction, item: app_commands.Choice[str]):
    p = get_player(interaction.user.id)
    prices = {"iron_sword": 200, "potion": 50}
    price = prices[item.value]
    if p["gold"] < price:
        await interaction.response.send_message("❌ Not enough gold!", ephemeral=True)
        return
    p["gold"] -= price
    p["inventory"].append(item.name)
    save_player(p)
    embed = discord.Embed(title="🛒 Purchase Successful", description=f"Bought **{item.name}** for `{price} Gold`!", color=0x2ecc71)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="coinflip", description="Gamble gold")
@app_commands.choices(choice=[app_commands.Choice(name="Heads", value="heads"), app_commands.Choice(name="Tails", value="tails")])
async def coinflip(interaction: discord.Interaction, bet: int, choice: app_commands.Choice[str]):
    p = get_player(interaction.user.id)
    if bet <= 0 or bet > p["gold"]:
        await interaction.response.send_message("❌ Invalid bet amount!", ephemeral=True)
        return
    outcome = random.choice(["heads", "tails"])
    if choice.value == outcome:
        p["gold"] += bet
        embed = discord.Embed(title="🎰 Coinflip Win!", description=f"It was **{outcome}**! Won **+{bet} Gold**!", color=0x2ecc71)
    else:
        p["gold"] -= bet
        embed = discord.Embed(title="💀 Coinflip Loss!", description=f"It was **{outcome}**! Lost **-{bet} Gold**!", color=0xe74c3c)
    save_player(p)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="boss_attack", description="Raid World Boss")
async def boss_attack(interaction: discord.Interaction):
    p = get_player(interaction.user.id)
    dmg = random.randint(p["atk"], p["atk"] + 20)
    global_boss["hp"] -= dmg
    if global_boss["hp"] <= 0:
        global_boss["hp"] = global_boss["max_hp"]
        p["gold"] += global_boss["reward"]
        save_player(p)
        embed = discord.Embed(title="💥 FINAL BLOW!", description=f"You landed the final blow on {global_boss['name']}! Received **+{global_boss['reward']} Gold**!", color=0xf1c40f)
    else:
        save_player(p)
        bar = make_hp_bar(global_boss['hp'], global_boss['max_hp'])
        embed = discord.Embed(title="⚔️ Boss Raided", description=f"Dealt **{dmg} DMG**!\n\n**Boss HP:** `{global_boss['hp']}/{global_boss['max_hp']}`\n`[{bar}]`", color=0xe74c3c)
    await interaction.response.send_message(embed=embed)

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
