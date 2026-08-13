import discord
from discord import app_commands
from discord.ext import commands
import random

class Minigames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # /fish
    @app_commands.command(name="fish", description="Go fishing to gather fish for crafting potions")
    async def fish(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        
        fish_types = ["Common Carp 🐟", "Salmon 🐟", "Golden Bass 🐠", "Old Boot 👞"]
        caught = random.choice(fish_types)
        
        if caught == "Old Boot 👞":
            embed = discord.Embed(title="🎣 Fishing", description="You hooked an **Old Boot 👞**... worth nothing!", color=0x95a5a6)
        else:
            p["fish_count"] = p.get("fish_count", 0) + 1
            self.bot.save_player(p)
            embed = discord.Embed(
                title="🎣 Fishing Success!", 
                description=f"You caught a **{caught}**!\nTotal Fish: `{p['fish_count']} 🐟`", 
                color=0x3498db
            )
            
        await interaction.response.send_message(embed=embed)

    # /mine
    @app_commands.command(name="mine", description="Mine deep underground for raw ores")
    async def mine(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        
        found_ore = random.randint(1, 3)
        p["ore_count"] = p.get("ore_count", 0) + found_ore
        self.bot.save_player(p)
        
        embed = discord.Embed(
            title="⛏️ Mining Operation", 
            description=f"Mined deep in the caves and extracted **+{found_ore} Ores 💎**!\nTotal Ores: `{p['ore_count']}`", 
            color=0x7f8c8d
        )
        await interaction.response.send_message(embed=embed)

    # /craft
    @app_commands.command(name="craft", description="Craft a Health Potion using 3 Fish and 1 Ore")
    async def craft(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        fish_cnt = p.get("fish_count", 0)
        ore_cnt = p.get("ore_count", 0)
        
        if fish_cnt < 3 or ore_cnt < 1:
            await interaction.response.send_message("❌ Crafting 1 Health Potion requires **3 Fish 🐟** and **1 Ore 💎**!", ephemeral=True)
            return
            
        p["fish_count"] = fish_cnt - 3
        p["ore_count"] = ore_cnt - 1
        p.setdefault("inventory", []).append("Health Potion")
        self.bot.save_player(p)
        
        embed = discord.Embed(title="🧪 Crafting Complete", description="Crafted **1x Health Potion** and added it to your Backpack!", color=0x2ecc71)
        await interaction.response.send_message(embed=embed)

    # /coinflip
    @app_commands.command(name="coinflip", description="Gamble gold on a coin toss")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Heads", value="heads"),
        app_commands.Choice(name="Tails", value="tails")
    ])
    async def coinflip(self, interaction: discord.Interaction, bet: int, choice: app_commands.Choice[str]):
        p = self.bot.get_player(interaction.user.id)
        gold = p.get("gold", 0)
        
        if bet <= 0 or bet > gold:
            await interaction.response.send_message("❌ Invalid bet amount or insufficient wallet gold!", ephemeral=True)
            return
            
        result = random.choice(["heads", "tails"])
        
        if choice.value == result:
            p["gold"] = gold + bet
            embed = discord.Embed(title="🎰 Coinflip Win!", description=f"The coin landed on **{result.upper()}**! You won **+{bet} Gold**!", color=0x2ecc71)
        else:
            p["gold"] = gold - bet
            embed = discord.Embed(title="💀 Coinflip Loss!", description=f"The coin landed on **{result.upper()}**! You lost **-{bet} Gold**.", color=0xe74c3c)
            
        self.bot.save_player(p)
        await interaction.response.send_message(embed=embed)

    # /slots
    @app_commands.command(name="slots", description="Spin the casino slot machine for huge payouts")
    async def slots(self, interaction: discord.Interaction, bet: int):
        p = self.bot.get_player(interaction.user.id)
        gold = p.get("gold", 0)
        
        if bet <= 0 or bet > gold:
            await interaction.response.send_message("❌ Invalid bet amount!", ephemeral=True)
            return
            
        emojis = ["🍎", "🍒", "💎", "7️⃣"]
        slot1, slot2, slot3 = random.choice(emojis), random.choice(emojis), random.choice(emojis)
        
        if slot1 == slot2 == slot3:
            payout = bet * 5
            p["gold"] = gold + payout
            msg = f"🎉 **JACKPOT 3-OF-A-KIND!** Won **+{payout} Gold**!"
            color = 0xf1c40f
        elif slot1 == slot2 or slot2 == slot3 or slot1 == slot3:
            payout = bet * 2
            p["gold"] = gold + payout
            msg = f"✨ **MATCH 2!** Won **+{payout} Gold**!"
            color = 0x2ecc71
        else:
            p["gold"] = gold - bet
            msg = f"❌ **NO MATCH!** Lost **-{bet} Gold**."
            color = 0xe74c3c
            
        self.bot.save_player(p)
        
        embed = discord.Embed(title="🎰 Slot Machine", description=f"|  {slot1}  |  {slot2}  |  {slot3}  |\n\n{msg}", color=color)
        await interaction.response.send_message(embed=embed)

    # /dice
    @app_commands.command(name="dice", description="Roll high against the dealer to double your gold")
    async def dice(self, interaction: discord.Interaction, bet: int):
        p = self.bot.get_player(interaction.user.id)
        gold = p.get("gold", 0)
        
        if bet <= 0 or bet > gold:
            await interaction.response.send_message("❌ Invalid bet amount!", ephemeral=True)
            return
            
        player_roll = random.randint(1, 6) + random.randint(1, 6)
        dealer_roll = random.randint(1, 6) + random.randint(1, 6)
        
        if player_roll > dealer_roll:
            p["gold"] = gold + bet
            desc = f"🎲 You rolled `{player_roll}` vs Dealer `{dealer_roll}`.\n\n🎉 **You Won +{bet} Gold!**"
            color = 0x2ecc71
        elif dealer_roll > player_roll:
            p["gold"] = gold - bet
            desc = f"🎲 You rolled `{player_roll}` vs Dealer `{dealer_roll}`.\n\n💀 **Dealer Won! Lost -{bet} Gold.**"
            color = 0xe74c3c
        else:
            desc = f"🎲 Both rolled `{player_roll}`.\n\n🤝 **It's a Tie! Gold returned.**"
            color = 0x3498db
            
        self.bot.save_player(p)
        embed = discord.Embed(title="🎲 Dice Duel", description=desc, color=color)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Minigames(bot))
