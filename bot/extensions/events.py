# Future
from __future__ import annotations

# Standard Library
import collections
import contextlib
import logging
import random
import traceback
from typing import Any, Optional, Union

# Packages
import discord
import pendulum
import slate
from discord.ext import commands

# My stuff
from core import colours, config, emojis, values
from core.bot import SkeletonClique
from utilities import context, enums, exceptions, utils


__log__: logging.Logger = logging.getLogger("extensions.events")

BAD_ARGUMENT_ERRORS = {
    commands.BadArgument:                   "I couldn't convert one of the arguments you passed. Use **{help}** for help.",
    commands.MessageNotFound:               "I couldn't find a message that matches **{argument}**.",
    commands.MemberNotFound:                "I couldn't find a member that matches **{argument}**.",
    commands.GuildNotFound:                 "I couldn't find a server that matches **{argument}**.",
    commands.UserNotFound:                  "I couldn't find a user that matches **{argument}**.",
    commands.ChannelNotFound:               "I couldn't find a channel that matches **{argument}**.",
    commands.ChannelNotReadable:            "I don't have permission to read messages in **{argument.mention}**.",
    commands.BadColourArgument:             "I couldn't find a colour that matches **{argument}**.",
    commands.RoleNotFound:                  "I couldn't find a role that matches **{argument}**.",
    commands.BadInviteArgument:             "That is not a valid invite.",
    commands.EmojiNotFound:                 "I couldn't find an emoji that matches **{argument}**.",
    commands.PartialEmojiConversionFailure: "**{argument}** does not match the emoji format.",
    commands.BadBoolArgument:               "**{argument}** is not a valid true or false value.",
    commands.ThreadNotFound:                "I couldn't find a thread that matches **{argument}**.",
    commands.BadFlagArgument:               "I couldn't convert a value for one of the flags you passed.",
    commands.MissingFlagArgument:           "You missed a value for the **{error.flag.name}** flag.",
    commands.TooManyFlags:                  "You passed too many values to the **{error.flag.name}** flag.",
    commands.MissingRequiredFlag:           "You missed the **{error.flag.name}** flag."

}

COOLDOWN_BUCKETS = {
    commands.BucketType.default:  "for the whole bot",
    commands.BucketType.user:     "for you",
    commands.BucketType.member:   "for you",
    commands.BucketType.role:     "for your role",
    commands.BucketType.guild:    "for this server",
    commands.BucketType.channel:  "for this channel",
    commands.BucketType.category: "for this channel category"
}

CONCURRENCY_BUCKETS = {
    commands.BucketType.default:  "for all users",
    commands.BucketType.user:     "per user",
    commands.BucketType.member:   "per member",
    commands.BucketType.role:     "per role",
    commands.BucketType.guild:    "per server",
    commands.BucketType.channel:  "per channel",
    commands.BucketType.category: "per channel category",
}

OTHER_ERRORS = {
    commands.TooManyArguments:              "You used too many arguments. Use **{prefix}help {command.qualified_name}** for help.",

    commands.UnexpectedQuoteError:          "There was an unexpected quote character in the arguments you passed.",
    commands.InvalidEndOfQuotedStringError: "There was an unexpected space after a quote character in the arguments you passed.",
    commands.ExpectedClosingQuoteError:     "There is a missing quote character in the arguments you passed.",

    commands.CheckFailure:                  "{error}",
    commands.CheckAnyFailure:               "PUT SOMETHING HERE",
    commands.PrivateMessageOnly:            "This command can only be used in private messages.",
    commands.NoPrivateMessage:              "This command can not be used in private messages.",
    commands.NotOwner:                      "You don't have permission to use this command.",
    commands.MissingRole:                   "You don't have the {error.missing_role.mention} role which is required to run this command.",
    commands.BotMissingRole:                "I don't have the {error.missing_role.mention} role which I require to run this command.",
    commands.NSFWChannelRequired:           "This command can only be run in NSFW channels.",

    commands.DisabledCommand:               "This command is currently disabled.",

    commands.MissingAnyRole:                "You are missing roles required to run this command.",
    commands.BotMissingAnyRole:             "I am missing roles required to run this command.",

}

PartialMessage = collections.namedtuple('PartialMessage', 'id created_at guild author channel content jump_url pinned attachments embeds')

WELCOME_MESSAGES = [
    'Welcome to trench {user}! Enjoy your stay.',
    'Dema don\'t control {user}. Welcome to the server!',
    'it looks like {user} might be one of us, welcome to **The Skeleton Clique!**',
    '{user} just wants to say hello. Welcome to **The Skeleton Clique!**',
    '{user} is waking up in Slowtown. Welcome to the server!',
    'Please welcome {user} to **The Skeleton Clique!**',
    'Don\'t shy away! {user}, welcome to **The Skeleton Clique!**'
]

RED = discord.Colour(0xFF0000)
ORANGE = discord.Colour(0xFAA61A)
GREEN = discord.Colour(0x00FF00)


def setup(bot: SkeletonClique) -> None:
    bot.add_cog(Events(bot=bot))


class Events(commands.Cog):

    def __init__(self, bot: SkeletonClique) -> None:
        self.bot = bot

    # Logging methods

    @staticmethod
    async def _log_attachments(webhook: discord.Webhook, message: discord.Message) -> None:

        with contextlib.suppress(discord.HTTPException, discord.NotFound, discord.Forbidden):
            for attachment in message.attachments:
                await webhook.send(
                        content=f'Attachment from message with id `{message.id}`:', file=await attachment.to_file(use_cached=True), username=f'{message.author}',
                        avatar_url=utils.avatar(person=message.author)
                )

    @staticmethod
    async def _log_embeds(webhook: discord.Webhook, message: discord.Message) -> None:

        for embed in message.embeds:
            await webhook.send(
                    content=f'Embed from message with id `{message.id}`:', embed=embed, username=f'{message.author}',
                    avatar_url=utils.avatar(person=message.author)
            )

    async def _log_dm(self, message: discord.Message) -> None:

        content = await utils.safe_content(self.bot.mystbin, message.content) if message.content else '*No content*'

        embed = discord.Embed(colour=GREEN, title=f'DM from `{message.author}`:', description=content)
        embed.add_field(
                name='Info:', value=f'`Channel:` {message.channel} `{message.channel.id}`\n'
                                    f'`Author:` {message.author} `{message.author.id}`\n'
                                    f'`Time:` {utils.format_datetime(datetime=pendulum.now(tz="UTC"))}\n'
                                    f'`Jump:` [Click here]({message.jump_url})', inline=False
        )
        embed.set_footer(text=f'ID: {message.id}')
        await self.bot.DMS_LOG.send(embed=embed, username=f'{message.author}', avatar_url=utils.avatar(person=message.author))

        await self._log_attachments(webhook=self.bot.DMS_LOG, message=message)
        await self._log_embeds(webhook=self.bot.DMS_LOG, message=message)

    async def _log_delete(self, message: discord.Message) -> None:

        webhook = self.bot.COMMON_LOG if message.guild else self.bot.DMS_LOG
        content = await utils.safe_content(self.bot.mystbin, message.content) if message.content else '*No content*'

        embed = discord.Embed(colour=RED, title=f'Message deleted in `{message.channel}`:', description=content)
        embed.add_field(
                name='Info:', value=f'{f"`Guild:` {message.guild} `{message.guild.id}`{values.NL}" if message.guild else ""}'
                                    f'`Channel:` {message.channel} `{message.channel.id}`\n'
                                    f'`Author:` {message.author} `{message.author.id}`\n'
                                    f'`Time:` {utils.format_datetime(datetime=pendulum.now(tz="UTC"))}\n'
                                    f'`Jump:` [Click here]({message.jump_url})', inline=False
        )
        embed.set_footer(text=f'ID: {message.id}')
        await webhook.send(embed=embed, username=f'{message.author}', avatar_url=utils.avatar(person=message.author))

        await self._log_attachments(webhook=webhook, message=message)
        await self._log_embeds(webhook=webhook, message=message)

    async def _log_update(self, before: Union[PartialMessage, discord.Message], after: Union[PartialMessage, discord.Message]) -> None:

        webhook = self.bot.COMMON_LOG if after.guild else self.bot.DMS_LOG
        before_content = await utils.safe_content(self.bot.mystbin, before.content) if before.content else '*No content*'
        after_content = await utils.safe_content(self.bot.mystbin, after.content) if after.content else '*No content*'

        embed = discord.Embed(colour=ORANGE, title=f'Message edited in `{after.channel}`:')
        embed.add_field(name='Before:', value=before_content, inline=False)
        embed.add_field(name='After:', value=after_content, inline=False)
        embed.add_field(
                name='Info:', value=f'{f"`Guild:` {after.guild} `{after.guild.id}`{values.NL}" if after.guild else ""}'
                                    f'`Channel:` {after.channel} `{after.channel.id}`\n'
                                    f'`Author:` {after.author} `{after.author.id}`\n'
                                    f'`Time:` {utils.format_datetime(datetime=pendulum.now(tz="UTC"))}\n'
                                    f'`Jump:` [Click here]({after.jump_url})', inline=False
        )
        embed.set_footer(text=f'ID: {after.id}')
        await webhook.send(embed=embed, username=f'{after.author}', avatar_url=utils.avatar(person=after.author))

        await self._log_attachments(webhook=webhook, message=after)
        await self._log_embeds(webhook=webhook, message=after)

    async def _log_pin(self, message: Union[PartialMessage, discord.Message]) -> None:

        webhook = self.bot.COMMON_LOG if message.guild else self.bot.DMS_LOG
        content = await utils.safe_content(self.bot.mystbin, message.content) if message.content else '*No content*'

        if message.pinned:
            embed = discord.Embed(colour=GREEN, title=f'Message pinned in `{message.channel}`:', description=content)
        else:
            embed = discord.Embed(colour=RED, title=f'Message unpinned in `{message.channel}`:', description=content)

        embed.add_field(
                name='Info:', value=f'{f"`Guild:` {message.guild} `{message.guild.id}`{values.NL}" if message.guild else ""}'
                                    f'`Channel:` {message.channel} `{message.channel.id}`\n'
                                    f'`Author:` {message.author} `{message.author.id}`\n'
                                    f'`Time:` {utils.format_datetime(datetime=pendulum.now(tz="UTC"))}\n'
                                    f'`Jump:` [Click here]({message.jump_url})', inline=False
        )
        embed.set_footer(text=f'ID: {message.id}')
        await webhook.send(embed=embed, username=f'{message.author}', avatar_url=utils.avatar(person=message.author))

        await self._log_attachments(webhook=webhook, message=message)
        await self._log_embeds(webhook=webhook, message=message)

    # Error handling

    @commands.Cog.listener()
    async def on_command_error(self, ctx: context.Context, error: Any) -> Optional[discord.Message]:

        error = getattr(error, "original", error)

        __log__.error(
            f"Error in command. Error: {type(error)} | Content: {getattr(ctx.message, 'content', None)} | "
            f"Channel: {ctx.channel} ({getattr(ctx.channel, 'id', None)}) | Author: {ctx.author} ({getattr(ctx.author, 'id', None)}) | "
            f"Guild: {ctx.guild} ({getattr(ctx.guild, 'id', None)})"
        )

        if isinstance(error, exceptions.EmbedError):
            await ctx.reply(embed=error.embed)
            return

        if isinstance(error, commands.CommandNotFound):
            await ctx.message.add_reaction(emojis.CROSS)
            return

        if isinstance(error, commands.MissingPermissions):
            permissions = values.NL.join([f"- {permission}" for permission in error.missing_permissions])
            await ctx.reply(
                f"You are missing permissions required to run the command `{ctx.command.qualified_name}` in `{ctx.guild}`.\n```diff\n{permissions}\n```"
            )
            return

        if isinstance(error, commands.BotMissingPermissions):
            permissions = values.NL.join([f"- {permission}" for permission in error.missing_permissions])
            await ctx.try_dm(
                f"I am missing permissions required to run the command `{ctx.command.qualified_name}` in `{ctx.guild}`.\n```diff\n{permissions}\n```"
            )
            return

        #

        message = None

        if isinstance(error, slate.NodesNotFound):
            message = "There are no players available right now."

        elif isinstance(error, commands.MissingRequiredArgument):
            message = f"You missed the **{error.param.name}** argument. Use **{config.PREFIX}help {ctx.command.qualified_name}** for help."

        elif isinstance(error, commands.BadArgument):
            argument = getattr(error, "argument", None)
            message = BAD_ARGUMENT_ERRORS.get(type(error), "None").format(
                argument=argument,
                help=f"{config.PREFIX}help {ctx.command.qualified_name}",
                error=error
            )

        elif isinstance(error, commands.BadUnionArgument):
            message = f"I couldn't understand the **{error.param.name}** argument. Use **{config.PREFIX}help {ctx.command.qualified_name}** for help."

        elif isinstance(error, commands.BadLiteralArgument):
            message = f"The argument **{error.param.name}** must be one of {', '.join([f'**{arg}**' for arg in error.literals])}."

        elif isinstance(error, commands.CommandOnCooldown):
            message = f"This command is on cooldown **{COOLDOWN_BUCKETS.get(error.type)}**. " \
                      f"You can retry in `{utils.format_seconds(error.retry_after, friendly=True)}`"

        elif isinstance(error, commands.MaxConcurrencyReached):
            message = f"This command is being ran at its maximum of **{error.number} time{'s' if error.number > 1 else ''}** " \
                      f"{CONCURRENCY_BUCKETS.get(error.per)}."

        embed = discord.Embed(colour=colours.RED)

        if message:
            embed.description = f"{emojis.CROSS}  {message}"
            await ctx.reply(embed=embed)

        elif (message := OTHER_ERRORS.get(type(error))) is not None:
            embed.description = f"{emojis.CROSS}  {message.format(command=ctx.command, error=error, prefix=config.PREFIX)}"
            await ctx.reply(embed=embed)

        else:
            await self.handle_traceback(ctx, error)

    async def handle_traceback(self, ctx: context.Context, exception: Exception) -> None:

        embed = utils.embed(
            colour=colours.RED,
            emoji=emojis.CROSS,
            description=f"Something went wrong! Join my [support server]({values.SUPPORT_LINK}) for help."
        )
        await ctx.reply(embed=embed)

        message = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        __log__.error(f"Traceback:", exc_info=exception)

        embed = discord.Embed(
            colour=colours.RED,
            description=await utils.safe_content(self.bot.mystbin, ctx.message.content, syntax="python", max_characters=2000)
        ).add_field(
            name="Info:",
            value=f"{f'`Guild:` {ctx.guild} `{ctx.guild.id}`{values.NL}' if ctx.guild else ''}"
                  f"`Channel:` {ctx.channel} `{ctx.channel.id}`\n"
                  f"`Author:` {ctx.author} `{ctx.author.id}`\n"
                  f"`Time:` {utils.format_datetime(pendulum.now(tz='UTC'))}"
        )

        message = await utils.safe_content(self.bot.mystbin, f"```py\n{message}```", syntax="python", max_characters=2000)

        await self.bot.ERROR_LOG.send(embed=embed, username=f"{ctx.author}", avatar_url=utils.avatar(person=ctx.author))
        await self.bot.ERROR_LOG.send(content=message, username=f"{ctx.author}", avatar_url=utils.avatar(person=ctx.author))

    # Bot events

    @commands.Cog.listener()
    async def on_socket_event_type(self, event_type: str) -> None:
        self.bot.socket_stats[event_type] += 1

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:

        if before.content == after.content:
            return

        await self.bot.process_commands(after)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        __log__.info(f"Bot is now ready. Name: {self.bot.user} | ID: {self.bot.user.id}")

    # Message logging

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:

        if config.ENV == enums.Environment.DEVELOPMENT:
            return

        if message.guild or message.is_system():
            return

        await self._log_dm(message=message)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:

        if config.ENV == enums.Environment.DEVELOPMENT:
            return

        if message.author.bot or (getattr(message.guild, 'id', None) not in {config.SKELETON_CLIQUE_GUILD_ID, config.ALESS_LAND_GUILD_ID} if message.guild else False):
            return

        await self._log_delete(message=message)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent) -> None:

        if config.ENV == enums.Environment.DEVELOPMENT:
            return

        guild = self.bot.get_guild(payload.guild_id)
        with contextlib.suppress(discord.HTTPException, discord.NotFound, discord.Forbidden):
            if not (channel := guild.get_channel(int(payload.data['channel_id'])) if guild else await self.bot.fetch_channel(int(payload.data['channel_id']))):
                return

        after = PartialMessage(
                id=payload.data['id'], created_at=discord.utils.snowflake_time(int(payload.data['id'])), guild=getattr(channel, 'guild', None),
                author=self.bot.get_user(int(payload.data.get("author", {}).get('id', 0))), channel=channel, content=payload.data.get('content'),
                jump_url=f'https://discord.com/channels/{getattr(guild, "id", "@me")}/{channel.id}/{payload.data["id"]}', pinned=payload.data.get('pinned'),
                attachments=[discord.Attachment(data=a, state=self.bot._connection) for a in payload.data.get('attachments', [])],
                embeds=[discord.Embed.from_dict(e) for e in payload.data['embeds']]
        )

        if not (before := payload.cached_message):
            before = PartialMessage(
                    id=after.id, created_at=after.created_at, guild=after.guild, author=after.author, channel=after.channel, content='*No content*',
                    jump_url=after.jump_url, pinned=False, attachments=after.attachments, embeds=after.embeds
            )

        if before.author.bot or (getattr(before.guild, 'id', None) not in {config.SKELETON_CLIQUE_GUILD_ID, config.ALESS_LAND_GUILD_ID} if before.guild else False):
            return

        if before.pinned != after.pinned:
            await self._log_pin(message=after)
            return

        await self._log_update(before=before, after=after)

    # Channel logging

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: Union[discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel, discord.StageChannel]) -> None:

        if config.ENV == enums.Environment.DEVELOPMENT:
            return

        if channel.guild.id not in {config.SKELETON_CLIQUE_GUILD_ID, config.ALESS_LAND_GUILD_ID}:
            return

        embed = discord.Embed(
                colour=GREEN, title='Channel created:',
                description=f'{channel.mention}\n\n'
                            f'`Guild:` {channel.guild} `{channel.guild.id}`\n'
                            f'{f"`Category:` {channel.category} `{channel.category_id}`{values.NL}" if channel.category else ""}'
                            f'`Name:` {channel.name} `{channel.id}`\n'
                            f'`Type:` {str(channel.type).title().replace("_", " ")}\n'
                            f'`Position:` {channel.position}\n'
                            f'`Created at:` {utils.format_datetime(channel.created_at, seconds=True)}'
        )
        embed.set_footer(text=f'ID: {channel.id}')
        await self.bot.COMMON_LOG.send(embed=embed, username='Logs: Channels', avatar_url=utils.icon(guild=channel.guild))

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: Union[discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel, discord.StageChannel]) -> None:

        if config.ENV == enums.Environment.DEVELOPMENT:
            return

        if channel.guild.id not in {config.SKELETON_CLIQUE_GUILD_ID, config.ALESS_LAND_GUILD_ID}:
            return

        embed = discord.Embed(
                colour=RED, title='Channel deleted:',
                description=f'`Guild:` {channel.guild} `{channel.guild.id}`\n'
                            f'{f"`Category:` {channel.category} `{channel.category_id}`{values.NL}" if channel.category else ""}'
                            f'`Name:` {channel.name} `{channel.id}`\n'
                            f'`Type:` {str(channel.type).title().replace("_", " ")}\n'
                            f'`Position:` {channel.position}\n'
                            f'`Deleted at:` {utils.format_datetime(channel.created_at, seconds=True)}'
        )
        embed.set_footer(text=f'ID: {channel.id}')
        await self.bot.COMMON_LOG.send(embed=embed, username='Logs: Channels', avatar_url=utils.icon(guild=channel.guild))

    @commands.Cog.listener()
    async def on_guild_channel_update(
            self, before: Union[discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel, discord.StageChannel],
            after: Union[discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel, discord.StageChannel]
    ) -> None:

        if config.ENV == enums.Environment.DEVELOPMENT:
            return

        if before.guild.id not in {config.SKELETON_CLIQUE_GUILD_ID, config.ALESS_LAND_GUILD_ID}:
            return

        embed = discord.Embed(
                colour=ORANGE, title='Channel updated:',
                description=f'`Name:` {before.name} `{before.id}`\n'
                            f'`Type:` {str(before.type).title().replace("_", " ")}\n'
                            f'`Time:` {utils.format_datetime(pendulum.now(tz="UTC"), seconds=True)}'
        )
        embed.set_footer(text=f'ID: {before.id}')

        # Common attributes
        if before.category != after.category:
            embed.add_field(name='Category:', value=f'`Before:` {before.category}\n`After:` {after.category}', inline=False)
        if before.name != after.name:
            embed.add_field(name='Name:', value=f'`Before:` {before.name}\n`After:` {after.name}', inline=False)
        if before.permissions_synced != after.permissions_synced:
            embed.add_field(name='Permissions synced:', value=f'`Before:` {before.permissions_synced}\n`After:` {after.permissions_synced}', inline=False)
        if before.position != after.position:
            embed.add_field(name='Position:', value=f'`Before:` {before.position}\n`After:` {after.position}')

        if before.changed_roles != after.changed_roles:
            embed.add_field(
                    name='Changed roles:',
                    value=f'`Before:` {" ".join(role.mention for role in before.changed_roles)}\n`After:` {" ".join(role.mention for role in after.changed_roles)}', inline=False
            )

        if before.overwrites != after.overwrites:  # I hate this so much...

            changes = []
            if added := {k: v for k, v in after.overwrites.items() if k not in before.overwrites}:
                changes.append(f'`Added:` {" ".join(getattr(before.guild.get_member(ow.id) or before.guild.get_role(ow.id), "mention", None) for ow in added)}')
            if removed := {k: v for k, v in before.overwrites.items() if k not in after.overwrites}:
                changes.append(f'`Removed:` {" ".join(getattr(before.guild.get_member(ow.id) or before.guild.get_role(ow.id), "mention", None) for ow in removed)}')
            if changed := {k: v for k, v in after.overwrites.items() if v != before.overwrites.get(k, v)}:
                changes.append(f'`Changed:` {" ".join(getattr(before.guild.get_member(ow.id) or before.guild.get_role(ow.id), "mention", None) for ow in changed)}')

            embed.add_field(name='Overwrites:', value='\n'.join(changes), inline=False)

        # Text
        if isinstance(before, discord.TextChannel) and before.slowmode_delay != after.slowmode_delay:
            embed.add_field(
                    name='Slowmode:',
                    value=f'`Before:` {utils.format_seconds(before.slowmode_delay, friendly=True)}\n'
                          f'`After:` {utils.format_seconds(after.slowmode_delay, friendly=True)}', inline=False
            )

        # Text and stage
        if isinstance(before, (discord.TextChannel, discord.StageChannel)) and before.topic != after.topic:
            embed.add_field(name='Topic:', value=f'`Before:` {before.topic}\n`After:` {after.topic}', inline=False)

        # Voice and stage
        if isinstance(before, (discord.VoiceChannel, discord.StageChannel)):
            if before.bitrate != after.bitrate:
                embed.add_field(name='Bitrate:', value=f'`Before:` {round(before.bitrate / 1000)} kbps\n`After:` {round(after.bitrate / 1000)} kbps', inline=False)
            if before.rtc_region != after.rtc_region:
                embed.add_field(name='Region:', value=f'`Before:` {utils.voice_region(before)}\n`After:` {utils.voice_region(after)}', inline=False)
            if before.user_limit != after.user_limit:
                embed.add_field(name='User limit:', value=f'`Before:` {before.user_limit}\n`After:` {after.user_limit}', inline=False)

        await self.bot.COMMON_LOG.send(embed=embed, username='Logs: Channels', avatar_url=utils.icon(guild=before.guild))

    # Member logging

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:

        if config.ENV == enums.Environment.DEVELOPMENT:
            return

        if member.guild.id != config.SKELETON_CLIQUE_GUILD_ID:
            return

        embed = discord.Embed(colour=GREEN, title=f'`{member}` just joined:', description=member.mention)
        embed.add_field(
                name='Info:',
                value=f'`Time joined:` {utils.format_datetime(datetime=pendulum.now(tz="UTC"), seconds=True)}\n'
                      f'`Created on:` {utils.format_datetime(datetime=member.created_at)}\n'
                      f'`Created:` {utils.format_difference(datetime=member.created_at)} ago\n'
                      f'`Member count:` {len(member.guild.members)}\n'
                      f'`Is bot:` {member.bot}', inline=False
        )
        embed.set_footer(text=f'ID: {member.id}')
        await self.bot.IMPORTANT_LOG.send(embed=embed, username='Logs: Members', avatar_url=utils.avatar(person=member))

        await member.guild.get_channel(config.GENERAL_CHAT_ID).send(random.choice(WELCOME_MESSAGES).format(user=member.mention))
        await member.add_roles(member.guild.get_role(config.CLIQUE_ROLE_ID))

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:

        if config.ENV == enums.Environment.DEVELOPMENT:
            return

        if member.guild.id != config.SKELETON_CLIQUE_GUILD_ID:
            return

        members = member.guild.members.copy()
        members.append(member)

        embed = discord.Embed(colour=RED, title=f'`{member}` just left:', description=member.mention)
        embed.add_field(
                name='Info:',
                value=f'`Time left:` {utils.format_datetime(datetime=pendulum.now(tz="UTC"), seconds=True)}\n' \
                      f'`Created on:` {utils.format_datetime(datetime=member.created_at)}\n' \
                      f'`Created:` {utils.format_difference(datetime=member.created_at)} ago\n' \
                      f'`Join position:` {sorted(members, key=lambda m: m.joined_at).index(member) + 1}\n' \
                      f'`Member count:` {len(members) - 1}\n' \
                      f'`Roles:` {" ".join([role.mention for role in member.roles][1:] if member.roles else ["None"])}', inline=False
        )
        embed.set_footer(text=f'ID: {member.id}')
        await self.bot.IMPORTANT_LOG.send(embed=embed, username='Logs: Members', avatar_url=utils.avatar(person=member))

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:

        if config.ENV == enums.Environment.DEVELOPMENT:
            return

        if before.guild.id != config.SKELETON_CLIQUE_GUILD_ID:
            return

        embed = discord.Embed(colour=ORANGE, title=f'`{after}` was updated', description=after.mention)

        embed.set_footer(text=f'ID: {after.id}')
        # await self.bot.IMPORTANT_LOG.send(embed=embed, username='Logs: Members', avatar_url=utils.avatar(person=after))

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User) -> None:

        if config.ENV == enums.Environment.DEVELOPMENT:
            return

        embed = discord.Embed(colour=ORANGE, title=f'`{after}` was updated', description=after.mention)

        if before.name != after.name:
            embed.add_field(name='Name:', value=f'`Before:` {before.name}\n`After:` {after.name}')

        embed.set_footer(text=f'ID: {after.id}')
        # await self.bot.IMPORTANT_LOG.send(embed=embed, username='Logs: Users', avatar_url=utils.avatar(person=after))
