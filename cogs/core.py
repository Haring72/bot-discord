import discord
from discord.ext import commands

class Core(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
    
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
                embed.add_field(name = f"!{command.name}", value = f"{command.help}\n**Uso: **{usage}", inline = False)
            
        await ctx.send(embed = embed)

async def setup(bot):
    await bot.add_cog(Core(bot))
