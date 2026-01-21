import discord
from discord.ext import commands

class Core(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        welcome_channel = discord.utils.get(member.guild.text_channels, name='welcome_channel_name')
        thumbnail_url = member.avatar.url if member.avatar else member.default_avatar.url
        if welcome_channel:
            embed = discord.Embed(
                title="Bienvenido!",
                description=f"Hola {member.mention}, bienvenido a este servidor",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=thumbnail_url)
            await welcome_channel.send(embed=embed)
        
async def setup(bot):
    await bot.add_cog(Core(bot))
