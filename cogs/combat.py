import discord
from discord import app_commands
from discord.ext import commands
import random

# --- Interactive Profile View ---
class ProfileView(discord.ui.View):
    def __init__(self, bot, user):
        super().__init__(timeout=120)
        self.bot = bot
        self.user = user

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ This is not your menu!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="⚔️ Hunt", style=discord.ButtonStyle.primary)
    async def hunt_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await do_hunt_action(self.bot, interaction)

    @discord.ui.button(label="💰 Balance", style=discord.ButtonStyle.secondary)
    async def balance_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        p = self.bot.get_player(self.user.id)
        embed = discord.Embed(title="💰 Financial Balance", color=0xf1c40f)
        embed.add_field(name="Wallet Gold", value=f"`{p.get('gold', 0)} G`", inline=True)
        embed.add_field(name="Bank Gold", value=f"`{p.get('bank', 0)} G`", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🎒 Inventory", style=discord.ButtonStyle.secondary)
    async def inventory_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        p = self.bot.get_player(self.user.id)
        inv = p.get("inventory", [])
        inv_str = ", ".join(inv) if inv else "Empty"
        embed = discord.Embed(title="🎒 Backpack Inventory", description=f"`{inv_str}`", color=0x3498db)
        await interaction.response.send_message(embed=embed, ephemeral=True)


# --- Hunt Action View (Hunt Again / Return) ---
class HuntResultView(discord.ui.View):
    def __init__(self, bot, user):
        super().__init__(timeout=120)
        self.bot = bot
        self.user = user

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ You cannot use another player's hunt buttons!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="⚔️ Hunt Again", style=discord.ButtonStyle.success)
    async def hunt_again(self, interaction: discord.Interaction, button: discord.ui.Button):
        await do_hunt_action(self.bot, interaction)

    @discord.ui.button(label="👤 Profile", style=discord.ButtonStyle.secondary)
    async def return_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        p = self.bot.get_player(self.user.id)
        
        embed = discord.Embed(title=f"🛡️ Profile — {self.user.name}", color=0x3498db)
        embed.set_thumbnail(url=self.user.display_avatar.url)
        embed.add_field(name="Level", value=f"`Lvl {p.get('level', 1)}` (`{p.get('exp', 0)} EXP`)", inline=True)
        embed.add_field(name="Wallet Gold", value=f"`{p.get('gold', 0)} G`", inline=True)
        embed.add_field(name="Bank Gold", value=f"`{p.get('bank', 0)} G`", inline=True)
        embed.add_field(name="Health (HP)", value=f"`{p.get('hp', 100)}/{p.get('max_hp', 100)}`", inline=True)
        embed.add_field(name="Attack (ATK)", value=f"`{p.get('base_atk', 10) + p.get('bonus_atk', 0)}`", inline=True)
        embed.add_field(name="Weapon", value=f"`{p.get('weapon', 'None')}`", inline=True)

        view = ProfileView(self.bot, self.user)
        
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, view=view)
        else:
            await interaction.response.send_message(embed=embed, view=view)


# Helper function to execute hunt logic and render embed safely
async def do_hunt_action(bot, interaction: discord.Interaction):
    p = bot.get_player(interaction.user.id)
    
    # Check if player is knocked out
    if p.get("hp", 100) <= 0:
        p["hp"] = 20 # Auto-revive with 20 HP
        bot.save_player(p)
        death_msg = "💀 You were previously knocked out! The village doctor revived you with 20 HP."
        if interaction.response.is_done():
            await interaction.followup.send(death_msg, ephemeral=True)
        else:
            await interaction.response.send_message(death_msg, ephemeral=True)
        return

    monsters = [
        {"name": "Goblin Raider", "emoji": "👺", "hp": 40, "atk": 8, "exp": 40, "gold": 41},
        {"name": "Wild Slime", "emoji": "🧪", "hp": 30, "atk": 5, "exp": 25, "gold": 30},
        {"name": "Forest Wolf", "emoji": "🐺", "hp": 65, "atk": 15, "exp": 60, "gold": 75},
        {"name": "Cave Troll", "emoji": "👹", "hp": 110, "atk": 22, "exp": 100, "gold": 150}
    ]
    monster = random.choice(monsters)

    player_atk = p.get("base_atk", 10) + p.get("bonus_atk", 0)
    buff_msg = ""
    if p.get("skill_buff", False):
        player_atk *= 2
        p["skill_buff"] = False
        buff_msg = "\n🔥 **Hellfire Nova Empowered Your Attack! (2x DMG)**"

    monster_hp = monster["hp"] - player_atk

    if monster_hp <= 0:
        exp_gain = monster["exp"]
        if p.get("pet"):
            exp_gain = int(exp_gain * 1.5)

        p["exp"] = p.get("exp", 0) + exp_gain
        p["gold"] = p.get("gold", 0) + monster["gold"]

        lvl_up = ""
        req_exp = p.get("level", 1) * 100
        if p["exp"] >= req_exp:
            p["level"] = p.get("level", 1) + 1
            p["max_hp"] = p.get("max_hp", 100) + 25
            p["hp"] = p["max_hp"]
            p["base_atk"] = p.get("base_atk", 10) + 5
            lvl_up = f"\n🎉 **LEVEL UP!** Reached **Level {p['level']}**! *(+5 ATK, +25 HP)*"

        bot.save_player(p)

        embed = discord.Embed(
            title="⚔️ Monster Defeated!",
            description=f"You slayed a **{monster['name']}** {monster['emoji']}!{buff_msg}{lvl_up}",
            color=0x2ecc71
        )
        embed.add_field(name="💰 Gold", value=f"`+{monster['gold']} G`", inline=True)
        embed.add_field(name="⭐ EXP", value=f"`+{exp_gain} EXP`", inline=True)
        embed.set_footer(text=f"Level {p.get('level', 1)} | Total Gold: {p.get('gold', 0)} G")
    else:
        player_hp = max(0, p.get("hp", 100) - monster["atk"])
        p["hp"] = player_hp
        
        # Revive warning if player died in battle
        death_note = ""
        if player_hp == 0:
            p["hp"] = 20
            death_note = "\n💀 **You were knocked out and revived at the village with 20 HP!**"

        bot.save_player(p)

        embed = discord.Embed(
            title="⚔️ Battle Stalemate",
            description=f"You dealt **{player_atk} DMG** to **{monster['name']}** {monster['emoji']}!\nMonster struck back dealing **{monster['atk']} DMG**! Remaining HP: `{p['hp']}/{p.get('max_hp', 100)}`{death_note}",
            color=0xe67e22
        )

    view = HuntResultView(bot, interaction.user)
    
    # Safe interaction response handling
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, view=view)
    else:
        await interaction.response.send_message(embed=embed, view=view)


class Combat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # /hunt
    @app_commands.command(name="hunt", description="Hunt wild monsters for Gold and EXP")
    async def hunt(self, interaction: discord.Interaction):
        await do_hunt_action(self.bot, interaction)

    # /skill
    @app_commands.command(name="skill", description="Charge Hellfire Nova for 2x DMG on next Hunt!")
    async def skill(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        p["skill_buff"] = True
        self.bot.save_player(p)

        embed = discord.Embed(
            title="🔥 Ultimate Skill Charged: Hellfire Nova",
            description="You empowered your blade with **Hellfire Nova**!\nYour next **/hunt** will deal **2x DOUBLE DAMAGE**!",
            color=0xe74c3c
        )
        await interaction.response.send_message(embed=embed)

    # /dungeon
    @app_commands.command(name="dungeon", description="Raid a high-risk dungeon for massive rewards")
    async def dungeon(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        if p.get("hp", 100) < 30:
            await interaction.response.send_message("❌ Your HP is too low (<30 HP)! Drink a Health Potion.", ephemeral=True)
            return

        success = random.choice([True, False])
        if success:
            gold_gain = random.randint(200, 500)
            exp_gain = 150
            p["gold"] = p.get("gold", 0) + gold_gain
            p["exp"] = p.get("exp", 0) + exp_gain
            self.bot.save_player(p)
            embed = discord.Embed(title="🏰 Dungeon Conquered!", description=f"Cleared dungeon floors! Found **+{gold_gain} Gold** & **+{exp_gain} EXP**!", color=0x2ecc71)
        else:
            p["hp"] = max(5, p.get("hp", 100) - 40)
            self.bot.save_player(p)
            embed = discord.Embed(title="🏰 Dungeon Defeat", description=f"Overwhelmed by traps! Lost **40 HP** (`{p['hp']}/{p['max_hp']}` left).", color=0xe74c3c)

        await interaction.response.send_message(embed=embed)

    # /boss
    @app_commands.command(name="boss", description="Check current status of Global World Boss")
    async def boss(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🐲 Global World Boss: Ancient Red Dragon", description="Health: `4,500 / 10,000 HP`\nUse `/boss_attack` to participate!", color=0x9b59b6)
        await interaction.response.send_message(embed=embed)

    # /boss_attack
    @app_commands.command(name="boss_attack", description="Attack Global World Boss for shared bounty")
    async def boss_attack(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        dmg = p.get("base_atk", 10) + p.get("bonus_atk", 0) + random.randint(10, 30)
        gold_reward = dmg * 3
        
        p["gold"] = p.get("gold", 0) + gold_reward
        self.bot.save_player(p)

        embed = discord.Embed(title="🐲 Boss Raid Attack", description=f"Attacked the World Boss dealing **{dmg} DMG**!\nEarned **+{gold_reward} Gold**!", color=0xe74c3c)
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
        
        if not p.get("weapon") or p.get("weapon") == "None":
            await interaction.response.send_message("❌ You don't have a weapon equipped! Buy and equip one first.", ephemeral=True)
            return

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
            embed = discord.Embed(title="🔨 Forge Success!", description=f"Upgraded **{p['weapon']}** to **+{p['weapon_level']}**!\nBonus ATK increased to **+{p['bonus_atk']}**.", color=0x2ecc71)
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
