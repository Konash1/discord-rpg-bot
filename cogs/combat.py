import discord
from discord import app_commands
from discord.ext import commands
import random

class Combat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # /hunt
    @app_commands.command(name="hunt", description="Hunt wild monsters for Gold and EXP")
    async def hunt(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        
        monsters = [
            {"name": "Wild Slime 🧪", "hp": 30, "atk": 5, "exp": 25, "gold": 40},
            {"name": "Goblin Scout 👺", "hp": 50, "atk": 10, "exp": 45, "gold": 80},
            {"name": "Forest Wolf 🐺", "hp": 80, "atk": 18, "exp": 70, "gold": 120},
            {"name": "Cave Troll 👹", "hp": 130, "atk": 25, "exp": 110, "gold": 200}
        ]
        monster = random.choice(monsters)
        
        # Calculate Player ATK (Includes Skill Buff if active)
        player_atk = p.get("base_atk", 10) + p.get("bonus_atk", 0)
        buff_msg = ""
        if p.get("skill_buff", False):
            player_atk *= 2
            p["skill_buff"] = False # Consume buff
            buff_msg = "\n🔥 **Hellfire Nova Empowered Your Attack! (2x DMG)**"

        # Combat Simulation
        monster_hp = monster["hp"]
        player_hp = p.get("hp", 100)

        # Player hits monster
        monster_hp -= player_atk

        if monster_hp <= 0:
            # Win
            exp_gain = monster["exp"]
            if p.get("pet"):
                exp_gain = int(exp_gain * 1.5)

            p["exp"] = p.get("exp", 0) + exp_gain
            p["gold"] = p.get("gold", 0) + monster["gold"]
            
            # Level Up Check
            lvl_up = ""
            req_exp = p.get("level", 1) * 100
            if p["exp"] >= req_exp:
                p["level"] = p.get("level", 1) + 1
                p["max_hp"] = p.get("max_hp", 100) + 25
                p["hp"] = p["max_hp"]
                p["base_atk"] = p.get("base_atk", 10) + 5
                lvl_up = f"\n🎉 **LEVEL UP!** You reached **Level {p['level']}**!"

            self.bot.save_player(p)
            embed = discord.Embed(title="⚔️ Victory!", description=f"You defeated **{monster['name']}**!{buff_msg}\n\n💰 Rewards: `+{monster['gold']} Gold` | `+{exp_gain} EXP`{lvl_up}", color=0x2ecc71)
        else:
            # Monster survives and hits back
            player_hp -= monster["atk"]
            p["hp"] = max(0, player_hp)
            self.bot.save_player(p)
            embed = discord.Embed(title="⚔️ Battle Stalemate", description=f"You dealt **{player_atk} DMG** to {monster['name']} (Left with {monster_hp} HP).{buff_msg}\nMonster struck back dealing **{monster['atk']} DMG**! Current HP: `{p['hp']}/{p['max_hp']}`", color=0xe67e22)

        await interaction.response.send_message(embed=embed)

    # /skill
    @app_commands.command(name="skill", description="Charge your Ultimate Skill to deal 2x DMG on your next Hunt or PvP!")
    async def skill(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        p["skill_buff"] = True
        self.bot.save_player(p)

        embed = discord.Embed(
            title="🔥 Ultimate Skill Charged: Hellfire Nova",
            description="You empowered your blade with **Hellfire Nova**!\nYour next **/hunt** or **/pvp** will deal **2x DOUBLE DAMAGE**!",
            color=0xe74c3c
        )
        await interaction.response.send_message(embed=embed)

    # /dungeon
    @app_commands.command(name="dungeon", description="Raid a high-risk dungeon for massive rewards")
    async def dungeon(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        if p.get("hp", 100) < 30:
            await interaction.response.send_message("❌ Your HP is too low! Use `/use` to drink a Health Potion.", ephemeral=True)
            return

        success = random.choice([True, False])
        if success:
            gold_gain = random.randint(200, 500)
            exp_gain = 150
            p["gold"] = p.get("gold", 0) + gold_gain
            p["exp"] = p.get("exp", 0) + exp_gain
            self.bot.save_player(p)
            embed = discord.Embed(title="🏰 Dungeon Conquered!", description=f"Cleared the dungeon floors and found **+{gold_gain} Gold** & **+{exp_gain} EXP**!", color=0x2ecc71)
        else:
            p["hp"] = max(5, p.get("hp", 100) - 40)
            self.bot.save_player(p)
            embed = discord.Embed(title="🏰 Dungeon Defeat", description=f"You were overwhelmed by dungeon traps! Lost **40 HP** (`{p['hp']}/{p['max_hp']}` left).", color=0xe74c3c)

        await interaction.response.send_message(embed=embed)

    # /boss
    @app_commands.command(name="boss", description="Check current status of Global World Boss")
    async def boss(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🐲 Global World Boss: Ancient Red Dragon", description="Health: `4,500 / 10,000 HP`\nUse `/boss_attack` to participate in raid!", color=0x9b59b6)
        await interaction.response.send_message(embed=embed)

    # /boss_attack
    @app_commands.command(name="boss_attack", description="Attack Global World Boss for shared bounty")
    async def boss_attack(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        dmg = p.get("base_atk", 10) + p.get("bonus_atk", 0) + random.randint(10, 30)
        gold_reward = dmg * 3
        
        p["gold"] = p.get("gold", 0) + gold_reward
        self.bot.save_player(p)

        embed = discord.Embed(title="🐲 Boss Raid Attack", description=f"You attacked the World Boss dealing **{dmg} DMG**!\nEarned **+{gold_reward} Gold** based on your performance!", color=0xe74c3c)
        await interaction.response.send_message(embed=embed)

    # /pvp
    @app_commands.command(name="pvp", description="Duel another player for gold")
    async def pvp(self, interaction: discord.Interaction, target: discord.User):
        if target.id == interaction.user.id:
            await interaction.response.send_message("❌ You cannot duel yourself!", ephemeral=True)
            return

        p1 = self.bot.get_player(interaction.user.id)
        p2 = self.bot.get_player(target.id)

        p1_atk = p1.get("base_atk", 10) + p1.get("bonus_atk", 0)
        p2_atk = p2.get("base_atk", 10) + p2.get("bonus_atk", 0)

        if p1_atk >= p2_atk:
            winner, loser = p1, p2
            winner_user, loser_user = interaction.user, target
        else:
            winner, loser = p2, p1
            winner_user, loser_user = target, interaction.user

        winner["gold"] = winner.get("gold", 0) + 100
        winner["wins"] = winner.get("wins", 0) + 1
        loser["losses"] = loser.get("losses", 0) + 1

        self.bot.save_player(winner)
        self.bot.save_player(loser)

        embed = discord.Embed(title="⚔️ PvP Duel Outcome", description=f"**{winner_user.name}** defeated **{loser_user.name}** in combat and won **+100 Gold**!", color=0xf1c40f)
        await interaction.response.send_message(embed=embed)

    # /forge
    @app_commands.command(name="forge", description="Upgrade your currently equipped weapon")
    async def forge(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        cost = 100 * (p.get("weapon_level", 0) + 1)

        if p.get("gold", 0) < cost:
            await interaction.response.send_message(f"❌ Forging costs **{cost} Gold**!", ephemeral=True)
            return

        p["gold"] -= cost
        success = random.random() < 0.70

        if success:
            p["weapon_level"] = p.get("weapon_level", 0) + 1
            p["bonus_atk"] = p.get("bonus_atk", 0) + 5
            self.bot.save_player(p)
            embed = discord.Embed(title="🔨 Forge Success!", description=f"Upgraded weapon to **+{p['weapon_level']}**! Bonus ATK increased to **+{p['bonus_atk']}**.", color=0x2ecc71)
        else:
            self.bot.save_player(p)
            embed = discord.Embed(title="🔨 Forge Failed", description="The blacksmith failed to upgrade your weapon! Gold was lost.", color=0xe74c3c)

        await interaction.response.send_message(embed=embed)

    # /bounty
    @app_commands.command(name="bounty", description="Place a bounty on a player")
    async def bounty(self, interaction: discord.Interaction, target: discord.User, amount: int):
        if amount < 50:
            await interaction.response.send_message("❌ Minimum bounty is 50 Gold!", ephemeral=True)
            return

        p = self.bot.get_player(interaction.user.id)
        if p.get("gold", 0) < amount:
            await interaction.response.send_message("❌ Insufficient gold!", ephemeral=True)
            return

        p["gold"] -= amount
        target_p = self.bot.get_player(target.id)
        target_p["bounty"] = target_p.get("bounty", 0) + amount

        self.bot.save_player(p)
        self.bot.save_player(target_p)

        embed = discord.Embed(title="🎯 Bounty Placed", description=f"Placed a **{amount} Gold** bounty on {target.name}!", color=0xe74c3c)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Combat(bot))
