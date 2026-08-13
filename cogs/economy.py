import discord
from discord import app_commands
from discord.ext import commands
import time
import random

PETS = {
    "1": {"name": "Baby Dragon", "cost": 500, "emoji": "🐲", "desc": "+50% bonus EXP from hunts"},
    "2": {"name": "Golden Cat", "cost": 400, "emoji": "🐱", "desc": "+30% bonus Gold from hunts"},
    "3": {"name": "Shadow Wolf", "cost": 600, "emoji": "🐺", "desc": "+10 bonus Attack power"},
    "4": {"name": "Phoenix", "cost": 750, "emoji": "🔥", "desc": "Heals +15 HP after every hunt"}
}

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # /profile
    @app_commands.command(name="profile", description="View your RPG character card and stats")
    async def profile(self, interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user
        p = self.bot.get_player(target.id)

        # Automatic Cleanup: Remove duplicate raw price/weapon names from inventory list
        raw_inv = p.get("inventory", [])
        cleaned_inv = [
            item for item in raw_inv 
            if isinstance(item, str) and not ("Gold" in item or "G)" in item)
        ]
        if len(cleaned_inv) != len(raw_inv):
            p["inventory"] = cleaned_inv
            self.bot.save_player(p)

        embed = discord.Embed(title=f"🛡️ Profile — {target.name}", color=0x3498db)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Level", value=f"`Lvl {p.get('level', 1)}` (`{p.get('exp', 0)} EXP`)", inline=True)
        embed.add_field(name="Wallet Gold", value=f"`{p.get('gold', 0)} G`", inline=True)
        embed.add_field(name="Bank Gold", value=f"`{p.get('bank', 0)} G`", inline=True)
        
        hp = p.get('hp', 100)
        max_hp = p.get('max_hp', 100)
        base_atk = p.get('base_atk', 10)
        bonus_atk = p.get('bonus_atk', 0)
        
        embed.add_field(name="Health (HP)", value=f"`{hp}/{max_hp}`", inline=True)
        embed.add_field(name="Attack (ATK)", value=f"`{base_atk + bonus_atk}` (`{base_atk}` + `{bonus_atk}`)", inline=True)
        embed.add_field(name="Equipped Weapon", value=f"`{p.get('weapon', 'None')}`", inline=True)
        embed.add_field(name="Guild", value=f"`{p.get('guild') or 'None'}`", inline=True)
        embed.add_field(name="Pet", value=f"`{p.get('pet') or 'None'}`", inline=True)
        embed.add_field(name="PvP Record", value=f"`{p.get('wins', 0)}W - {p.get('losses', 0)}L`", inline=True)
        
        inv_str = ", ".join(cleaned_inv) if cleaned_inv else "Empty"
        embed.add_field(name="Backpack Items", value=f"`{inv_str}`", inline=False)

        await interaction.response.send_message(embed=embed)

    # /balance
    @app_commands.command(name="balance", description="Check your wallet and bank gold balance")
    async def balance(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        embed = discord.Embed(title="💰 Financial Balance", color=0xf1c40f)
        embed.add_field(name="Wallet Gold", value=f"`{p.get('gold', 0)} G`", inline=True)
        embed.add_field(name="Bank Gold", value=f"`{p.get('bank', 0)} G`", inline=True)
        await interaction.response.send_message(embed=embed)

    # /daily
    @app_commands.command(name="daily", description="Claim your daily gold reward (24h cooldown)")
    async def daily(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        now = time.time()
        last_daily = p.get("last_daily", 0)
        
        if now - last_daily < 86400:
            remaining = int((86400 - (now - last_daily)) / 3600)
            await interaction.response.send_message(f"⌛ Daily reward on cooldown! Wait **{remaining} hours**.", ephemeral=True)
            return

        reward = 300 + (p.get("level", 1) * 20)
        p["gold"] = p.get("gold", 0) + reward
        p["last_daily"] = now
        self.bot.save_player(p)

        embed = discord.Embed(title="🎁 Daily Claimed!", description=f"You received **+{reward} Gold**!", color=0x2ecc71)
        await interaction.response.send_message(embed=embed)

    # /work
    @app_commands.command(name="work", description="Do odd jobs to earn quick cash (1h cooldown)")
    async def work(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        now = time.time()
        last_work = p.get("last_work", 0)

        if now - last_work < 3600:
            remaining = int((3600 - (now - last_work)) / 60)
            await interaction.response.send_message(f"⌛ You're tired! Wait **{remaining} minutes** before working again.", ephemeral=True)
            return

        earned = random.randint(50, 150)
        p["gold"] = p.get("gold", 0) + earned
        p["last_work"] = now
        self.bot.save_player(p)

        jobs = ["cleared dungeon rubble", "trained village guards", "repaired weapons for local heroes", "brewed potion ingredients"]
        job = random.choice(jobs)

        embed = discord.Embed(title="💼 Hard Work Pays Off", description=f"You {job} and earned **+{earned} Gold**!", color=0x3498db)
        await interaction.response.send_message(embed=embed)

    # /deposit
    @app_commands.command(name="deposit", description="Deposit gold from wallet to secure bank")
    async def deposit(self, interaction: discord.Interaction, amount: int):
        p = self.bot.get_player(interaction.user.id)
        gold = p.get("gold", 0)

        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be greater than 0!", ephemeral=True)
            return
        if gold < amount:
            await interaction.response.send_message("❌ You don't have enough wallet gold!", ephemeral=True)
            return

        p["gold"] = gold - amount
        p["bank"] = p.get("bank", 0) + amount
        self.bot.save_player(p)

        embed = discord.Embed(title="🏦 Bank Deposit", description=f"Deposited **{amount} Gold** into your bank account!", color=0x2ecc71)
        await interaction.response.send_message(embed=embed)

    # /withdraw
    @app_commands.command(name="withdraw", description="Withdraw gold from bank to wallet")
    async def withdraw(self, interaction: discord.Interaction, amount: int):
        p = self.bot.get_player(interaction.user.id)
        bank = p.get("bank", 0)

        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be greater than 0!", ephemeral=True)
            return
        if bank < amount:
            await interaction.response.send_message("❌ You don't have enough bank gold!", ephemeral=True)
            return

        p["bank"] = bank - amount
        p["gold"] = p.get("gold", 0) + amount
        self.bot.save_player(p)

        embed = discord.Embed(title="🏦 Bank Withdrawal", description=f"Withdrew **{amount} Gold** from your bank account!", color=0xe74c3c)
        await interaction.response.send_message(embed=embed)

    # /pay
    @app_commands.command(name="pay", description="Transfer wallet gold to another player")
    async def pay(self, interaction: discord.Interaction, target: discord.User, amount: int):
        if target.id == interaction.user.id:
            await interaction.response.send_message("❌ You cannot send gold to yourself!", ephemeral=True)
            return
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be greater than 0!", ephemeral=True)
            return

        sender = self.bot.get_player(interaction.user.id)
        if sender.get("gold", 0) < amount:
            await interaction.response.send_message("❌ Insufficient wallet gold!", ephemeral=True)
            return

        receiver = self.bot.get_player(target.id)
        sender["gold"] -= amount
        receiver["gold"] = receiver.get("gold", 0) + amount

        self.bot.save_player(sender)
        self.bot.save_player(receiver)

        embed = discord.Embed(title="💸 Direct Transfer", description=f"Transferred **{amount} Gold** to {target.name}!", color=0x9b59b6)
        await interaction.response.send_message(embed=embed)

    # /leaderboard
    @app_commands.command(name="leaderboard", description="View top 5 richest players in the bot database")
    async def leaderboard(self, interaction: discord.Interaction):
        players = list(self.bot.db_players.find())
        players.sort(key=lambda x: x.get("gold", 0) + x.get("bank", 0), reverse=True)

        embed = discord.Embed(title="🏆 Global Wealth Leaderboard", color=0xf1c40f)
        for idx, pl in enumerate(players[:5], start=1):
            total = pl.get("gold", 0) + pl.get("bank", 0)
            user_str = f"<@{pl['_id']}>"
            embed.add_field(name=f"#{idx} Place", value=f"{user_str} — `{total} Gold`", inline=False)

        await interaction.response.send_message(embed=embed)

    # /pet_list
    @app_commands.command(name="pet_list", description="View available pets for adoption")
    async def pet_list(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🐾 Pet Shelter & Adoption", color=0x9b59b6)
        for key, pet in PETS.items():
            embed.add_field(
                name=f"{pet['emoji']} {pet['name']} (Option {key})",
                value=f"**Cost:** `{pet['cost']} Gold`\n**Buff:** {pet['desc']}",
                inline=False
            )
        embed.set_footer(text="Use /pet_adopt to pick your pet!")
        await interaction.response.send_message(embed=embed)

    # /pet_adopt
    @app_commands.command(name="pet_adopt", description="Adopt a companion pet")
    @app_commands.choices(pet_choice=[
        app_commands.Choice(name="🐲 Baby Dragon (500 Gold - +50% EXP)", value="1"),
        app_commands.Choice(name="🐱 Golden Cat (400 Gold - +30% Gold)", value="2"),
        app_commands.Choice(name="🐺 Shadow Wolf (600 Gold - +10 ATK)", value="3"),
        app_commands.Choice(name="🔥 Phoenix (750 Gold - Auto +15 HP Heal)", value="4")
    ])
    async def pet_adopt(self, interaction: discord.Interaction, pet_choice: str):
        p = self.bot.get_player(interaction.user.id)

        # Prevent double adoption
        if p.get("pet"):
            await interaction.response.send_message(
                f"❌ You already own a companion pet (**{p['pet']}**)! Release or change it first.",
                ephemeral=True
            )
            return

        pet = PETS.get(pet_choice)
        if not pet:
            await interaction.response.send_message("❌ Invalid pet choice!", ephemeral=True)
            return

        if p.get("gold", 0) < pet["cost"]:
            await interaction.response.send_message(f"❌ You need **{pet['cost']} Gold** to adopt {pet['name']}!", ephemeral=True)
            return

        p["gold"] -= pet["cost"]
        p["pet"] = pet["name"]
        self.bot.save_player(p)

        embed = discord.Embed(
            title="🐶 Pet Adopted!",
            description=f"Adopted **{pet['name']}** {pet['emoji']}!\n**Effect:** {pet['desc']}",
            color=0x2ecc71
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
