import aiohttp
import discord
from discord.ext import commands, tasks


class StreamCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.twitch_token = None
        self.youtube_api_key = self._get_youtube_api_key()
        self.channels = {}
        self.stream_states = {}
        self.youtube_channels = {}
        self.youtube_stream_states = {}
        self.check_twitch_streams.start()
        self.check_youtube_streams.start()

    def cog_unload(self):
        self.check_twitch_streams.cancel()
        self.check_youtube_streams.cancel()

    def _get_youtube_api_key(self):
        if isinstance(self.config, dict):
            for key in ("youtube_api_key", "YOUTUBE_API_KEY"):
                value = self.config.get(key)
                if value:
                    print(f"YouTube API Key obtained {value}")
                    return value

            youtube_cfg = self.config.get("youtube", {})
            if isinstance(youtube_cfg, dict):
                value = youtube_cfg.get("api_key")
                if value:
                    print("YouTube API Key obtained")
                    return value

        return None

    @commands.command(
        name="twitch-track",
        help="Track a Twitch user's stream",
        usage="!twitch-track <twitch_username> #[discord_text_channel]",
    )
    @commands.has_permissions(manage_guild=True)
    async def track_twitch(
        self, ctx, twitch_username: str, discord_channel: discord.TextChannel = None
    ):
        twitch_username = twitch_username.lower().strip()

        if not await self.verify_twitch_user(twitch_username):
            embed = discord.Embed(
                title="Usuario no encontrado / Usuario no válido",
                description=f"No se ha encontrado al usuario **{twitch_username}** en Twitch. Verifica que se ha escrito correctamente o, si crees que es un error, contacta con un administrador",
                color=discord.Color.red(),
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
            title="Twitch Tracking Correcto",
            description=f"Se notificarán los streams de **{twitch_username}** en {discord_channel.mention}",
            color=discord.Color.purple(),
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="youtube-track",
        help="Track a YouTube channel live status",
        usage="!youtube-track <youtube_channel_id_or_handle> #[discord_text_channel]",
    )
    @commands.has_permissions(manage_guild=True)
    async def track_youtube(
        self, ctx, youtube_channel: str, discord_channel: discord.TextChannel = None
    ):
        youtube_channel = youtube_channel.strip()

        channel_id = await self.resolve_youtube_channel_id(youtube_channel)
        if not channel_id:
            embed = discord.Embed(
                title="Canal de YouTube no encontrado / no válido",
                description=f"No se ha encontrado el canal **{youtube_channel}** en YouTube. Usa el ID del canal o el handle tipo `@canal`.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return

        if discord_channel is None:
            discord_channel = ctx.channel

        if ctx.guild.id not in self.youtube_channels:
            self.youtube_channels[ctx.guild.id] = {}

        self.youtube_channels[ctx.guild.id][discord_channel.id] = channel_id
        self.youtube_stream_states[(ctx.guild.id, discord_channel.id)] = False

        embed = discord.Embed(
            title="YouTube Tracking Correcto",
            description=f"Se notificarán los directos del canal **{youtube_channel}** en {discord_channel.mention}",
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)

    @tasks.loop(minutes=10)
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

    @tasks.loop(minutes=10)
    async def check_youtube_streams(self):
        if not self.youtube_api_key:
            self.youtube_api_key = self._get_youtube_api_key()
            if not self.youtube_api_key:
                return

        async with aiohttp.ClientSession() as session:
            for guild_id, channels in self.youtube_channels.items():
                guild = self.bot.get_guild(guild_id)

                if not guild:
                    continue

                for channel_id, youtube_channel_id in channels.items():
                    channel = guild.get_channel(channel_id)
                    if not channel:
                        continue

                    stream_data = await self.check_youtube_live(
                        session, youtube_channel_id
                    )
                    state_key = (guild_id, channel_id)

                    if stream_data and not self.youtube_stream_states.get(
                        state_key, False
                    ):
                        await self.send_youtube_live_notification(channel, stream_data)
                        self.youtube_stream_states[state_key] = True
                    elif not stream_data and self.youtube_stream_states.get(
                        state_key, False
                    ):
                        self.youtube_stream_states[state_key] = False

    async def resolve_youtube_channel_id(self, value):
        if not value:
            return None

        value = value.strip()

        if value.startswith(("http://", "https://")):
            parsed = (
                value.split("youtube.com/")[1] if "youtube.com/" in value else value
            )
            if "/channel/" in parsed:
                return parsed.split("/channel/")[1].split("/")[0]
            if "/@/" in parsed:
                return await self.get_channel_id_from_handle(
                    parsed.split("/@/")[1].split("/")[0]
                )
            return None

        if value.startswith("@"):
            return await self.get_channel_id_from_handle(value[1:])

        if value.startswith("UC") and len(value) >= 24:
            return value

        return await self.get_channel_id_from_handle(value)

    async def get_channel_id_from_handle(self, handle):
        if not self.youtube_api_key:
            return None

        url = "https://www.googleapis.com/youtube/v3/channels"
        params = {"part": "id", "forHandle": handle, "key": self.youtube_api_key}

        async with (
            aiohttp.ClientSession() as session,
            session.get(url, params=params) as resp,
        ):
            if resp.status != 200:
                return None
            data = await resp.json()
            items = data.get("items", [])
            if not items:
                return None
            return items[0].get("id")

    async def verify_twitch_user(self, username):
        async with aiohttp.ClientSession() as session:
            if not self.config:
                return False

            headers = {
                "Client-ID": self.config["twitch_app_credentials"]["client_id"],
                "Authorization": self.twitch_token,
            }

            async with session.get(
                "https://api.twitch.tv/helix/users",
                headers=headers,
                params={"login": username},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return bool(data.get("data"))
                return False

    async def get_twitch_token(self):
        async with (
            aiohttp.ClientSession() as session,
            session.post(
                "https://id.twitch.tv/oauth2/token",
                data={
                    "client_id": self.config["twitch_app_credentials"]["client_id"],
                    "client_secret": self.config["twitch_app_credentials"][
                        "client_secret"
                    ],
                    "grant_type": "client_credentials",
                },
            ) as resp,
        ):
            data = await resp.json()
            self.twitch_token = f"Bearer {data['access_token']}"
            print("Twitch token obtained.")
            print(f"Token expires in {data['expires_in']} seconds.")

    async def check_stream_live(self, session, username):
        if not self.twitch_token or not self.config:
            return None

        headers = {
            "Client-ID": self.config["twitch_app_credentials"]["client_id"],
            "Authorization": self.twitch_token,
        }

        async with session.get(
            "https://api.twitch.tv/helix/users",
            headers=headers,
            params={"login": username},
        ) as resp:
            user_data = await resp.json()

            if not user_data["data"]:
                return None
            user_id = user_data["data"][0]["id"]

        async with session.get(
            "https://api.twitch.tv/helix/streams",
            headers=headers,
            params={"user_id": user_id},
        ) as resp:
            stream_data = await resp.json()

            if stream_data.get("data"):
                stream = stream_data["data"][0]
                return {
                    "username": username,
                    "title": stream["title"],
                    "game": stream["game_name"],
                    "viewer_count": stream["viewer_count"],
                    "thumbnail_url": stream["thumbnail_url"].format(
                        width=320, height=180
                    ),
                    "url": f"https://twitch.tv/{username}",
                }

            return None

    async def check_youtube_live(self, session, channel_id):
        if not self.youtube_api_key:
            return None

        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "channelId": channel_id,
            "eventType": "live",
            "type": "video",
            "maxResults": 1,
            "key": self.youtube_api_key,
        }

        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                return None

            data = await resp.json()
            items = data.get("items", [])

            if not items:
                return None

            item = items[0]
            video_id = item["id"]["videoId"]
            snippet = item["snippet"]

            return {
                "channel_title": snippet.get("channelTitle") or "YouTube",
                "title": snippet.get("title"),
                "thumbnail_url": (
                    snippet.get("thumbnails", {}).get("high", {}).get("url")
                    or snippet.get("thumbnails", {}).get("default", {}).get("url")
                ),
                "url": f"https://youtu.be/{video_id}",
            }

    async def send_live_notification(self, channel, stream_data):
        embed = discord.Embed(
            title=f"{stream_data['username'].title()} está ahora mismo en directo!",
            description=f"**{stream_data['title']}**",
            color=discord.Color.purple(),
            url=stream_data["url"],
        )
        embed.add_field(
            name="Jugando a ", value=stream_data["game"] or "Desconocido", inline=True
        )
        embed.add_field(
            name="Espectadores", value=f"{stream_data['viewer_count']:,}", inline=True
        )
        embed.set_image(url=stream_data["thumbnail_url"])

        await channel.send(embed=embed)

    async def send_youtube_live_notification(self, channel, stream_data):
        embed = discord.Embed(
            title=f"{stream_data['channel_title']} está en directo en YouTube",
            description=f"**{stream_data['title']}**",
            color=discord.Color.red(),
            url=stream_data["url"],
        )
        embed.set_image(url=stream_data["thumbnail_url"])
        await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(StreamCog(bot))
