import discord
from discord.ext import commands

class TestCog(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
    
    @commands.command(name='test')
    async def test_command(self, ctx):
        await ctx.send(f'Si lees esto, el comando se ejecutó correctamente')
    
async def setup(bot):
    await bot.add_cog(TestCog(bot))
