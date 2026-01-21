import discord
from discord.ext import commands



class CoreCog(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        welcome_channel = discord.utils.get(member.guild.text_channels, name='welcome_channel_name')
        if welcome_channel:
            embed = discord.Embed(
                title="Bienvenido al servidor! :D",
                description=f"Hola {member.mention}, ¡nos alegra tenerte aquí!",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=member.avatar.url)
            await welcome_channel.send(embed=embed)
        


async def setup(bot):
    await bot.add_cog(CoreCog(bot))
