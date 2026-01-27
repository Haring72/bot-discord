import discord
import os
import json
from discord.ext import commands
from datetime import datetime, timedelta

class Core(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
        self.xp_file = "cog_data/users_xp.json"
        self.cooldown = {}
        self.load_xp_data()
    
    def load_xp_data(self):
        if not os.path.exists("cog_data"):
            os.makedirs("cog_data")
        if not os.path.exists(self.xp_file):
            with open(self.xp_file, 'w') as f:
                json.dump({}, f)

    def get_xp_data(self):
        with open(self.xp_file, 'r') as f:
            return json.load(f)

    def save_xp_data(self, data): 
        with open(self.xp_file, 'w') as f:
            json.dump(data, f, indent = 4)
    
    def add_xp(self, user_id, xp_amount):
        data = self.get_xp_data()
        user_id_str = str(user_id)

        if user_id_str not in data:
            data[user_id_str] = {"xp": 0, "level": 1}

        data[user_id_str]["xp"] += xp_amount

        xp_needed = data[user_id_str]["level"] * 100

        if data[user_id_str]["xp"] >= xp_needed:
            data[user_id_str]["level"] += 1
            data[user_id_str]["xp"] = 0
        
        self.save_xp_data(data)
        return data[user_id_str]
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        user_id = message.author.id
        now = datetime.now()

        if user_id in self.cooldown:
            if now < self.cooldown[user_id]:
                return
        
        self.cooldown[user_id] = now + timedelta(seconds = 30)
        self.add_xp(user_id, 10)
    
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
        data = self.get_xp_data()
        user_data = data.get(str(member.id), {"xp": 0, "level": 1})

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
