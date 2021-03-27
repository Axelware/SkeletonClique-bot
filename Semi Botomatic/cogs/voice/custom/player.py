import asyncio
import logging
import re
from typing import List, Optional

import async_timeout
import discord
import spotify
import yarl
from spotify.errors import HTTPException

import config
import slate
from bot import SemiBotomatic
from cogs.voice.custom import objects, queue
from utilities import context, enums, exceptions, utils

__log__ = logging.getLogger('slate.player')


class Player(slate.BasePlayer):

    def __init__(self, bot: SemiBotomatic, channel: discord.VoiceChannel) -> None:
        super().__init__(bot, channel)

        self.queue = queue.Queue(player=self)

        self.queue_add_event = asyncio.Event()
        self.track_start_event = asyncio.Event()
        self.track_end_event = asyncio.Event()

        self.skip_requests: List[int] = []

        self.text_channel: Optional[discord.TextChannel] = None
        self.task: Optional[asyncio.Task] = None

        self.spotify_url_regex = re.compile(r'https?://open.spotify.com/(?P<type>album|playlist|track)/(?P<id>[a-zA-Z0-9]+)')

    #

    async def connect(self, *, timeout: float, reconnect: bool) -> None:

        await self.guild.change_voice_state(channel=self.channel, self_deaf=True)
        __log__.info(f'PLAYER | Guild player \'{self.guild.id}\' joined channel \'{self.channel.id}\'.')

        self.task = self.bot.loop.create_task(self.player_loop())

    async def disconnect(self, *, force: bool = False) -> None:

        if not self.is_connected and not force:
            return

        await self.guild.change_voice_state(channel=None)
        __log__.info(f'PLAYER | Guild player \'{self.guild.id}\' disconnected from voice channel \'{self.channel.id}\'.')

        self.task.cancel()
        self.task = None
        self.channel = None

    async def reconnect(self, *, channel: discord.VoiceChannel) -> None:

        if not isinstance(channel, discord.VoiceChannel):
            raise slate.SlateException

        self.channel = channel

        await self.guild.change_voice_state(channel=self.channel, self_deaf=True)
        __log__.info(f'PLAYER | Guild player \'{self.guild.id}\' joined channel \'{self.channel}\'.')

        self.task = self.bot.loop.create_task(self.player_loop())

    async def destroy(self, *, force: bool = False) -> None:

        await self.disconnect(force=force)
        await self.cleanup()

        if self.node.is_connected:
            await self.stop(force=force)
            await self.node._send(op='destroy', guildId=str(self.guild.id))

        del self.node.players[self.guild.id]
        __log__.info(f'PLAYER | Guild player \'{self.guild.id}\' was destroyed.')


    #

    async def invoke_controller(self) -> None:

        embed = discord.Embed(colour=self.current.ctx.colour)
        embed.set_thumbnail(url=self.current.thumbnail)
        embed.add_field(name=f'Now playing:', value=f'**[{self.current.title}]({self.current.uri})**', inline=False)

        queue_time = utils.format_seconds(seconds=round(sum(track.length for track in self.queue)) // 1000, friendly=True)

        if self.current.ctx.guild_config.embed_size == enums.EmbedSize.LARGE:

            embed.add_field(name='Player info:',
                            value=f'`Volume:` {self.volume}\n`Paused:` {self.is_paused}\n`Looping:` {self.queue.is_looping}\n`Looping current:` {self.queue.is_looping_current}\n'
                                  f'`Queue entries:` {len(self.queue)}\n`Queue time:` {queue_time}')
            embed.add_field(name='Track info:',
                            value=f'`Time:` {utils.format_seconds(seconds=round(self.position) // 1000)} / '
                                  f'{utils.format_seconds(seconds=round(self.current.length) // 1000)}\n`Author:` {self.current.author}\n`Source:` {self.current.source}\n'
                                  f'`Requester:` {self.current.requester.mention}\n`Live:` {self.current.is_stream}\n`Seekable:` {self.current.is_seekable}')

            if not self.queue.is_empty:
                entries = [f'`{index + 1}.` [{entry.title}]({entry.uri}) | {utils.format_seconds(seconds=round(entry.length) // 1000)} | {entry.requester.mention}'
                           for index, entry in enumerate(self.queue[:5])]

                if len(self.queue) > 5:
                    entries.append(f'`...`\n`{len(self.queue)}.` [{self.queue[-1].title}]({self.queue[-1].uri}) | '
                                   f'{utils.format_seconds(seconds=round(self.queue[-1].length) // 1000)} | {self.queue[-1].requester.mention}')

                embed.add_field(name='Up next:', value='\n'.join(entries), inline=False)

        if self.current.ctx.guild_config.embed_size == enums.EmbedSize.MEDIUM:

            embed.add_field(name='Player info:',
                            value=f'`Volume:` {self.volume}\n`Paused:` {self.is_paused}\n`Looping:` {self.queue.is_looping}\n`Looping current:` {self.queue.is_looping_current}\n')
            embed.add_field(name='Track info:',
                            value=f'`Time:` {utils.format_seconds(seconds=round(self.position) // 1000)} / '
                                  f'{utils.format_seconds(seconds=round(self.current.length) // 1000)}\n`Author:` {self.current.author}\n`Source:` {self.current.source}\n'
                                  f'`Requester:` {self.current.requester.mention}\n')

        await self.send(embed=embed)

    async def send(self, *, message: str = None, embed: discord.Embed = None) -> None:

        if not self.text_channel:
            return

        if message:
            await self.text_channel.send(message)
        if embed:
            await self.text_channel.send(embed=embed)

    #

    async def search(self, query: str, ctx: context.Context) -> objects.SearchResult:

        search_result = None
        search_tracks = None

        spotify_url_check = self.spotify_url_regex.match(query)
        if spotify_url_check is not None:

            source = 'spotify'

            spotify_client: spotify.Client = self.bot.cogs["Music"].spotify
            spotify_http_client: spotify.HTTPClient = self.bot.cogs["Music"].spotify_http

            search_type = spotify_url_check.group('type')
            spotify_id = spotify_url_check.group('id')

            try:
                if search_type == 'album':
                    search_result = await spotify_client.get_album(spotify_id=spotify_id)
                    search_tracks = await search_result.get_all_tracks()
                elif search_type == 'playlist':
                    search_result = spotify.Playlist(client=spotify_client, data=await spotify_http_client.get_playlist(spotify_id))
                    search_tracks = await search_result.get_all_tracks()
                elif search_type == 'track':
                    search_result = await spotify_client.get_track(spotify_id=spotify_id)
                    search_tracks = [search_result]

            except spotify.NotFound or HTTPException:
                raise exceptions.VoiceError(f'No results were found for your Spotify link.')
            if not search_tracks:
                raise exceptions.VoiceError(f'No results were found for your Spotify link.')

            tracks = [
                slate.Track(
                        track_id='',
                        ctx=ctx,
                        track_info={'title': track.name or 'Unknown', 'author': ', '.join(artist.name for artist in track.artists) or 'Unknown',
                                    'length': track.duration or 0, 'identifier': track.id or 'Unknown', 'uri': track.url or 'spotify',
                                    'isStream': False, 'isSeekable': False, 'position': 0, 'thumbnail': track.images[0].url if track.images else None},
                ) for track in search_tracks
            ]

        else:

            url = yarl.URL(query)
            if not url.host or not url.scheme:
                if query.startswith('soundcloud'):
                    query = f'scsearch:{query[11:]}'
                else:
                    query = f'ytsearch:{query}'

            try:
                search_result = await self.node.search(query=query, ctx=ctx)
            except slate.TrackLoadError as error:
                raise exceptions.VoiceError(f'`{error.status_code}` error code while searching for results. For support use `{config.PREFIX}support`.')
            except slate.TrackLoadFailed as error:
                raise exceptions.VoiceError(f'`{error.severity}` error while searching for results. For support use `{config.PREFIX}support`.\nReason: `{error.message}`')

            if not search_result:
                raise exceptions.VoiceError(f'No results were found for your search.')

            if isinstance(search_result, slate.Playlist):
                source = 'youtube'
                search_type = 'playlist'
                tracks = search_result.tracks
            else:
                source = search_result[0].source
                search_type = 'track'
                tracks = search_result

        return objects.SearchResult(source=source, search_type=search_type, search_result=search_result, tracks=tracks)

    #

    async def player_loop(self) -> None:

        while True:

            self.queue_add_event.clear()
            self.track_start_event.clear()
            self.track_end_event.clear()

            if self.queue.is_empty:

                timeout = 120

                try:
                    with async_timeout.timeout(timeout=timeout):
                        await self.queue_add_event.wait()
                except asyncio.TimeoutError:
                    await self.send(message=f'No tracks were added to the queue for `{timeout}s`. The player has disconnected temporarily.')
                    await self.stop()
                    await self.disconnect()
                    break

            track = self.queue.get()

            if track.source == 'Spotify':
                try:
                    search = await self.search(query=f'{track.author} - {track.title}', ctx=track.ctx)
                except exceptions.VoiceError as error:
                    await self.send(message=f'{error}')
                    continue
                track = search.tracks[0]

            await self.play(track=track)

            try:
                with async_timeout.timeout(timeout=10):
                    await self.track_start_event.wait()
            except asyncio.TimeoutError:
                await self.send(message=f'Something went wrong while starting the track `{track.title}`. Use `{config.PREFIX}support` for help.')
                continue

            await self.track_end_event.wait()

            if self.queue.is_looping:
                self.queue.put(items=track, position=0 if self.queue.is_looping_current else None)

            self._current = None
