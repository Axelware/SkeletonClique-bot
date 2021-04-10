import collections
import sys

import discord
import humanize
import pkg_resources
import setproctitle
from discord.ext import commands

import config
import time
from bot import SemiBotomatic
from utilities import context, converters, exceptions


class Dev(commands.Cog):

    def __init__(self, bot: SemiBotomatic) -> None:
        self.bot = bot

    @commands.is_owner()
    @commands.group(name='dev', hidden=True, invoke_without_command=True)
    async def dev(self, ctx: context.Context) -> None:
        """
        Base command for bot developer commands.

        Displays a message with stats about the bot.
        """

        python_version = f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'
        discordpy_version = pkg_resources.get_distribution('discord.py').version
        platform = sys.platform
        process_name = setproctitle.getproctitle()
        process_id = self.bot.process.pid
        thread_count = self.bot.process.num_threads()

        description = [f'I am running on the python version **{python_version}** on the OS **{platform}** using the discord.py version **{discordpy_version}**. '
                       f'The process is running as **{process_name}** on PID **{process_id}** and is using **{thread_count}** threads.']

        if isinstance(self.bot, commands.AutoShardedBot):
            description.append(f'The bot is automatically sharded with **{self.bot.shard_count}** shard(s) and can see **{len(self.bot.guilds)}** guilds and '
                               f'**{len(self.bot.users)}** users.')
        else:
            description.append(f'The bot is not sharded and can see **{len(self.bot.guilds)}** guilds and **{len(self.bot.users)}** users.')

        with self.bot.process.oneshot():

            memory_info = self.bot.process.memory_full_info()
            physical_memory = humanize.naturalsize(memory_info.rss)
            virtual_memory = humanize.naturalsize(memory_info.vms)
            unique_memory = humanize.naturalsize(memory_info.uss)
            cpu_usage = self.bot.process.cpu_percent(interval=None)

            description.append(f'The process is using **{physical_memory}** of physical memory, **{virtual_memory}** of virtual memory and **{unique_memory}** of memory '
                               f'that is unique to the process. It is also using **{cpu_usage}%** of CPU.')

        embed = discord.Embed(title=f'{self.bot.user.name} bot information page.', colour=0xF5F5F5)
        embed.description = '\n\n'.join(description)

        await ctx.send(embed=embed)

    @commands.is_owner()
    @dev.command(name='cleanup', aliases=['clean'], hidden=True)
    async def dev_cleanup(self, ctx: context.Context, limit: int = 50) -> None:
        """
        Clean up the bots messages.

        `limit`: The amount of messages to check back through. Defaults to 50.
        """

        if ctx.channel.permissions_for(ctx.me).manage_messages:
            messages = await ctx.channel.purge(check=lambda message: message.author == ctx.me or message.content.startswith(config.PREFIX), bulk=True, limit=limit)
        else:
            messages = await ctx.channel.purge(check=lambda message: message.author == ctx.me, bulk=False, limit=limit)

        await ctx.send(f'Found and deleted `{len(messages)}` of my message(s) out of the last `{limit}` message(s).', delete_after=3)

    @commands.is_owner()
    @dev.command(name='socketstats', aliases=['ss'], hidden=True)
    async def dev_socket_stats(self, ctx: context.Context) -> None:
        """
        Displays a list of socket event counts since bot startup.
        """

        event_stats = collections.OrderedDict(sorted(self.bot.socket_stats.items(), key=lambda kv: kv[1], reverse=True))
        events_total = sum(event_stats.values())
        events_per_second = round(events_total / round(time.time() - self.bot.start_time))

        description = [f'```py\n{events_total} socket events observed at a rate of {events_per_second} per second.\n']

        for event, count in event_stats.items():
            description.append(f'{event:29} | {count}')

        description.append('```')

        embed = discord.Embed(title=f'{self.bot.user.name} socket stats.', colour=ctx.colour, description='\n'.join(description))
        await ctx.send(embed=embed)

    @dev.group(name='blacklist', aliases=['bl'], hidden=True, invoke_without_command=True)
    async def dev_blacklist(self, ctx: context.Context) -> None:
        """
        Base command for blacklisting.
        """

        await ctx.send(f'Choose a valid subcommand. Use `{config.PREFIX}help dev blacklist` for more information.')

    @dev_blacklist.group(name='users', aliases=['user', 'u'], hidden=True, invoke_without_command=True)
    async def dev_blacklist_users(self, ctx: context.Context) -> None:
        """
        Display a list of blacklisted users.
        """

        blacklisted = [user_config for user_config in self.bot.user_manager.configs.values() if user_config.blacklisted is True]
        if not blacklisted:
            raise exceptions.ArgumentError('There are no blacklisted users.')

        entries = [f'{user_config.id:<19} | {user_config.blacklisted_reason}' for user_config in blacklisted]
        header = 'User id             | Reason\n'
        await ctx.paginate(entries=entries, per_page=15, header=header, codeblock=True)

    @dev_blacklist_users.command(name='add', hidden=True)
    async def dev_blacklist_users_add(self, ctx: context.Context, user: converters.UserConverter, *, reason: str = 'No reason') -> None:
        """
        Blacklist a user.

        `user`: The user to add to the blacklist.
        `reason`: Reason why the user is being blacklisted.
        """

        if reason == 'No reason':
            reason = f'{user.name} - No reason'

        user_config = self.bot.user_manager.get_config(user.id)
        if user_config.blacklisted is True:
            raise exceptions.ArgumentError('That user is already blacklisted.')

        await self.bot.user_manager.set_blacklisted(user.id, reason=reason)
        await ctx.send(f'Blacklisted user `{user.id}` with reason:\n\n`{reason}`')

    @dev_blacklist_users.command(name='remove', hidden=True)
    async def dev_blacklist_users_remove(self, ctx: context.Context, user: converters.UserConverter) -> None:
        """
        Unblacklist a user.

        `user`: The user to remove from the blacklist.
        """

        user_config = self.bot.user_manager.get_config(user.id)
        if user_config.blacklisted is False:
            raise exceptions.ArgumentError('That user is not blacklisted.')

        await self.bot.user_manager.set_blacklisted(user.id, blacklisted=False)
        await ctx.send(f'Unblacklisted user `{user.id}`.')


def setup(bot: SemiBotomatic) -> None:
    bot.add_cog(Dev(bot=bot))
