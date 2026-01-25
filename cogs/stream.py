import discord
import aiohttp
import asyncio
from discord.ext import commands, tasks
from datetime import datetime

class StreamCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.twitch_token = None
        self.channels = {} # {guild_id: {'channel_id': twitch_username}}
    
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def trackTwitch(self, ctx, twitch_username: str, discord_channel: discord.TextChannel):
        if discord_channel is None:
            discord_channel = ctx.channel
        if ctx.guild.id not in self.channels:
            self.channels[ctx.guild.id] = {}
        
        self.channels[ctx.guild.id][discord_channel.id] = twitch_username.lower()

        embed = discord.Embed(
            title="Twitch Tracking",
            description=f"Se notificarán los streams de **{twitch_username}** en {discord_channel.mention}",
            color=discord.Color.red()
        )
        await ctx.send(embed = embed)
    
    @tasks.loop(minutes=5)
    async def check_twitch_streams(self):
        if not self.twitch_token:
            await self.get_twitch_token()
        
        async with aiohttp.ClientSession() as session:
            for guild_id, channels in self.channels.items():
                guild = self.bot.get_guild(guild_id)
                for channel_id, twitch_user in channels.items():
                    channel = guild.get_channel(channel_id)
                    if not channel:
                        continue

                    is_live = await self.check_stream_live(session, twitch_user)
                    if is_live:
                        await self.send_live_notification(channel, is_live)
                    
    async def get_twitch_token(self):
        async with aiohttp.ClientSession() as session:
            async with session.post('https://id.twitch.tv/oauth2/token', data = {
                'client_id': '',
                'client_secret': '',
                'grant_type': 'client_credentials'
            }) as resp:
                data = await resp.json()
                self.twitch_token = f"Bearer {data['access_token']}"
    
    async def check_stream_live(self, session, username):
        if not self.twitch_token:
            return None
        
        async with session.get('https://api.twitch.tv/helix/users', headers = {'Client-ID': '', 'Authorization': self.twitch_token}, params = {'login': username}) as resp:
            user_data = await resp.json()
            if not user_data['data']:
                return None
            user_id = user_data['data'][0]['id']

        async with session.get('https://api.twitch.tv/helix/streams', headers = {'Client-ID': '', 'Authorization': self.twitch_token}, params = {'user_id': user_id}) as resp:
            stream_data = await resp.json()
            if stream_data['data']:
                stream = stream_data['data'][0]
                return {
                    'username': username,
                    'title': stream['title'],
                    'game': stream['game_name'],
                    'viewer_count': stream['viewer_count'],
                    'thumbnail_url': stream['thumbnail_url'].format(width=320, height=180),
                    'url': f"https://twitch.tv/{username}"
                }
            return None
        
        async def send_live_notification(self, channel, stream_data):
            embed = discord.Embed(
                title = f"{stream_data['username'].title()} está ahora mismo en directo!",
                description = f"**{stream_data['title']}**",
                color = discord.Color.red(),
                url = stream_data['url']
            )
            embed.add_field(name = "Jugando a ", value = stream_data['game'] or "Desconocido", inline = True)
            embed.add_field(name = "Espectadores" , value = f"{stream_data['viewer_count']:,}", inline = True)
            embed.set_image(url = stream_data['thumbnail_url'])

            await channel.send(embed = embed)

async def setup(bot):
    await bot.add_cog(StreamCog(bot))
