import discord
import aiohttp
from discord.ext import commands, tasks
from datetime import datetime

class StreamCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.twitch_token = None
        self.channels = {}
        self.stream_states = {}
        self.check_twitch_streams.start()

    def cog_unload(self):
        self.check_twitch_streams.cancel()

    @commands.command(name = 'twitch-track', help = "Track a Twitch user's stream", usage = '!twitch-track <twitch_username> #[discord_text_channel]')
    @commands.has_permissions(manage_guild=True)
    async def track_twitch(self, ctx, twitch_username: str, discord_channel: discord.TextChannel = None):
        twitch_username = twitch_username.lower().strip()

        if not await self.verify_twitch_user(twitch_username):
            embed = discord.Embed(
                title = "Usuario no encontrado / Usuario no válido",
                description = f"No se ha encontrado al usuario **{twitch_username}** en Twitch. Verifica que se ha escrito correctamente o, si crees que es un error, contacta con un administrador",
                color = discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if discord_channel is None:
            discord_channel = ctx.channel

        if ctx.guild.id not in self.channels:
            self.channels[ctx.guild.id] = {}

        self.channels[ctx.guild.id][discord_channel.id] = twitch_username
        self.stream_states[(ctx.guild.id, discord_channel.id)] = False

        embed = discord.Embed(
            title = "Twitch Tracking Correcto",
            description = f"Se notificarán los streams de **{twitch_username}** en {discord_channel.mention}",
            color = discord.Color.purple()
        )
        await ctx.send(embed=embed)

    @tasks.loop(minutes = 10)
    async def check_twitch_streams(self):
        if not self.twitch_token:
            await self.get_twitch_token()

        async with aiohttp.ClientSession() as session:
            for guild_id, channels in self.channels.items():
                guild = self.bot.get_guild(guild_id)

                if not guild:
                    continue

                for channel_id, twitch_user in channels.items():
                    channel = guild.get_channel(channel_id)
                    if not channel:
                        continue

                    is_live = await self.check_stream_live(session, twitch_user)
                    state_key = (guild_id, channel_id)

                    if is_live and not self.stream_states.get(state_key, False):
                        await self.send_live_notification(channel, is_live)
                        self.stream_states[state_key] = True
                    elif not is_live and self.stream_states.get(state_key, False):
                        self.stream_states[state_key] = False

    async def verify_twitch_user(self, username):
        try:
            async with aiohttp.ClientSession() as session:
                if not self.config:
                    return False

                headers = {
                    'Client-ID': self.config['twitch_app_credentials']['client_id'],
                    'Authorization': self.twitch_token
                }

                async with session.get('https://api.twitch.tv/helix/users', headers = headers, params = {'login': username}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return bool(data.get('data'))
                    return False
        except Exception:
            return False

    async def get_twitch_token(self):
        async with aiohttp.ClientSession() as session:
            async with session.post('https://id.twitch.tv/oauth2/token', data={
                    'client_id': self.config['twitch_app_credentials']['client_id'],
                    'client_secret': self.config['twitch_app_credentials']['client_secret'],
                    'grant_type': 'client_credentials'
                }) as resp:
                data = await resp.json()
                self.twitch_token = f"Bearer {data['access_token']}"
                print("Twitch token obtained.")
                print(f"Token expires in {data['expires_in']} seconds.")

    async def check_stream_live(self, session, username):
        if not self.twitch_token or not self.config:
            return None

        headers = {
            'Client-ID': self.config['twitch_app_credentials']['client_id'],
            'Authorization': self.twitch_token
        }

        async with session.get('https://api.twitch.tv/helix/users', headers = headers, params = {'login': username}) as resp:
            user_data = await resp.json()

            if not user_data['data']:
                return None
            user_id = user_data['data'][0]['id']

        async with session.get('https://api.twitch.tv/helix/streams', headers = headers, params = {'user_id': user_id}) as resp:
            stream_data = await resp.json()

            if stream_data.get('data'):
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
            color = discord.Color.purple(),
            url = stream_data['url']
        )
        embed.add_field(name = "Jugando a ", value = stream_data['game'] or "Desconocido", inline = True)
        embed.add_field(name = "Espectadores", value = f"{stream_data['viewer_count']:,}", inline = True)
        embed.set_image(url = stream_data['thumbnail_url'])

        await channel.send(embed = embed)

async def setup(bot):
    await bot.add_cog(StreamCog(bot))
