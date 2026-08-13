import discord
from discord import app_commands
from discord.ext import commands
import time
import random

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 1. /profile
    @app_commands.command(name="profile", description="View your detailed RPG character profile and stats")
    async def profile(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        total_atk = p["base_atk"] + p["bonus_atk"] + (p["weapon_level"] * 5)
        
        embed = discord.Embed(title=f"🛡️ Character Profile — {interaction.user.name}", color=0x3498db)
        embed.add_field(
            name="📊 Combat Stats", 
            value=f"**Level:** {p['level']}\n**EXP:** {p['exp']}/{p['level']*100}\n**HP:** {p['hp']}/{p['max_hp']}\n**Total ATK:** {total_atk}", 
            inline=True
        )
        embed.add_field(
            name="💼 Wealth & Guild", 
            value=f"**Wallet:** {p['gold']} G\n**Bank:** {p['bank']} G\n**Bounty:** {p['bounty']} G\n**Guild:** {p['guild'] or 'None'}", 
            inline=True
        )
        embed.add_field(
            name="⚔️ Gear & Assets", 
            value=f"**Weapon:** {p['weapon']} `(+{p['weapon_level']})`\n**Armor:** {p['armor']}\n**Pet:** {p['pet'] or 'None'}\n**Fish:** {p['fish_count']} 🐟 | **Ores:** {p['ore_count']} 💎", 
            inline=False
        )
        
        inv_str = ", ".join([f"`{item}`" for item in p['inventory']]) if p['inventory'] else "*Empty*"
        embed.add_field(name="🎒 Backpack", value=inv_str, inline=False)
        embed.set_footer(text=f"Duels Won: {p['wins']} | Lost: {p['losses']}")
        
        await interaction.response.send_message(embed=embed)

    # 2. /balance
    @app_commands.command(name="balance", description="Check your wallet and bank gold balance")
    async def balance(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        embed = discord.Embed(title=f"💰 Balance — {interaction.user.name}", color=0xf1c40f)
        embed.add_field(name="Wallet Gold", value=f"`{p['gold']} G`", inline=True)
        embed.add_field(name="Bank Deposit", value=f"`{p['bank']} G`", inline=True)
        embed.add_field(name="Net Worth", value=f"`{p['gold'] + p['bank']} G`", inline=False)
        await interaction.response.send_message(embed=embed)

    # 3. /daily
    @app_commands.command(name="daily", description="Claim your 24-hour daily gold allowance")
    async def daily(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        now = time.time()
        if now - p["last_daily"] < 86400:
            remaining = int((86400 - (now - p["last_daily"])) / 3600)
            await interaction.response.send_message(f"⏳ Daily reward on cooldown! Try again in `{remaining} hours`.", ephemeral=True)
            return
            
        p["gold"] += 350
        p["last_daily"] = now
        self.bot.save_player(p)
        
        embed = discord.Embed(title="🎁 Daily Reward Claimed", description="You received **+350 Gold**!", color=0x2ecc71)
        await interaction.response.send_message(embed=embed)

    # 4. /work
    @app_commands.command(name="work", description="Do odd jobs around town for gold (1 Hour Cooldown)")
    async def work(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        now = time.time()
        if now - p["last_work"] < 3600:
            remaining = int((3600 - (now - p["last_work"])) / 60)
            await interaction.response.send_message(f"⏳ You are tired! Rest for `{remaining} minutes` before working again.", ephemeral=True)
            return
            
        jobs = ["repaired tavern tables", "cleaned the blacksmith forge", "guarded the city gate", "harvested wheat"]
        earned = random.randint(50, 120)
        job = random.choice(jobs)
        
        p["gold"] += earned
        p["last_work"] = now
        self.bot.save_player(p)
        
        embed = discord.Embed(title="🔨 Work Shift Complete", description=f"You {job} and earned **+{earned} Gold**!", color=0x3498db)
        await interaction.response.send_message(embed=embed)

    # 5. /deposit
    @app_commands.command(name="deposit", description="Deposit wallet gold safely into your bank account")
    async def deposit(self, interaction: discord.Interaction, amount: int):
        p = self.bot.get_player(interaction.user.id)
        if amount <= 0 or amount > p["gold"]:
            await interaction.response.send_message("❌ Invalid deposit amount!", ephemeral=True)
            return
            
        p["gold"] -= amount
        p["bank"] += amount
        self.bot.save_player(p)
        
        embed = discord.Embed(title="🏦 Bank Deposit", description=f"Deposited **{amount} Gold** into your bank account.", color=0x2ecc71)
        await interaction.response.send_message(embed=embed)

    # 6. /withdraw
    @app_commands.command(name="withdraw", description="Withdraw gold from your bank account to your wallet")
    async def withdraw(self, interaction: discord.Interaction, amount: int):
        p = self.bot.get_player(interaction.user.id)
        if amount <= 0 or amount > p["bank"]:
            await interaction.response.send_message("❌ Invalid withdrawal amount!", ephemeral=True)
            return
            
        p["bank"] -= amount
        p["gold"] += amount
        self.bot.save_player(p)
        
        embed = discord.Embed(title="🏧 Bank Withdrawal", description=f"Withdrew **{amount} Gold** from your bank account.", color=0x2ecc71)
        await interaction.response.send_message(embed=embed)

    # 7. /pay
    @app_commands.command(name="pay", description="Transfer gold from your wallet to another player")
    async def pay(self, interaction: discord.Interaction, target: discord.User, amount: int):
        if target.id == interaction.user.id:
            await interaction.response.send_message("❌ You cannot send gold to yourself!", ephemeral=True)
            return
            
        p1 = self.bot.get_player(interaction.user.id)
        p2 = self.bot.get_player(target.id)
        
        if amount <= 0 or p1["gold"] < amount:
            await interaction.response.send_message("❌ You do not have enough wallet gold!", ephemeral=True)
            return
            
        p1["gold"] -= amount
        p2["gold"] += amount
        self.bot.save_player(p1)
        self.bot.save_player(p2)
        
        embed = discord.Embed(title="💸 Gold Transferred", description=f"Sent **{amount} Gold** to {target.name}!", color=0x9b59b6)
        await interaction.response.send_message(embed=embed)

    # 8. /leaderboard
    @app_commands.command(name="leaderboard", description="View top 10 richest players across all servers")
    async def leaderboard(self, interaction: discord.Interaction):
        top_players = list(self.bot.db_players.find().sort("gold", -1).limit(10))
        description = ""
        for idx, player in enumerate(top_players, 1):
            total_net = player.get("gold", 0) + player.get("bank", 0)
            description += f"**#{idx}** <@{player['_id']}> — `{total_net} G` *(Lvl {player.get('level', 1)})*\n"
            
        embed = discord.Embed(title="🏆 Global Wealth Leaderboard", description=description or "No recorded players yet.", color=0xf1c40f)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
