import discord
from discord import app_commands
from discord.ext import commands
import time

# 30+ Achievements List
ACHIEVEMENTS_LIST = [
    # Combat & Dungeons
    {"id": "first_blood", "cat": "⚔️ Combat", "name": "First Blood", "desc": "Win 1 PvP duel", "key": "wins", "target": 1, "reward": 150},
    {"id": "pvp_warrior", "cat": "⚔️ Combat", "name": "Gladiator", "desc": "Win 10 PvP duels", "key": "wins", "target": 10, "reward": 500},
    {"id": "pvp_legend", "cat": "⚔️ Combat", "name": "Arena Master", "desc": "Win 50 PvP duels", "key": "wins", "target": 50, "reward": 2500},
    {"id": "apprentice", "cat": "⚔️ Combat", "name": "Rookie Adventurer", "desc": "Reach Level 5", "key": "level", "target": 5, "reward": 300},
    {"id": "veteran", "cat": "⚔️ Combat", "name": "Seasoned Fighter", "desc": "Reach Level 15", "key": "level", "target": 15, "reward": 1000},
    {"id": "godlike", "cat": "⚔️ Combat", "name": "Ascended Legend", "desc": "Reach Level 50", "key": "level", "target": 50, "reward": 5000},
    {"id": "weapon_master", "cat": "⚔️ Combat", "name": "Master Blacksmith", "desc": "Forge a +5 Weapon", "key": "weapon_level", "target": 5, "reward": 800},
    {"id": "bounty_hunter", "cat": "⚔️ Combat", "name": "Headhunter", "desc": "Have a bounty placed on you", "key": "bounty", "target": 100, "reward": 400},

    # Economy & Wealth
    {"id": "pocket_change", "cat": "💰 Wealth", "name": "Getting Started", "desc": "Hold 500 Gold in wallet", "key": "gold", "target": 500, "reward": 100},
    {"id": "thrifty", "cat": "💰 Wealth", "name": "Smart Saver", "desc": "Deposit 1,000 Gold in bank", "key": "bank", "target": 1000, "reward": 250},
    {"id": "wealthy", "cat": "💰 Wealth", "name": "Merchant Prince", "desc": "Deposit 10,000 Gold in bank", "key": "bank", "target": 10000, "reward": 1500},
    {"id": "millionaire", "cat": "💰 Wealth", "name": "Dragon Hoarder", "desc": "Deposit 100,000 Gold in bank", "key": "bank", "target": 100000, "reward": 10000},
    {"id": "big_pockets", "cat": "💰 Wealth", "name": "Backpack Collector", "desc": "Hold 5 items in inventory", "key": "inv_count", "target": 5, "reward": 200},
    {"id": "hoarder", "cat": "💰 Wealth", "name": "Treasure Vault", "desc": "Hold 15 items in inventory", "key": "inv_count", "target": 15, "reward": 600},
    {"id": "first_purchase", "cat": "💰 Wealth", "name": "Support Local Business", "desc": "Equip any non-wooden weapon", "key": "has_custom_weapon", "target": 1, "reward": 200},
    {"id": "pet_owner", "cat": "💰 Wealth", "name": "Beast Tamer", "desc": "Adopt a companion pet", "key": "has_pet", "target": 1, "reward": 350},

    # Gathering & Crafting
    {"id": "first_catch", "cat": "🎣 Gathering", "name": "First Catch", "desc": "Catch 1 Fish", "key": "fish_count", "target": 1, "reward": 100},
    {"id": "angler", "cat": "🎣 Gathering", "name": "Avid Fisherman", "desc": "Catch 10 Fish", "key": "fish_count", "target": 10, "reward": 500},
    {"id": "poseidon", "cat": "🎣 Gathering", "name": "Ruler of the Seas", "desc": "Catch 50 Fish", "key": "fish_count", "target": 50, "reward": 2000},
    {"id": "novice_miner", "cat": "⛏️ Gathering", "name": "Strike Ore", "desc": "Mine 1 Ore", "key": "ore_count", "target": 1, "reward": 100},
    {"id": "cave_explorer", "cat": "⛏️ Gathering", "name": "Deep Speleologist", "desc": "Mine 15 Ores", "key": "ore_count", "target": 15, "reward": 600},
    {"id": "dwarf_king", "cat": "⛏️ Gathering", "name": "Mines of Moria", "desc": "Mine 50 Ores", "key": "ore_count", "target": 50, "reward": 2000},
    {"id": "alchemist", "cat": "🧪 Crafting", "name": "Apprentice Alchemist", "desc": "Craft 1 Health Potion", "key": "crafted_potions", "target": 1, "reward": 250},
    {"id": "master_alchemist", "cat": "🧪 Crafting", "name": "Grand Pharmacist", "desc": "Craft 10 Health Potions", "key": "crafted_potions", "target": 10, "reward": 1200},

    # Guild & Social
    {"id": "guild_member", "cat": "🛡️ Guild", "name": "Brotherhood", "desc": "Join or create a Guild", "key": "in_guild", "target": 1, "reward": 300},
    {"id": "charity", "cat": "🛡️ Guild", "name": "Generous Leader", "desc": "Pay another player gold", "key": "gold_given", "target": 500, "reward": 200},

    # Gambling & Luck
    {"id": "lucky_flip", "cat": "🎰 Casino", "name": "Lucky Toss", "desc": "Win a Coinflip", "key": "coinflip_wins", "target": 1, "reward": 150},
    {"id": "high_roller_casino", "cat": "🎰 Casino", "name": "Casino King", "desc": "Win 10 Coinflips", "key": "coinflip_wins", "target": 10, "reward": 800},
    {"id": "slots_beginner", "cat": "🎰 Casino", "name": "Slot Spinner", "desc": "Spin the slots 5 times", "key": "slots_played", "target": 5, "reward": 250},
    {"id": "dice_gambler", "cat": "🎰 Casino", "name": "High Roller", "desc": "Win 5 Dice duels", "key": "dice_wins", "target": 5, "reward": 500},
    {"id": "jackpot_winner", "cat": "🎰 Casino", "name": "Lady Luck", "desc": "Hit a 3-of-a-kind Slots Jackpot", "key": "jackpots", "target": 1, "reward": 2000}
]

DAILY_QUESTS_POOL = [
    {"title": "Slay Wild Beasts 🐺", "desc": "Defeat 3 monsters using `/hunt`", "reward": 200},
    {"title": "Deep Water Angler 🐟", "desc": "Catch 2 Fish using `/fish`", "reward": 180},
    {"title": "Cave Expedition 💎", "desc": "Extract 3 Ores using `/mine`", "reward": 220},
    {"title": "Casino Thrills 🎰", "desc": "Play 3 Coinflips or Slots", "reward": 150},
    {"title": "Dungeon Crawler 🏰", "desc": "Attempt 2 Dungeon raids", "reward": 300},
    {"title": "Blacksmith Shift 🔨", "desc": "Attempt 1 Weapon Forge", "reward": 250}
]

class Quests(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_user_value(self, p, key):
        if key == "inv_count":
            return len(p.get("inventory", []))
        elif key == "has_custom_weapon":
            return 1 if p.get("weapon") and "Wooden" not in p.get("weapon") else 0
        elif key == "has_pet":
            return 1 if p.get("pet") else 0
        elif key == "in_guild":
            return 1 if p.get("guild") else 0
        return p.get(key, 0)

    # 1. /help
    @app_commands.command(name="help", description="List all available RPG commands by category")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📜 RPG Bot — Command Guide",
            description="Here is a complete list of all available slash commands:",
            color=0x3498db
        )

        embed.add_field(
            name="💰 Economy & Profile",
            value="`/profile` • `/balance` • `/daily` • `/work` • `/deposit` • `/withdraw` • `/pay` • `/leaderboard`",
            inline=False
        )
        embed.add_field(
            name="⚔️ Combat & Adventure",
            value="`/hunt` • `/dungeon` • `/boss` • `/boss_attack` • `/pvp` • `/forge` • `/bounty` • `/skill`",
            inline=False
        )
        embed.add_field(
            name="🛡️ Guilds & Shop",
            value="`/guild_create` • `/guild_join` • `/guild_leave` • `/guild_info` • `/shop` • `/equip` • `/use` • `/pet_adopt`",
            inline=False
        )
        embed.add_field(
            name="🎣 Gathering & Casino",
            value="`/fish` • `/mine` • `/craft` • `/coinflip` • `/slots` • `/dice`",
            inline=False
        )
        embed.add_field(
            name="📜 Quests & System",
            value="`/quest` • `/claim_quest` • `/advancements` • `/claim_advancement` • `/ping` • `/info` • `/help`",
            inline=False
        )

        embed.set_footer(text="Created by Konashi • Type / standard slash commands")
        await interaction.response.send_message(embed=embed)

    # 2. /advancements
    @app_commands.command(name="advancements", description="View all 30+ advancements and progress")
    async def advancements(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        unlocked_list = p.get("unlocked_achievements", [])

        embed = discord.Embed(
            title="🏆 Player Advancements & Achievements",
            description=f"Unlocked: `{len(unlocked_list)} / {len(ACHIEVEMENTS_LIST)}` Achievements\nUse `/claim_advancement` to collect rewards!",
            color=0xf1c40f
        )

        categories = {}
        for ach in ACHIEVEMENTS_LIST:
            cat = ach["cat"]
            if cat not in categories:
                categories[cat] = []

            val = self.get_user_value(p, ach["key"])
            is_unlocked = ach["id"] in unlocked_list
            status = "✅ **Unlocked**" if is_unlocked else f"🔒 `{val}/{ach['target']}`"

            categories[cat].append(f"{ach['name']} — {status}\n*({ach['desc']} • Reward: `{ach['reward']} G`)*")

        for cat_name, items in categories.items():
            embed.add_field(name=cat_name, value="\n".join(items[:3]), inline=False)

        await interaction.response.send_message(embed=embed)

    # 3. /claim_advancement
    @app_commands.command(name="claim_advancement", description="Claim rewards for unlocked advancements!")
    async def claim_advancement(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        if "unlocked_achievements" not in p:
            p["unlocked_achievements"] = []

        total_reward = 0
        newly_unlocked = []

        for ach in ACHIEVEMENTS_LIST:
            if ach["id"] not in p["unlocked_achievements"]:
                val = self.get_user_value(p, ach["key"])
                if val >= ach["target"]:
                    p["unlocked_achievements"].append(ach["id"])
                    total_reward += ach["reward"]
                    newly_unlocked.append(ach["name"])

        if newly_unlocked:
            p["gold"] = p.get("gold", 0) + total_reward
            self.bot.save_player(p)
            
            names_str = "\n• " + "\n• ".join(newly_unlocked)
            embed = discord.Embed(
                title="🎉 Advancements Unlocked!",
                description=f"You completed **{len(newly_unlocked)}** new advancements:{names_str}\n\n💰 **Total Claimed:** `+{total_reward} Gold`",
                color=0x2ecc71
            )
        else:
            embed = discord.Embed(
                title="🔒 No Pending Advancements",
                description="You haven't completed any new advancements yet. Keep playing and check `/advancements`!",
                color=0xe74c3c
            )

        await interaction.response.send_message(embed=embed)

    # 4. /quest
    @app_commands.command(name="quest", description="View your current active daily quests")
    async def quest(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📜 Active Daily Quest Board", color=0x3498db)
        
        for q in DAILY_QUESTS_POOL[:3]:
            embed.add_field(
                name=f"✨ {q['title']}", 
                value=f"{q['desc']}\nReward: 💰 `{q['reward']} Gold`", 
                inline=False
            )

        embed.set_footer(text="Complete these actions and use /claim_quest to receive gold!")
        await interaction.response.send_message(embed=embed)

    # 5. /claim_quest
    @app_commands.command(name="claim_quest", description="Claim daily quest gold bonus")
    async def claim_quest(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        current_time = int(time.time())
        cooldown = 86400  # 24 hours

        last_claim = p.get("last_quest_claim", 0)
        if current_time - last_claim < cooldown:
            remaining = cooldown - (current_time - last_claim)
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            await interaction.response.send_message(
                f"⌛ You already claimed your daily quest reward! Try again in **{hours}h {minutes}m**.",
                ephemeral=True
            )
            return

        reward = 250
        p["gold"] = p.get("gold", 0) + reward
        p["last_quest_claim"] = current_time
        self.bot.save_player(p)

        embed = discord.Embed(
            title="🎯 Daily Quest Claimed!",
            description=f"Completed your daily assignments and received **+{reward} Gold**!",
            color=0x2ecc71
        )
        await interaction.response.send_message(embed=embed)

    # 6. /ping
    @app_commands.command(name="ping", description="Check bot latency and connection status")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(title="🏓 Pong!", description=f"Bot Latency: `{latency} ms`", color=0x2ecc71)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # 7. /info
    @app_commands.command(name="info", description="View RPG server statistics and developer credits")
    async def info(self, interaction: discord.Interaction):
        total_players = self.bot.db_players.count_documents({})
        total_guilds = self.bot.db_guilds.count_documents({})

        embed = discord.Embed(title="🤖 RPG Bot Info", color=0x9b59b6)
        embed.add_field(name="Developer", value="`Created by Konashi`", inline=False)
        embed.add_field(name="Registered Players", value=f"`{total_players}`", inline=True)
        embed.add_field(name="Active Guilds", value=f"`{total_guilds}`", inline=True)
        embed.add_field(name="Connected Servers", value=f"`{len(self.bot.guilds)}`", inline=True)
        embed.set_footer(text="Created by Konashi • Discord.py v2 & MongoDB")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Quests(bot))
