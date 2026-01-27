import discord
import os
import json
from discord.ext import commands
from datetime import datetime, timedelta



XP_FILE = "cog_data/users_xp.json"
XP_COOLDOWN_SECONDS = 30
XP_PER_MESSAGE = 10
XP_PER_LEVEL = 100



class XPManager:
    def __init__(self, xp_file: str = XP_FILE):
        self.xp_file = xp_file
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        os.makedirs(os.path.dirname(self.xp_file), exist_ok = True)
        if not os.path.exists(self.xp_file):
            with open(self.xp_file, 'w') as f:
                json.dump({}, f)
    
    def get_data(self) -> dict:
        with open(self.xp_file, 'r') as f:
            return json.load(f)
    
    def save_data(self, data: dict):
        with open(self.xp_file, 'w') as f:
            json.dump(data, f, indent = 4)
    
    def calculate_level_up(self, current_level: int) -> int:
        return current_level * XP_PER_LEVEL
    
    def add_xp(self, user_id: int, xp_amount: int) -> dict:
        data = self.get_data()
        user_id_str = str(user_id)

        if user_id_str not in data:
            data[user_id_str] = {"xp": 0, "level": 1}
        
        data[user_id_str]["xp"] += xp_amount
        xp_needed = self.calculate_level_up(data[user_id_str]["level"])

        if data[user_id_str]["xp"] >= xp_needed:
            data[user_id_str]["level"] += 1
            data[user_id_str]["xp"] = 0
        
        self.save_data(data)
        return data[user_id_str]
    
    def get_user_data(self, user_id: int) -> dict:
        data = self.get_data()
        return data.get(str(user_id), {"xp": 0, "level": 1})
    


class Core(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
        self.xp_manager = XPManager()
        self.cooldown = {}
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        user_id = message.author.id
        now = datetime.now()

        if user_id in self.cooldown and now < self.cooldown[user_id]:
            return
        
        self.cooldown[user_id] = now + timedelta(seconds = XP_COOLDOWN_SECONDS)
        self.xp_manager.add_xp(user_id, XP_PER_MESSAGE)
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        welcome_channel = discord.utils.get(member.guild.text_channels, name = 'welcome_channel_name')
        thumbnail_url = member.avatar.url if member.avatar else member.default_avatar.url
        
        if welcome_channel:
            embed = discord.Embed(
                title = "Bienvenido!",
                description = f"Hola {member.mention}, bienvenido a este servidor",
                color = discord.Color.red()
            )
            embed.set_thumbnail(url = thumbnail_url)
            await welcome_channel.send(embed = embed)

    @commands.command(name = 'help', help = 'Show this help message', usage = '!help')
    async def custom_help_command(self, ctx):
        embed = discord.Embed(
            title = "Comandos disponibles",
            color = discord.Color.red()
        )

        for command in self.bot.commands:
            if command.help:
                usage = f"`{command.usage}`" if command.usage else "No usage provided"
                embed.add_field(name = f"--- !{command.name}", value = f"{command.help}\n**Uso: **{usage}", inline = False)
            
        await ctx.send(embed = embed)
    
    @commands.command(name = 'level', help = 'Check your current level and XP', usage = '!level [@member]')
    async def level_command(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_data = self.xp_manager.get_user_data(member.id)

        embed = discord.Embed(
            title = f"Nivel de {member.name}",
            color = discord.Color.red()
        )
        embed.add_field(name = "Nivel", value = user_data["level"], inline = True)
        embed.add_field(name = "XP", value = user_data["xp"], inline = True)
        embed.set_thumbnail(url = member.avatar.url if member.avatar else member.default_avatar.url)

        await ctx.send(embed = embed)

async def setup(bot):
    await bot.add_cog(Core(bot))
