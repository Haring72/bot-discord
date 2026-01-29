import discord
from discord.ext import commands

class TestCog(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
    
    @commands.command(name = 'test', help = 'Testing command', usage = '!test')
    async def test_command(self, ctx):
        await ctx.send(f'Si lees esto, el comando se ejecutó correctamente')

    @commands.command(name = 'say', help = 'Send a message to a specified channel', usage = '!say #[channel_name] <message>')
    async def say_command(self, ctx, channel: discord.TextChannel, *, message: str):
        await channel.send(message)
        await ctx.send(f"Mensaje enviado a {channel.mention}")

    
async def setup(bot):
    await bot.add_cog(TestCog(bot))
