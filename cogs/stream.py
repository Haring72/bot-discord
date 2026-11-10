import re

import aiohttp
import discord
from discord.ext import commands, tasks

YOUTUBE_API = "https://www.googleapis.com/youtube/v3"


class YouTubeAPIError(Exception):
    """Error al consultar la API de YouTube"""


class StreamCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.twitch_token = None
        self.channels = {}
        self.stream_states = {}
        self.youtube_channels = {}
        self.youtube_states = {}
        self.check_twitch_streams.start()
        self.check_youtube_streams.start()

    def cog_unload(self):
        self.check_twitch_streams.cancel()
        self.check_youtube_streams.cancel()

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

    @commands.command(
        name="youtube-track",
        help="Track a YouTube channel's live streams",
        usage="!youtube-track <@handle | URL | channel_id> #[discord_text_channel]",
    )
    @commands.has_permissions(manage_guild=True)
    async def track_youtube(
        self, ctx, youtube_channel: str, discord_channel: discord.TextChannel = None
    ):
        try:
            async with aiohttp.ClientSession() as session:
                info = await self.resolve_youtube_channel(session, youtube_channel)
        except YouTubeAPIError as e:
            print(f"[YouTube] Error al verificar canal: {e}")
            embed = discord.Embed(
                title="Error con la API de YouTube",
                description="No se ha podido consultar YouTube ahora mismo. Inténtalo de nuevo más tarde",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return

        if info is None:
            embed = discord.Embed(
                title="Canal no encontrado / Canal no válido",
                description=f"No se ha encontrado el canal **{youtube_channel}** en YouTube. Verifica que el handle (@usuario), la URL del canal o ID estén correctamente escritos o, si crees que es un error, contacta con un administrador",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return

        if discord_channel is None:
            discord_channel = ctx.channel

        self.youtube_channels.setdefault(ctx.guild.id, {})[discord_channel.id] = info
        self.youtube_states[(ctx.guild.id, discord_channel.id)] = None

        embed = discord.Embed(
            title="YouTube Tracking Correcto",
            description=f"Se notificarán los directos de **{info['name']}** en {discord_channel.mention}",
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)

    @tasks.loop(minutes=10)
    async def check_youtube_streams(self):
        async with aiohttp.ClientSession() as session:
            for guild_id, channels in self.youtube_channels.items():
                guild = self.bot.get_guild(guild_id)

                if not guild:
                    continue

                for channel_id, yt_info in channels.items():
                    channel = guild.get_channel(channel_id)
                    if not channel:
                        continue

                    state_key = (guild_id, channel_id)

                    try:
                        live = await self.check_youtube_live(session, yt_info)
                    except YouTubeAPIError as e:
                        print(f"[YouTube] Error comprobando {yt_info['name']}: {e}")
                        continue

                    last_notified = self.youtube_states.get(state_key)

                    if live and live["video_id"] != last_notified:
                        await self.send_youtube_notification(channel, live)
                        self.youtube_states[state_key] = live["video_id"]
                    elif not live and last_notified is not None:
                        self.youtube_states[state_key] = None

    @check_youtube_streams.before_loop
    async def before_check_youtube_streams(self):
        await self.bot.wait_until_ready()

    @check_youtube_streams.error
    async def on_youtube_loop_error(self, error):
        print(f"[YouTube] Error en el loop: {error!r}")
        if not self.check_youtube_streams.is_running():
            self.check_youtube_streams.restart()

    async def _youtube_get(self, session, endpoint, params):
        api_key = (self.config or {}).get("YOUTUBE_API_KEY")
        if not api_key:
            raise YouTubeAPIError(
                "Falta 'YOUTUBE_API_KEY' en el archivo de configuración (.env)"
            )

        params = {**params, "key": api_key}
        try:
            async with session.get(f"{YOUTUBE_API}/{endpoint}", params=params) as resp:
                data = await resp.json()
                if resp.status != 200:
                    reason = data.get("error", {}).get("message", "sin detalle")
                    raise YouTubeAPIError(f"HTTP {resp.status}: {reason}")
                return data
        except aiohttp.ClientError as e:
            raise YouTubeAPIError(str(e)) from e

    async def resolve_youtube_channel(self, session, query):
        query = query.strip()

        match = re.search(r"youtube\.com/channel/(UC[\w-]{22})", query)
        if match:
            params = {"id": match.group(1)}
        elif re.fullmatch(r"UC[\w-]{22}", query):
            params = {"id": query}
        else:
            match = re.search(r"youtube\.com/(@[\w.\-]+)", query)
            handle = match.group(1) if match else query
            if not handle.startswith("@"):
                handle = f"@{handle}"
            params = {"forHandle": handle}

        data = await self._youtube_get(
            session, "channels", {**params, "part": "snippet,contentDetails"}
        )
        items = data.get("items")
        if not items:
            return None

        item = items[0]
        return {
            "id": item["id"],
            "name": item["snippet"]["title"],
            "uploads": item["contentDetails"]["relatedPlaylists"]["uploads"],
        }

    async def check_youtube_live(self, session, yt_info):
        playlist = await self._youtube_get(
            session,
            "playlistItems",
            {
                "part": "contentDetails",
                "playlistId": yt_info["uploads"],
                "maxResults": 5,
            },
        )
        video_ids = [i["contentDetails"]["videoId"] for i in playlist.get("items", [])]
        if not video_ids:
            return None

        videos = await self._youtube_get(
            session,
            "videos",
            {
                "part": "snippet,liveStreamingDetails",
                "id": ",".join(video_ids),
            },
        )

        for video in videos.get("items", []):
            snippet = video["snippet"]
            if snippet.get("liveBroadcastContent") != "live":
                continue

            details = video.get("liveStreamingDetails", {})
            thumbs = snippet.get("thumbnails", {})
            thumb = (
                thumbs.get("high")
                or thumbs.get("medium")
                or thumbs.get("default")
                or {}
            )
            viewers = details.get("concurrentViewers")

            return {
                "video_id": video["id"],
                "channel_name": yt_info["name"],
                "title": snippet["title"],
                "viewer_count": int(viewers) if viewers is not None else None,
                "thumbnail_url": thumb.get("url"),
                "url": f"https://www.youtube.com/watch?v={video['id']}",
            }

        return None

    async def send_youtube_notification(self, channel, stream_data):
        embed = discord.Embed(
            title=f"{stream_data['channel_name']} está ahora mismo en directo :D",
            description=f"**{stream_data['title']}**",
            color=discord.Color.red(),
            url=stream_data["url"],
        )
        if stream_data["viewer_count"] is not None:
            embed.add_field(
                name="Espectadores",
                value=f"{stream_data['viewer_count']:,}",
                inline=True,
            )
        if stream_data["thumbnail_url"]:
            embed.set_image(url=stream_data["thumbnail_url"])

        await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(StreamCog(bot))
