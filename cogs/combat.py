import discord
from discord import app_commands
from discord.ext import commands
import random

# Global Boss state
GLOBAL_BOSS = {"name": "Elder Shadow Dragon 🐉", "hp": 2500, "max_hp": 2500, "reward": 2500}

def make_hp_bar(current, max_val, length=10):
    percent = max(0, min(1.0, current / max_val))
    filled = int(length * percent)
    return "█" * filled + "░" * (length - filled)

class Combat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 9. /hunt
    @app_commands.command(name="hunt", description="Battle wild monsters for gold and experience")
    async def hunt(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        
        monsters = [
            {"name": "Wild Slime 🧪", "min_gold": 15, "max_gold": 30, "exp": 20},
            {"name": "Goblin Raider 👺", "min_gold": 30, "max_gold": 60, "exp": 40},
            {"name": "Dire Wolf 🐺", "min_gold": 50, "max_gold": 90, "exp": 65},
            {"name": "Skeleton Warrior 💀", "min_gold": 80, "max_gold": 130, "exp": 90}
        ]
        
        monster = random.choice(monsters)
        earned_gold = random.randint(monster["min_gold"], monster["max_gold"])
        earned_exp = monster["exp"]
        
        if p.get("pet"):
            earned_exp = int(earned_exp * 1.5)

        p["gold"] += earned_gold
        p["exp"] += earned_exp
        
        lvl_up_msg = ""
        if p["exp"] >= p["level"] * 100:
            p["level"] += 1
            p["base_atk"] += 5
            p["max_hp"] += 25
            p["hp"] = p["max_hp"]
            lvl_up_msg = f"\n\n🎉 **LEVEL UP!** Reached **Level {p['level']}**! *(+5 ATK, +25 HP)*"
        
        self.bot.save_player(p)
        
        embed = discord.Embed(title="⚔️ Monster Defeated!", description=f"You slayed a **{monster['name']}**!{lvl_up_msg}", color=0x2ecc71)
        embed.add_field(name="💰 Gold", value=f"`+{earned_gold} G`", inline=True)
        embed.add_field(name="⭐ EXP", value=f"`+{earned_exp} EXP`", inline=True)
        embed.set_footer(text=f"Level {p['level']} | Total Gold: {p['gold']} G")
        
        await interaction.response.send_message(embed=embed)

    # 10. /dungeon
    @app_commands.command(name="dungeon", description="Raid dangerous dungeon floors for high rewards")
    async def dungeon(self, interaction: discord.Interaction, floor: int):
        if floor < 1 or floor > 10:
            await interaction.response.send_message("❌ Dungeon floor must be between 1 and 10!", ephemeral=True)
            return
            
        p = self.bot.get_player(interaction.user.id)
        success_chance = max(10, 95 - (floor * 8))
        
        if random.randint(1, 100) <= success_chance:
            gold_reward = floor * 200
            exp_reward = floor * 75
            p["gold"] += gold_reward
            p["exp"] += exp_reward
            self.bot.save_player(p)
            
            embed = discord.Embed(title=f"🏰 Dungeon Floor {floor} Cleared!", description=f"You successfully conquered Floor {floor}!", color=0x2ecc71)
            embed.add_field(name="Rewards", value=f"💰 **+{gold_reward} Gold**\n⭐ **+{exp_reward} EXP**", inline=False)
        else:
            loss_hp = floor * 10
            p["hp"] = max(1, p["hp"] - loss_hp)
            self.bot.save_player(p)
            
            embed = discord.Embed(title=f"💀 Dungeon Floor {floor} Failed!", description=f"The dungeon monsters overpowered you! Lost **{loss_hp} HP**.", color=0xe74c3c)
            
        await interaction.response.send_message(embed=embed)

    # 11. /boss
    @app_commands.command(name="boss", description="View the current World Boss status and health")
    async def boss(self, interaction: discord.Interaction):
        bar = make_hp_bar(GLOBAL_BOSS["hp"], GLOBAL_BOSS["max_hp"])
        pct = int((GLOBAL_BOSS["hp"] / GLOBAL_BOSS["max_hp"]) * 100)
        
        embed = discord.Embed(
            title=f"🔥 World Boss: {GLOBAL_BOSS['name']}",
            description=f"**Health:** `{GLOBAL_BOSS['hp']}/{GLOBAL_BOSS['max_hp']}` ({pct}%)\n`[{bar}]`\n\nUse `/boss_attack` to join the raid!",
            color=0xe74c3c
        )
        embed.add_field(name="🏆 Final Blow Reward", value=f"`{GLOBAL_BOSS['reward']} Gold`", inline=False)
        await interaction.response.send_message(embed=embed)

    # 12. /boss_attack
    @app_commands.command(name="boss_attack", description="Deal heavy damage to the active World Boss")
    async def boss_attack(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        total_atk = p["base_atk"] + p["bonus_atk"] + (p["weapon_level"] * 5)
        
        dmg = random.randint(total_atk, total_atk + 35)
        GLOBAL_BOSS["hp"] -= dmg
        
        if GLOBAL_BOSS["hp"] <= 0:
            GLOBAL_BOSS["hp"] = GLOBAL_BOSS["max_hp"]
            p["gold"] += GLOBAL_BOSS["reward"]
            self.bot.save_player(p)
            
            embed = discord.Embed(title="💥 WORLD BOSS SLAIN!", description=f"**{interaction.user.name}** dealt the final blow and claimed **+{GLOBAL_BOSS['reward']} Gold**!", color=0xf1c40f)
        else:
            self.bot.save_player(p)
            bar = make_hp_bar(GLOBAL_BOSS["hp"], GLOBAL_BOSS["max_hp"])
            embed = discord.Embed(title="⚔️ Boss Strike", description=f"Dealt **{dmg} DMG** to {GLOBAL_BOSS['name']}!\n\n**HP:** `{GLOBAL_BOSS['hp']}/{GLOBAL_BOSS['max_hp']}`\n`[{bar}]`", color=0xe74c3c)
            
        await interaction.response.send_message(embed=embed)

    # 13. /pvp
    @app_commands.command(name="pvp", description="Challenge another player to a wagered duel")
    async def pvp(self, interaction: discord.Interaction, opponent: discord.User, wager: int):
        if opponent.id == interaction.user.id:
            await interaction.response.send_message("❌ You cannot fight yourself!", ephemeral=True)
            return
            
        p1 = self.bot.get_player(interaction.user.id)
        p2 = self.bot.get_player(opponent.id)
        
        if wager <= 0 or p1["gold"] < wager or p2["gold"] < wager:
            await interaction.response.send_message("❌ One of you doesn't have enough wallet gold for that wager!", ephemeral=True)
            return
            
        winner = random.choice([interaction.user, opponent])
        loser = opponent if winner == interaction.user else interaction.user
        
        w_p = self.bot.get_player(winner.id)
        l_p = self.bot.get_player(loser.id)
        
        w_p["gold"] += wager
        w_p["wins"] += 1
        l_p["gold"] -= wager
        l_p["losses"] += 1
        
        self.bot.save_player(w_p)
        self.bot.save_player(l_p)
        
        embed = discord.Embed(title="⚔️ PvP Duel Results", description=f"**{winner.name}** defeated **{loser.name}** in combat and took **{wager} Gold**!", color=0x9b59b6)
        await interaction.response.send_message(embed=embed)

    # 14. /forge
    @app_commands.command(name="forge", description="Attempt to upgrade your equipped weapon level")
    async def forge(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        cost = (p["weapon_level"] + 1) * 150
        
        if p["gold"] < cost:
            await interaction.response.send_message(f"❌ Weapon upgrade costs **{cost} Gold**!", ephemeral=True)
            return
            
        p["gold"] -= cost
        success_rate = max(25, 85 - (p["weapon_level"] * 10))
        
        if random.randint(1, 100) <= success_rate:
            p["weapon_level"] += 1
            embed = discord.Embed(title="✨ Forge Success!", description=f"Upgraded weapon to **+{p['weapon_level']}** *(+5 ATK)*!", color=0xf1c40f)
        else:
            embed = discord.Embed(title="💥 Forge Failed!", description="The upgrade attempt failed and materials were lost.", color=0xe74c3c)
            
        self.bot.save_player(p)
        await interaction.response.send_message(embed=embed)

    # 15. /bounty
    @app_commands.command(name="bounty", description="Place a bounty hit on another player")
    async def bounty(self, interaction: discord.Interaction, target: discord.User, amount: int):
        p1 = self.bot.get_player(interaction.user.id)
        p2 = self.bot.get_player(target.id)
        
        if amount <= 0 or p1["gold"] < amount:
            await interaction.response.send_message("❌ Insufficient gold balance!", ephemeral=True)
            return
            
        p1["gold"] -= amount
        p2["bounty"] += amount
        self.bot.save_player(p1)
        self.bot.save_player(p2)
        
        embed = discord.Embed(title="🎯 Bounty Placed", description=f"Placed a **{amount} Gold** bounty on {target.name}!", color=0xe74c3c)
        await interaction.response.send_message(embed=embed)

    # 16. /skill
    @app_commands.command(name="skill", description="Unleash a class special skill")
    async def skill(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        total_atk = p["base_atk"] + p["bonus_atk"] + (p["weapon_level"] * 5)
        dmg = total_atk * 2
        
        embed = discord.Embed(title="🔥 Ultimate Skill: Hellfire Nova", description=f"Cast Hellfire Nova dealing **{dmg} DMG** to enemies!", color=0xe67e22)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Combat(bot))
