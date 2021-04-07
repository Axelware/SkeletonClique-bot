from abc import ABC

import dateparser.search
import discord
import pendulum
import rapidfuzz
import yarl
from discord.ext import commands
from pendulum.tz.timezone import Timezone

import config
from utilities import context, exceptions, utils


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


class TimezoneConverter(commands.Converter, ABC):

    async def convert(self, ctx: context.Context, argument: str) -> Timezone:

        if argument not in pendulum.timezones:
            msg = '\n'.join(f'`{index + 1}.` {match[0]}' for index, match in enumerate(
                    rapidfuzz.process.extract(query=argument, choices=pendulum.timezones, processor=lambda s: s)
            ))
            raise exceptions.ArgumentError(f'That was not a recognised timezone. Maybe you meant one of these?\n{msg}')

        return pendulum.timezone(argument)


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


class DatetimeConverter(commands.Converter, ABC):

    async def convert(self, ctx: context.Context, argument: str) -> dict:

        searches = dateparser.search.search_dates(argument, languages=['en'], settings=config.DATEPARSER_SETTINGS)
        if not searches:
            raise exceptions.ArgumentError('I was unable to find a time and/or date within your query, try to be more explicit or put the time/date first.')

        data = {'argument': argument, 'found': {}}

        for datetime_phrase, datetime in searches:
            datetime = pendulum.instance(dt=datetime, tz='UTC')
            data['found'][datetime_phrase] = datetime

        if not data['found']:
            raise exceptions.ArgumentError('I was able to find a time and/or date within your query, however it seems to be in the past.')

        return data


class ImageConverter(commands.Converter, ABC):

    async def convert(self, ctx: context.Context, argument: str) -> str:

        try:
            member = await commands.MemberConverter().convert(ctx=ctx, argument=str(argument))
        except commands.BadArgument:
            pass
        else:
            await ctx.send(f'Editing the avatar of `{member}`. If this is a mistake please specify the user/image you would like to edit before any extra arguments.')
            return utils.avatar(person=member)

        if (check := yarl.URL(argument)) and check.scheme and check.host:
            return argument

        try:
            emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=str(argument))
        except commands.EmojiNotFound:
            pass
        else:
            return str(emoji.url)

        try:
            partial_emoji = await commands.PartialEmojiConverter().convert(ctx=ctx, argument=str(argument))
        except commands.PartialEmojiConversionFailure:
            pass
        else:
            return str(partial_emoji.url)

        url = f'https://twemoji.maxcdn.com/v/latest/72x72/{ord(argument[0]):x}.png'
        async with ctx.bot.session.get(url) as response:
            if response.status == 200:
                return url

        raise commands.ConversionError
