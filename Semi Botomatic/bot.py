import collections
import logging
import time
from typing import Optional, Union

import aiohttp
import asyncpg
import discord
import mystbin
import psutil
from discord.ext import commands

import config
from cogs.web import main
from managers import guild_manager, reminder_manager, tag_manager, todo_manager, user_manager
from utilities import context, help, spotify

__log__ = logging.getLogger(__name__)


class SemiBotomatic(commands.AutoShardedBot):

    def __init__(self) -> None:
        super().__init__(
                command_prefix=commands.when_mentioned_or(config.PREFIX), help_command=help.HelpCommand(), owner_ids=config.OWNER_IDS, intents=discord.Intents.all(),
                activity=discord.Activity(type=discord.ActivityType.watching, name='all of you'), max_messages=10000,
                allowed_mentions=discord.AllowedMentions(everyone=False, users=True, roles=True, replied_user=True)
        )

        self.text_permissions = discord.Permissions(read_messages=True, send_messages=True, embed_links=True, attach_files=True, read_message_history=True, add_reactions=True,
                                                    external_emojis=True)
        self.voice_permissions = discord.Permissions(read_messages=True, send_messages=True, embed_links=True, attach_files=True, read_message_history=True, add_reactions=True,
                                                     external_emojis=True, connect=True, speak=True, use_voice_activation=True)

        self.session = aiohttp.ClientSession()
        self.start_time = time.time()
        self.process = psutil.Process()
        self.socket_stats = collections.Counter()

        self.ERROR_LOG = discord.Webhook.from_url(adapter=discord.AsyncWebhookAdapter(self.session), url=config.ERROR_WEBHOOK_URL)
        self.DMS_LOG = discord.Webhook.from_url(adapter=discord.AsyncWebhookAdapter(self.session), url=config.DM_WEBHOOK_URL)
        self.COMMON_LOG = discord.Webhook.from_url(adapter=discord.AsyncWebhookAdapter(self.session), url=config.COMMON_LOG_WEBHOOK_URL)
        self.IMPORTANT_LOG = discord.Webhook.from_url(adapter=discord.AsyncWebhookAdapter(self.session), url=config.IMPORTANT_LOG_WEBHOOK_URL)

        self.first_ready: bool = True

        self.db: Optional[asyncpg.Pool] = None
        self.mystbin: mystbin.Client = mystbin.Client()
        self.spotify: Optional[spotify.client.Client] = None
        self.semi_botomatic_web: Optional[main.SemiBotomaticWeb] = None

        self.user_manager: user_manager.UserManager = user_manager.UserManager(bot=self)
        self.guild_manager: guild_manager.GuildManager = guild_manager.GuildManager(bot=self)
        self.tag_manager: tag_manager.TagManager = tag_manager.TagManager(bot=self)
        self.reminder_manager: reminder_manager.ReminderManager = reminder_manager.ReminderManager(bot=self)
        self.todo_manager: todo_manager.TodoManager = todo_manager.TodoManager(bot=self)


    async def get_context(self, message: discord.Message, *, cls=context.Context) -> context.Context:
        return await super().get_context(message, cls=cls)

    async def is_owner(self, person: Union[discord.User, discord.Member]) -> bool:
        return person.id in config.OWNER_IDS

    async def start(self, *args, **kwargs) -> None:

        try:
            __log__.debug('[POSTGRESQL] Attempting connection.')
            db = await asyncpg.create_pool(**config.POSTGRESQL, max_inactive_connection_lifetime=0)
        except Exception as e:
            __log__.critical(f'[POSTGRESQL] Error while connecting.\n{e}\n')
            print(f'\n[POSTGRESQL] Error while connecting: {e}')
            raise ConnectionError
        else:
            __log__.info('[POSTGRESQL] Successful connection.')
            print(f'\n[POSTGRESQL] Successful connection.\n')
            self.db = db

        for extension in config.EXTENSIONS:
            try:
                self.load_extension(extension)
                __log__.info(f'[EXTENSIONS] Loaded - {extension}')
                print(f'[EXTENSIONS] Loaded - {extension}')
            except commands.ExtensionNotFound:
                __log__.warning(f'[EXTENSIONS] Extension not found - {extension}')
                print(f'[EXTENSIONS] Extension not found - {extension}')
            except commands.NoEntryPointError:
                __log__.warning(f'[EXTENSIONS] No entry point - {extension}')
                print(f'[EXTENSIONS] No entry point - {extension}')
            except commands.ExtensionFailed as error:
                __log__.warning(f'[EXTENSIONS] Failed - {extension} - Reason: {error}')
                print(f'[EXTENSIONS] Failed - {extension} - Reason: {error}')

        await super().start(*args, **kwargs)

    async def close(self) -> None:

        __log__.info('[BOT] Closing bot down.')
        print('\n[BOT] Closing bot down.')

        __log__.info('[BOT] Closing database connection.')
        print('[DB] Closing database connection.')
        await self.db.close()

        __log__.info('[BOT] Closing aiohttp client session.')
        print('[CS] Closing aiohttp client session.')
        await self.session.close()

        __log__.info('[BOT] Bot has shutdown.')
        print('Bye bye!')
        await super().close()

    #

    async def on_ready(self) -> None:

        if self.first_ready is False:
            return
        self.first_ready = False

        self.add_check(self.command_check)

        self.semi_botomatic_web = await main.load(bot=self)
        await self.user_manager.load()
        await self.guild_manager.load()
        await self.tag_manager.load()

        for cog in self.cogs.values():
            if hasattr(cog, 'load'):
                await cog.load()

    async def command_check(self, ctx: context.Context) -> bool:

        if ctx.user_config.blacklisted is True and ctx.command.qualified_name not in {'help', 'support'}:
            raise commands.CheckFailure(f'You are blacklisted from using this bot with the reason:\n\n`{ctx.user_config.blacklisted_reason}`')

        current_permissions = dict(ctx.me.permissions_in(ctx.channel))
        needed_permissions = {permission: value for permission, value in self.text_permissions if value is True}

        if ctx.command.cog and ctx.command.cog in {self.get_cog('Music')}:
            if (channel := getattr(ctx.author.voice, 'channel', None)) is not None:
                needed_permissions.update({permission: value for permission, value in self.voice_permissions if value is True})
                current_permissions.update({permission: value for permission, value in ctx.me.permissions_in(channel) if value is True})

        missing = [permissions for permissions, value in needed_permissions.items() if current_permissions[permissions] != value]

        if missing:
            raise commands.BotMissingPermissions(missing)

        return True
