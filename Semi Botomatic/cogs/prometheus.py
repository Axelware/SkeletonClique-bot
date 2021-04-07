import collections

import discord
import prometheus_client
from discord.ext import commands, tasks

import time
from bot import SemiBotomatic

OP_TYPES = {
    0:  'DISPATCH',
    1:  'HEARTBEAT',
    2:  'IDENTIFY',
    3:  'PRESENCE',
    4:  'VOICE_STATE',
    5:  'VOICE_PING',
    6:  'RESUME',
    7:  'RECONNECT',
    8:  'REQUEST_MEMBERS',
    9:  'INVALIDATE_SESSION',
    10: 'HELLO',
    11: 'HEARTBEAT_ACK',
    12: 'GUILD_SYNC',
}


# noinspection PyUnusedLocal
class Prometheus(commands.Cog):

    def __init__(self, bot: SemiBotomatic) -> None:
        self.bot = bot

        self.ready = False

        self.guild_stats = prometheus_client.Gauge('counts', documentation='Guild counters:', namespace='guild', labelnames=['id', 'count'])

        self.socket_responses = prometheus_client.Counter('socket_responses', documentation='Socket responses:', namespace='semi', labelnames=['response'])
        self.socket_events = prometheus_client.Counter('socket_events', documentation='Socket events:', namespace='semi', labelnames=['event'])

        self.counters = prometheus_client.Counter('stats', documentation='Bot stats', namespace='semi', labelnames=['stat'])
        self.gauges = prometheus_client.Gauge('counts', documentation='Bot counts', namespace='semi', labelnames=['count'])

        self.stats.start()

    #

    @commands.Cog.listener()
    async def on_socket_response(self, message: dict) -> None:

        event = message.get('t')
        if event is not None:
            self.socket_events.labels(event=event).inc()

        if (op_type := OP_TYPES.get(message.get('op'), 'UNKNOWN')) == 'HEARTBEAT_ACK':
            self.gauges.labels(count='latency').set(self.bot.latency)

        self.socket_responses.labels(response=op_type).inc()

    @commands.Cog.listener()
    async def on_ready(self) -> None:

        if self.ready is True:
            return
        self.ready = True

        self.gauges.labels(count='members').set(len(self.bot.get_all_members()))
        self.gauges.labels(count='users').set(len(self.bot.users))
        self.gauges.labels(count='guilds').set(len(self.bot.guilds))

        for guild in self.bot.guilds:
            statuses = collections.Counter([member.status for member in guild.members])
            self.guild_stats.labels(id=str(guild.id), count='online').set(statuses[discord.Status.online])
            self.guild_stats.labels(id=str(guild.id), count='offline').set(statuses[discord.Status.offline])
            self.guild_stats.labels(id=str(guild.id), count='idle').set(statuses[discord.Status.idle])
            self.guild_stats.labels(id=str(guild.id), count='dnd').set(statuses[discord.Status.dnd])

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:

        self.gauges.labels(count='members').inc()
        self.gauges.labels(count='users').set(len(self.bot.users))

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:

        self.gauges.labels(count='members').dec()
        self.gauges.labels(count='users').set(len(self.bot.users))

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:

        if before.status != after.status:
            self.guild_stats.labels(id=str(after.guild.id), count=str(before.status)).dec()
            self.guild_stats.labels(id=str(after.guild.id), count=str(after.status)).inc()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:

        self.gauges.labels(count='members').inc(len(guild.members))
        self.gauges.labels(count='users').set(len(self.bot.users))
        self.gauges.labels(count='guilds').inc()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:

        self.gauges.labels(count='members').dec(len(guild.members))
        self.gauges.labels(count='users').set(len(self.bot.users))
        self.gauges.labels(count='guilds').dec()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        self.counters.labels(stat='messages').inc()

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context) -> None:
        self.counters.labels(stat='commands').inc()

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context) -> None:
        self.counters.labels(stat='commands_completed').inc()

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error) -> None:

        error = getattr(error, 'original', error)
        if isinstance(error, (commands.CommandNotFound, commands.CommandOnCooldown, commands.MaxConcurrencyReached, commands.CheckFailure)):
            return

        self.counters.labels(stat='commands_errored').inc()

    #

    @tasks.loop(seconds=30)
    async def stats(self) -> None:

        self.gauges.labels(count='uptime').set(round(time.time() - self.bot.start_time))
        self.gauges.labels(count='threads').set(self.bot.process.num_threads())
        self.gauges.labels(count='cpu').set(self.bot.process.cpu_percent(interval=None))

        with self.bot.process.oneshot():
            memory_info = self.bot.process.memory_full_info()
            self.gauges.labels(count='physical_memory').set(memory_info.rss)
            self.gauges.labels(count='virtual_memory').set(memory_info.vms)
            self.gauges.labels(count='unique_memory').set(memory_info.uss)

        for guild in self.bot.guilds:

            statuses = collections.Counter([member.status for member in guild.members])
            self.guild_stats.labels(id=str(guild.id), count='online').set(statuses[discord.Status.online])
            self.guild_stats.labels(id=str(guild.id), count='offline').set(statuses[discord.Status.offline])
            self.guild_stats.labels(id=str(guild.id), count='idle').set(statuses[discord.Status.idle])
            self.guild_stats.labels(id=str(guild.id), count='dnd').set(statuses[discord.Status.dnd])

    @stats.before_loop
    async def stats_before_loop(self) -> None:
        await self.bot.wait_until_ready()


def setup(bot: SemiBotomatic) -> None:
    bot.add_cog(cog=Prometheus(bot))
