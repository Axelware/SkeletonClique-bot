import codecs
import datetime as dt
import logging
import os
import pathlib
from typing import Tuple, Union

import discord
import humanize
import mystbin
import pendulum

import config
from bot import SemiBotomatic

__log__ = logging.getLogger(__name__)


async def safe_text(*, mystbin_client: mystbin.Client, text: str) -> str:

    if len(text) <= 1024:
        return text

    try:
        mystbin_link = await mystbin_client.post(text, syntax='python')
    except mystbin.APIError as error:
        __log__.warning(f'[ERRORS] Error while uploading error traceback to mystbin | Code: {error.status_code} | Message: {error.message}')
        mystbin_link = f'{text[:1024]}'

    return mystbin_link


def convert_datetime(*, datetime: Union[dt.datetime, pendulum.datetime]) -> pendulum.datetime:
    return pendulum.instance(datetime, tz='UTC') if isinstance(datetime, dt.datetime) else datetime


def format_seconds(*, seconds: int, friendly: bool = False) -> str:

    minute, second = divmod(seconds, 60)
    hour, minute = divmod(minute, 60)
    day, hour = divmod(hour, 24)

    days, hours, minutes, seconds = round(day), round(hour), round(minute), round(second)

    if friendly is True:
        return f'{f"{days}d " if not days == 0 else ""}{f"{hours}h " if not hours == 0 or not days == 0 else ""}{minutes}m {seconds}s'

    return f'{f"{days:02d}:" if not days == 0 else ""}{f"{hours:02d}:" if not hours == 0 or not days == 0 else ""}{minutes:02d}:{seconds:02d}'


def format_datetime(*, datetime: Union[dt.datetime, pendulum.datetime], seconds: bool = False) -> str:
    datetime = convert_datetime(datetime=datetime)
    return datetime.format(f'dddd MMMM Do YYYY [at] hh:mm{":ss" if seconds else ""} A zz{"ZZ" if datetime.timezone.name != "UTC" else ""}')


def format_date(*, datetime: Union[dt.datetime, pendulum.datetime]) -> str:
    return convert_datetime(datetime=datetime).format(f'dddd MMMM Do YYYY')


def format_difference(*, datetime: Union[dt.datetime, pendulum.datetime], suppress=None) -> str:

    if suppress is None:
        suppress = ['seconds']

    return humanize.precisedelta(pendulum.now(tz='UTC').diff(convert_datetime(datetime=datetime)), format='%0.0f', suppress=suppress)


def person_avatar(*, person: Union[discord.User, discord.Member]) -> str:
    return str(person.avatar_url_as(format='gif' if person.is_avatar_animated() else 'png'))


def line_count() -> Tuple[int, int, int, int]:

    files, functions, lines, classes = 0, 0, 0, 0
    is_docstring = False

    for dirpath, dirname, filenames in os.walk('.'):

        for filename in filenames:
            if not filename.endswith('.py'):
                continue
            files += 1

            with codecs.open('./' + str(pathlib.PurePath(dirpath, filename)), 'r', 'utf-8') as filelines:
                filelines = [line.strip() for line in filelines]
                for line in filelines:

                    if len(line) == 0:
                        continue

                    if line.startswith('"""'):
                        is_docstring = not is_docstring
                    if is_docstring:
                        continue

                    if line.startswith('#'):
                        continue
                    if line.startswith(('def', 'async def')):
                        functions += 1
                    if line.startswith('class'):
                        classes += 1
                    lines += 1

    return files, functions, lines, classes


def badges(*, bot: SemiBotomatic, person: Union[discord.User, discord.Member]) -> str:

    badges = [badge for name, badge in config.BADGE_EMOJIS.items() if dict(person.public_flags)[name] is True]
    if dict(person.public_flags)['verified_bot'] is False and person.bot:
        badges.append('<:bot:738979752244674674>')

    if any([guild.get_member(person.id).premium_since for guild in bot.guilds if person in guild.members]):
        badges.append('<:booster_level_4:738961099310760036>')

    if person.is_avatar_animated() or any([guild.get_member(person.id).premium_since for guild in bot.guilds if person in guild.members]):
        badges.append('<:nitro:738961134958149662>')

    elif member := discord.utils.get(bot.get_all_members(), id=person.id):
        if activity := discord.utils.get(member.activities, type=discord.ActivityType.custom):
            if activity.emoji and activity.emoji.is_custom_emoji():
                badges.append('<:nitro:738961134958149662>')

    return ' '.join(badges) if badges else 'N/A'


def activities(*, person: discord.Member) -> str:

    if not person.activities:
        return 'N/A'

    message = '\n'
    for activity in person.activities:

        if activity.type == discord.ActivityType.custom:
            message += f'• '
            if activity.emoji:
                message += f'{activity.emoji} '
            if activity.name:
                message += f'{activity.name}'
            message += '\n'

        elif activity.type == discord.ActivityType.playing:

            message += f'• Playing **{activity.name}** '
            if not isinstance(activity, discord.Game):
                if activity.details:
                    message += f'**| {activity.details}** '
                if activity.state:
                    message += f'**| {activity.state}** '
                message += '\n'

        elif activity.type == discord.ActivityType.streaming:
            message += f'• Streaming **[{activity.name}]({activity.url})** on **{activity.platform}**\n'

        elif activity.type == discord.ActivityType.watching:
            message += f'• Watching **{activity.name}**\n'

        elif activity.type == discord.ActivityType.listening:

            if isinstance(activity, discord.Spotify):
                url = f'https://open.spotify.com/track/{activity.track_id}'
                message += f'• Listening to **[{activity.title}]({url})** by **{", ".join(activity.artists)}** '
                if activity.album and activity.album != activity.title:
                    message += f'from the album **{activity.album}** '
                message += '\n'
            else:
                message += f'• Listening to **{activity.name}**\n'

    return message
