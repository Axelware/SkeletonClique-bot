from abc import ABC

import discord
from discord.ext import commands

import config
from utilities import context, exceptions


class ChannelEmojiConverter(commands.Converter, ABC):

    async def convert(self, ctx: context.Context, channel: discord.abc.GuildChannel) -> str:

        if isinstance(channel, discord.VoiceChannel):
            emoji = 'voice'
            if channel.overwrites_for(channel.guild.default_role).connect is False:
                emoji = 'voice_locked'

        else:
            if channel.is_news():
                emoji = 'news'
                if channel.overwrites_for(channel.guild.default_role).read_messages is False:
                    emoji = 'news_locked'
            else:
                emoji = 'text'
                if channel.is_nsfw():
                    emoji = 'text_nsfw'
                elif channel.overwrites_for(channel.guild.default_role).read_messages is False:
                    emoji = 'text_locked'

        return config.CHANNEL_EMOJIS[emoji]


class UserConverter(commands.UserConverter):

    async def convert(self, ctx: context.Context, argument: str) -> discord.User:

        user = None
        try:
            user = await super().convert(ctx, argument)
        except commands.BadArgument:
            pass

        if not user:
            try:
                user = await ctx.bot.fetch_user(argument)
            except (discord.NotFound, discord.HTTPException):
                raise commands.UserNotFound(argument=argument)

        return user


class TagNameConverter(commands.clean_content, ABC):

    async def convert(self, ctx: context.Context, argument: str) -> str:

        argument = discord.utils.escape_markdown(await super().convert(ctx, argument)).strip()

        if not argument:
            raise commands.BadArgument

        if argument.split(' ')[0] in ctx.bot.get_command('tag').all_commands:
            raise exceptions.ArgumentError('Your tag name can not start with a tag subcommand.')
        if '`' in argument:
            raise exceptions.ArgumentError('Your tag name can not contain backtick characters.')
        if len(argument) < 3 or len(argument) > 50:
            raise exceptions.ArgumentError('Your tag name must be between 3 and 50 characters long.')

        return argument


class TagContentConverter(commands.clean_content, ABC):

    async def convert(self, ctx: context.Context, argument: str) -> str:

        argument = (await super().convert(ctx, argument)).strip()

        if not argument:
            raise commands.BadArgument

        if len(argument) > 1024:
            raise exceptions.ArgumentError('Your tag content can not be more than 1024 characters long.')

        return argument
