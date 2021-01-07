import logging
import sys
import traceback
from typing import Any, Optional

import discord
import mystbin
import pendulum
import slate
from discord.ext import commands
from discord.ext.alternatives.literal_converter import BadLiteralArgument

import config
from bot import SemiBotomatic
from utilities import context, exceptions, utils

__log__ = logging.getLogger(__name__)


class Events(commands.Cog):

    def __init__(self, *, bot: SemiBotomatic) -> None:
        self.bot = bot

        self.BAD_ARGUMENT_ERRORS = {
            commands.MessageNotFound:               'A message for the argument `{argument}` was not found.',
            commands.MemberNotFound:                'A member for the argument `{argument}` was not found.',
            commands.UserNotFound:                  'A user for the argument `{argument}` was not found.',
            commands.ChannelNotFound:               'A channel for the argument `{argument}` was not found.',
            commands.RoleNotFound:                  'A role for the argument `{argument}` was not found.',
            commands.EmojiNotFound:                 'An emoji for the argument `{argument}` was not found.',
            commands.ChannelNotReadable:            'I do not have permission to read the channel `{argument}`',
            commands.BadInviteArgument:             'The invite `{argument}` was not valid or is expired.',
            commands.PartialEmojiConversionFailure: 'The argument `{argument}` did not match the partial emoji format.',
            commands.BadBoolArgument:               'The argument `{argument}` was not a valid True or False value.',
            commands.BadColourArgument:             'The argument `{argument}` was not a valid colour type.',
            BadLiteralArgument:                     'The argument `{argument}` must be one of {", ".join([f"`{arg}`" for arg in argument])}.',
            commands.BadArgument:                   'I was unable to convert an argument that you used.',
        }

        self.COOLDOWN_BUCKETS = {
            commands.BucketType.default:  f'for the whole bot',
            commands.BucketType.user:     f'for you',
            commands.BucketType.member:   f'for you',
            commands.BucketType.role:     f'for your role',
            commands.BucketType.guild:    f'for this server',
            commands.BucketType.channel:  f'for this channel',
            commands.BucketType.category: f'for this channel category'
        }

        self.CONCURRENCY_BUCKETS = {
            commands.BucketType.default:  f'for all users',
            commands.BucketType.user:     f'per user',
            commands.BucketType.member:   f'per member',
            commands.BucketType.role:     f'per role',
            commands.BucketType.guild:    f'per server',
            commands.BucketType.channel:  f'per channel',
            commands.BucketType.category: f'per channel category',
        }

        self.OTHER_ERRORS = {
            exceptions.ArgumentError:               '{error}',
            slate.NoNodesAvailable:                 'There are no music nodes available right now.',

            commands.TooManyArguments:              'You used too many arguments. Use `{prefix}help {command}` for more information on what arguments to use.',

            commands.UnexpectedQuoteError:          'There was an unexpected quote character in the arguments you passed.',
            commands.InvalidEndOfQuotedStringError: 'There was an unexpected space after a quote character in the arguments you passed.',
            commands.ExpectedClosingQuoteError:     'There is a missing quote character in the arguments you passed.',

            commands.CheckFailure:                  '{error}',
            commands.PrivateMessageOnly:            'The command `{command}` can only be used in private messages',
            commands.NoPrivateMessage:              'The command `{command}` can not be used in private messages.',
            commands.NotOwner:                      'The command `{command}` is owner only.',
            commands.NSFWChannelRequired:           'The command `{command}` can only be run in a NSFW channel.',

            commands.DisabledCommand:               'The command `{command}` has been disabled.',
        }

    @commands.Cog.listener()
    async def on_command_error(self, ctx: context.Context, error: Any) -> Optional[discord.Message]:

        error = getattr(error, 'original', error)

        __log__.error(f'[COMMANDS] Error while running command. Name: {ctx.command.qualified_name} | Error: {type(error)} | Invoker: {ctx.author} | '
                      f'Channel: {ctx.channel} ({ctx.channel.id})')

        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.BotMissingPermissions):
            permissions = '\n'.join([f'> {permission}' for permission in error.missing_perms])
            message = f'I am missing the following permissions required to run the command `{ctx.command.qualified_name}`.\n{permissions}'
            return await ctx.try_dm(content=message)

        message = None

        if isinstance(error, commands.BadArgument):
            message = self.BAD_ARGUMENT_ERRORS.get(type(error), 'None').format(argument=getattr(error, 'argument', 'None'))

        elif isinstance(error, commands.CommandOnCooldown):
            message = f'The command `{ctx.command.qualified_name}` is on cooldown {self.COOLDOWN_BUCKETS.get(error.cooldown.type)}. You can retry in ' \
                      f'`{utils.format_seconds(seconds=error.retry_after, friendly=True)}`'

        elif isinstance(error, commands.MaxConcurrencyReached):
            message = f'The command `{ctx.command.qualified_name}` is being ran at its maximum of {error.number} time{"s" if error.number > 1 else ""} ' \
                      f'{self.CONCURRENCY_BUCKETS.get(error.per)}. Retry a bit later.'

        elif isinstance(error, commands.MissingPermissions):
            permissions = '\n'.join([f'> {permission}' for permission in error.missing_perms])
            message = f'You are missing the following permissions required to run the command `{ctx.command.qualified_name}`.\n{permissions}'

        elif isinstance(error, commands.MissingRequiredArgument):
            message = f'You missed the `{error.param.name}` argument. Use `{config.PREFIX}help {ctx.command.qualified_name}` for more information on what arguments to use.'

        elif isinstance(error, commands.BadUnionArgument):
            message = f'I was unable to convert the `{error.param.name}` argument. Use `{config.PREFIX}help {ctx.command.qualified_name}` for more help on what arguments to use.'

        elif isinstance(error, commands.MissingRole):
            message = f'The role `{error.missing_role}` is required to run this command.'

        elif isinstance(error, commands.BotMissingRole):
            message = f'The bot requires the role `{error.missing_role}` to run this command.'

        elif isinstance(error, commands.MissingAnyRole):
            message = f'The roles {", ".join([f"`{role}`" for role in error.missing_roles])} are required to run this command.'

        elif isinstance(error, commands.BotMissingAnyRole):
            message = f'The bot requires the roles {", ".join([f"`{role}`" for role in error.missing_roles])} to run this command.'

        if message:
            return await ctx.send(message)

        message = self.OTHER_ERRORS.get(type(error), None)
        if message:
            message = message.format(command=ctx.command.qualified_name, error=error, prefix=config.PREFIX)
            return await ctx.send(message)

        await self.handle_traceback(ctx=ctx, error=error)

    async def handle_traceback(self, *, ctx: context.Context, error: Any) -> None:

        await ctx.send(f'Something went wrong while executing that command.')

        error_traceback = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        print(f'\n{error_traceback}\n', file=sys.stderr)
        __log__.error(f'[COMMANDS]\n\n{traceback}\n\n')

        info = f'{f"`Guild:` {ctx.guild} `{ctx.guild.id}`" if ctx.guild else ""}\n' \
               f'`Channel:` {ctx.channel} `{ctx.channel.id}`\n' \
               f'`Author:` {ctx.author} `{ctx.author.id}`\n' \
               f'`Time:` {utils.format_datetime(datetime=pendulum.now(tz="UTC"))}'

        embed = discord.Embed(colour=ctx.colour, description=f'{ctx.message.content}')
        embed.add_field(name='Info:', value=info)
        await self.bot.ERROR_LOG.send(embed=embed, username=f'{ctx.author}', avatar_url=utils.person_avatar(person=ctx.author))

        if len(error_traceback) < 2000:
            error_traceback = f'```py\n{error_traceback}\n```'
        else:
            error_traceback = utils.safe_text(mystbin_client=self.bot.mystbin, text=error_traceback)

        await self.bot.ERROR_LOG.send(content=f'{error_traceback}', username=f'{ctx.author}', avatar_url=utils.person_avatar(person=ctx.author))

    #

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:

        if message.author.id == self.bot.user.id:
            return

        ctx = await self.bot.get_context(message)

        if message.guild:
            return

        embed = discord.Embed(colour=ctx.colour, description=f'{message.content}')

        info = f'`Channel:` {ctx.channel} `{ctx.channel.id}`\n`Author:` {ctx.author} `{ctx.author.id}`\n`Time:` {utils.format_datetime(datetime=pendulum.now(tz="UTC"))}'
        embed.add_field(name='Info:', value=info)

        await self.bot.DMS_LOG.send(embed=embed, username=f'{ctx.author}', avatar_url=utils.person_avatar(person=ctx.author))

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:

        if before.author.bot:
            return

        if before.content == after.content:
            return

        await self.bot.process_commands(after)

        ctx = await self.bot.get_context(message=before)
        before_content = await utils.safe_text(mystbin_client=self.bot.mystbin, text=before.content)
        after_content = await utils.safe_text(mystbin_client=self.bot.mystbin, text=after.content)

        embed = discord.Embed(colour=ctx.colour, title='Message content changed:')
        embed.set_footer(text=f'ID: {before.id}')
        embed.add_field(name='Before:', value=before_content, inline=False)
        embed.add_field(name='After:', value=after_content, inline=False)

        info = f'`Channel:` {ctx.channel} `{ctx.channel.id}`\n`Author:` {ctx.author} `{ctx.author.id}`\n`Time:` {utils.format_datetime(datetime=pendulum.now(tz="UTC"))}'
        embed.add_field(name='Info:', value=info, inline=False)

        await self.bot.COMMON_LOG.send(embed=embed, username=f'{ctx.author}', avatar_url=utils.person_avatar(person=ctx.author))

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:

        ctx = await self.bot.get_context(message=message)
        content = await utils.safe_text(mystbin_client=self.bot.mystbin, text=message.content) if message.content else "*No content*"

        embed = discord.Embed(colour=ctx.colour, title='Message deleted:', description=f'{content}')
        embed.set_footer(text=f'ID: {message.id}')

        info = f'`Channel:` {ctx.channel} `{ctx.channel.id}`\n`Author:` {ctx.author} `{ctx.author.id}`\n`Time:` {utils.format_datetime(datetime=pendulum.now(tz="UTC"))}'
        embed.add_field(name='Info:', value=info, inline=False)

        avatar = utils.person_avatar(person=ctx.author)

        await self.bot.COMMON_LOG.send(embed=embed, username=f'{ctx.author}', avatar_url=avatar)

        if message.attachments:

            for attachment in message.attachments:
                try:
                    file = await attachment.to_file(use_cached=True)
                    await self.bot.COMMON_LOG.send(content=f'Deleted attachments in message `{message.id}`: ', file=file, username=f'{ctx.author}', avatar_url=avatar)
                except discord.HTTPException or discord.Forbidden or discord.NotFound:
                    continue


def setup(bot: SemiBotomatic):
    bot.add_cog(Events(bot=bot))
