import discord
from discord.ext import commands



class ModerationCog(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot

    @commands.command(name = 'kick', help = 'Kick a member from this server', usage = '!kick <member> [reason]')
    @commands.has_permissions(kick_members=True)
    async def kick_member(self, ctx, member: discord.Member, *, reason=None):
        await member.kick(reason=reason)
        await ctx.send(f'{member.mention} ha sido expulsado')

    @commands.command(name = 'ban', help = 'Ban a member from this server', usage = '!ban <member> [reason]')
    @commands.has_permissions(ban_members=True)
    async def ban_member(self, ctx, member: discord.Member, *, reason=None):
        await member.ban(reason=reason)
        await ctx.send(f'{member.mention} ha sido baneado')

    @commands.command(name = 'mute', help='Mute a member in this server', usage='!mute <member> [reason]')
    @commands.has_permissions(manage_roles=True)
    async def mute_member(self, ctx, member: discord.Member, *, reason=None):
        mute_role = discord.utils.get(ctx.guild.roles, name='Muted')

        if not mute_role:
            mute_role = await ctx.guild.create_role(name='Muted')
            for channel in ctx.guild.channels:
                await channel.set_permissions(mute_role, speak=False, send_messages=False, read_message_history=True, read_messages=True)
                await member.add_roles(mute_role, reason=reason)
                await ctx.send(f'{member.mention} ha sido muteado')

    @commands.command(name = 'unmute', help = 'Unmute a member in this server', usage = '!unmute <member>')
    @commands.has_permissions(manage_roles=True)
    async def unmute_member(self, ctx, member: discord.Member):
        mute_role = discord.utils.get(ctx.guild.roles, name='Muted')
        
        if mute_role in member.roles:
            await member.remove_roles(mute_role)
            await ctx.send(f'{member.mention} ha sido desmuteado')
        else:
            await ctx.send(f'{member.mention} no está muteado')

    @commands.command(name = 'clear', help = 'Clear a number of messages from a channel', usage = '!clear <amount>')
    @commands.has_permissions(manage_messages=True)
    async def clear_messages(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f'Se han eliminado {amount} mensajes', delete_after=3)


        
async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
