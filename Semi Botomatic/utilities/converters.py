from abc import ABC

import discord
from discord.ext import commands

import config
from utilities import context


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
