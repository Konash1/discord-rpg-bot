import discord
from discord import app_commands
from discord.ext import commands

SHOP_ITEMS = {
    "potion": {"name": "Health Potion", "price": 50, "type": "consumable"},
    "exp_scroll": {"name": "EXP Scroll", "price": 150, "type": "consumable"},
    "dagger": {"name": "Steel Dagger (+10 ATK)", "price": 100, "type": "weapon", "atk": 10},
    "iron_sword": {"name": "Iron Sword (+25 ATK)", "price": 250, "type": "weapon", "atk": 25},
    "obsidian_blade": {"name": "Obsidian Blade (+50 ATK)", "price": 600, "type": "weapon", "atk": 50}
}

class Guilds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 17. /guild_create
    @app_commands.command(name="guild_create", description="Found a new guild for 500 Gold")
    async def guild_create(self, interaction: discord.Interaction, name: str):
        p = self.bot.get_player(interaction.user.id)
        if p["guild"]:
            await interaction.response.send_message("❌ You are already in a guild!", ephemeral=True)
            return
        if p["gold"] < 500:
            await interaction.response.send_message("❌ Creating a guild costs 500 Gold!", ephemeral=True)
            return
            
        guild_data = {
            "_id": name,
            "owner_id": str(interaction.user.id),
            "members": [str(interaction.user.id)],
            "vault": 0,
            "level": 1
        }
        
        try:
            self.bot.db_guilds.insert_one(guild_data)
        except Exception:
            await interaction.response.send_message("❌ A guild with that name already exists!", ephemeral=True)
            return

        p["gold"] -= 500
        p["guild"] = name
        self.bot.save_player(p)
        
        embed = discord.Embed(title="🛡️ Guild Founded!", description=f"You successfully created **{name}**!", color=0x9b59b6)
        await interaction.response.send_message(embed=embed)

    # 18. /guild_join
    @app_commands.command(name="guild_join", description="Join an existing guild")
    async def guild_join(self, interaction: discord.Interaction, name: str):
        p = self.bot.get_player(interaction.user.id)
        if p["guild"]:
            await interaction.response.send_message("❌ You are already in a guild!", ephemeral=True)
            return
            
        guild = self.bot.db_guilds.find_one({"_id": name})
        if not guild:
            await interaction.response.send_message("❌ Guild not found!", ephemeral=True)
            return
            
        p["guild"] = name
        guild["members"].append(str(interaction.user.id))
        
        self.bot.db_guilds.replace_one({"_id": name}, guild)
        self.bot.save_player(p)
        
        embed = discord.Embed(title="🛡️ Guild Joined", description=f"You joined **{name}**!", color=0x3498db)
        await interaction.response.send_message(embed=embed)

    # 19. /guild_leave
    @app_commands.command(name="guild_leave", description="Leave your current guild")
    async def guild_leave(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        if not p["guild"]:
            await interaction.response.send_message("❌ You are not in a guild!", ephemeral=True)
            return
            
        old_guild_name = p["guild"]
        guild = self.bot.db_guilds.find_one({"_id": old_guild_name})
        
        if guild and str(interaction.user.id) in guild["members"]:
            guild["members"].remove(str(interaction.user.id))
            self.bot.db_guilds.replace_one({"_id": old_guild_name}, guild)

        p["guild"] = None
        self.bot.save_player(p)
        
        embed = discord.Embed(title="🛡️ Guild Left", description=f"You left **{old_guild_name}**.", color=0xe74c3c)
        await interaction.response.send_message(embed=embed)

    # 20. /guild_info
    @app_commands.command(name="guild_info", description="Check details and members of a guild")
    async def guild_info(self, interaction: discord.Interaction, name: str):
        guild = self.bot.db_guilds.find_one({"_id": name})
        if not guild:
            await interaction.response.send_message("❌ Guild not found!", ephemeral=True)
            return
            
        embed = discord.Embed(title=f"🛡️ Guild: {guild['_id']}", color=0x9b59b6)
        embed.add_field(name="Leader", value=f"<@{guild['owner_id']}>", inline=True)
        embed.add_field(name="Members Count", value=f"`{len(guild['members'])}`", inline=True)
        embed.add_field(name="Guild Vault", value=f"`{guild['vault']} Gold`", inline=True)
        await interaction.response.send_message(embed=embed)

    # 21. /shop
    @app_commands.command(name="shop", description="Browse and buy gear/items from the RPG Shop")
    @app_commands.choices(item=[
        app_commands.Choice(name="Health Potion (50 G)", value="potion"),
        app_commands.Choice(name="EXP Scroll (150 G)", value="exp_scroll"),
        app_commands.Choice(name="Steel Dagger (+10 ATK) (100 G)", value="dagger"),
        app_commands.Choice(name="Iron Sword (+25 ATK) (250 G)", value="iron_sword"),
        app_commands.Choice(name="Obsidian Blade (+50 ATK) (600 G)", value="obsidian_blade")
    ])
    async def shop(self, interaction: discord.Interaction, item: app_commands.Choice[str]):
        p = self.bot.get_player(interaction.user.id)
        item_info = SHOP_ITEMS[item.value]
        
        if p["gold"] < item_info["price"]:
            await interaction.response.send_message("❌ Insufficient gold balance!", ephemeral=True)
            return
            
        p["gold"] -= item_info["price"]
        p["inventory"].append(item_info["name"])
        self.bot.save_player(p)
        
        embed = discord.Embed(title="🛒 Purchase Successful", description=f"Bought **{item_info['name']}** for `{item_info['price']} Gold`!\nUse `/equip` or `/use` to activate it.", color=0x2ecc71)
        await interaction.response.send_message(embed=embed)

    # 22. /equip
    @app_commands.command(name="equip", description="Equip a weapon from your Backpack")
    async def equip(self, interaction: discord.Interaction, weapon_name: str):
        p = self.bot.get_player(interaction.user.id)
        
        matched_item = None
        for item in p["inventory"]:
            if weapon_name.lower() in item.lower() and "ATK" in item:
                matched_item = item
                break
                
        if not matched_item:
            await interaction.response.send_message("❌ Weapon not found in your Backpack!", ephemeral=True)
            return
            
        p["inventory"].remove(matched_item)
        if p["weapon"]:
            p["inventory"].append(p["weapon"])
            
        p["weapon"] = matched_item
        p["weapon_level"] = 0
        
        try:
            boost = int(matched_item.split("+")[1].split(" ")[0])
            p["bonus_atk"] = boost
        except Exception:
            p["bonus_atk"] = 5
            
        self.bot.save_player(p)
        embed = discord.Embed(title="⚔️ Weapon Equipped", description=f"Successfully equipped **{matched_item}**!", color=0xf1c40f)
        await interaction.response.send_message(embed=embed)

    # 23. /use
    @app_commands.command(name="use", description="Consume an item from your Backpack")
    @app_commands.choices(item=[
        app_commands.Choice(name="Health Potion", value="Health Potion"),
        app_commands.Choice(name="EXP Scroll", value="EXP Scroll")
    ])
    async def use(self, interaction: discord.Interaction, item: app_commands.Choice[str]):
        p = self.bot.get_player(interaction.user.id)
        if item.value not in p["inventory"]:
            await interaction.response.send_message("❌ Item not found in Backpack!", ephemeral=True)
            return
            
        p["inventory"].remove(item.value)
        
        if item.value == "Health Potion":
            p["hp"] = min(p["max_hp"], p["hp"] + 50)
            desc = f"Restored HP to **{p['hp']}/{p['max_hp']}**!"
        else:
            p["exp"] += 100
            desc = "Gained **+100 EXP**!"
            
        self.bot.save_player(p)
        embed = discord.Embed(title="🧪 Item Consumed", description=desc, color=0x3498db)
        await interaction.response.send_message(embed=embed)

    # 24. /pet_adopt
    @app_commands.command(name="pet_adopt", description="Adopt a companion pet (+50% EXP boost) for 500 Gold")
    async def pet_adopt(self, interaction: discord.Interaction):
        p = self.bot.get_player(interaction.user.id)
        if p["gold"] < 500:
            await interaction.response.send_message("❌ Pets cost 500 Gold!", ephemeral=True)
            return
            
        p["gold"] -= 500
        p["pet"] = "Baby Dragon 🐉"
        self.bot.save_player(p)
        
        embed = discord.Embed(title="🐶 Pet Adopted", description="Adopted **Baby Dragon 🐉**! Grants **+50% bonus EXP** from hunts.", color=0x9b59b6)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Guilds(bot))
