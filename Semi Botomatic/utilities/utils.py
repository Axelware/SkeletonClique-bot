from __future__ import annotations

import codecs
import colorsys
import datetime as dt
import logging
import os
import pathlib
from typing import TYPE_CHECKING, Union

import PIL.ImageDraw
from PIL import ImageFont
import discord
import humanize
import mystbin
import pendulum
from pendulum.datetime import DateTime

import config

if TYPE_CHECKING:
    from bot import SemiBotomatic

__log__ = logging.getLogger(__name__)


async def safe_text(text: str, mystbin_client: mystbin.Client, max_characters: int = 1024, syntax: str = 'python') -> str:

    if len(text) <= max_characters:
        return text

    try:
        return await mystbin_client.post(text, syntax=syntax)
    except mystbin.APIError as error:
        __log__.warning(f'[ERRORS] Error while uploading error traceback to mystbin | Code: {error.status_code} | Message: {error.message}')
        return f'{text[:max_characters]}'  # Not the best solution.


def convert_datetime(datetime: Union[dt.datetime, DateTime]) -> DateTime:
    return pendulum.instance(datetime, tz='UTC') if isinstance(datetime, dt.datetime) else datetime


def format_datetime(datetime: Union[dt.datetime, DateTime], *, seconds: bool = False) -> str:
    datetime = convert_datetime(datetime=datetime)
    return datetime.format(f'dddd MMMM Do YYYY [at] hh:mm{":ss" if seconds else ""} A zz{"ZZ" if datetime.timezone.name != "UTC" else ""}')


def format_date(datetime: Union[dt.datetime, DateTime]) -> str:
    return convert_datetime(datetime=datetime).format('dddd MMMM Do YYYY')


def format_difference(datetime: Union[dt.datetime, DateTime], *, suppress=None) -> str:

    if suppress is None:
        suppress = ['seconds']

    return humanize.precisedelta(pendulum.now(tz='UTC').diff(convert_datetime(datetime=datetime)), format='%0.0f', suppress=suppress)


def format_seconds(seconds: int, *, friendly: bool = False) -> str:

    minute, second = divmod(seconds, 60)
    hour, minute = divmod(minute, 60)
    day, hour = divmod(hour, 24)

    days, hours, minutes, seconds = round(day), round(hour), round(minute), round(second)

    if friendly is True:
        return f'{f"{days}d " if not days == 0 else ""}{f"{hours}h " if not hours == 0 or not days == 0 else ""}{minutes}m {seconds}s'

    return f'{f"{days:02d}:" if not days == 0 else ""}{f"{hours:02d}:" if not hours == 0 or not days == 0 else ""}{minutes:02d}:{seconds:02d}'


def line_count() -> tuple[int, int, int, int]:

    files, functions, lines, classes = 0, 0, 0, 0
    is_docstring = False

    for dirpath, _, filenames in os.walk('.'):

        for filename in filenames:
            if not filename.endswith('.py'):
                continue
            files += 1

            # noinspection PyArgumentEqualDefault
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


def badges(bot: SemiBotomatic, person: Union[discord.User, discord.Member]) -> str:

    badges_list = [badge for badge_name, badge in config.BADGE_EMOJIS.items() if dict(person.public_flags)[name] is True]
    if dict(person.public_flags)['verified_bot'] is False and person.bot:
        badges_list.append('<:bot:738979752244674674>')

    if any(getattr(guild.get_member(person.id), 'premium_since', None) for guild in bot.guilds):
        badges_list.append('<:booster_level_4:738961099310760036>')

    if person.is_avatar_animated() or any(getattr(guild.get_member(person.id), 'premium_since', None) for guild in bot.guilds):
        badges_list.append('<:nitro:738961134958149662>')

    elif member := discord.utils.get(bot.get_all_members(), id=person.id):  # skipcq: PTC-W0048
        if activity := discord.utils.get(member.activities, type=discord.ActivityType.custom):
            if activity.emoji and activity.emoji.is_custom_emoji():
                badges_list.append('<:nitro:738961134958149662>')

    return ' '.join(badges_list) if badges_list else 'N/A'


def avatar(person: Union[discord.User, discord.Member], img_format: str = None) -> str:
    return str(person.avatar_url_as(format=img_format or 'gif' if person.is_avatar_animated() else 'png'))


def icon(guild: discord.Guild, img_format: str = None) -> str:
    return str(guild.icon_url_as(format=img_format or 'gif' if guild.is_icon_animated() else 'png'))


def activities(person: discord.Member) -> str:  # sourcery no-metrics

    if not person.activities:
        return 'N/A'

    message = '\n'
    for activity in person.activities:

        if activity.type == discord.ActivityType.custom:
            message += '• '
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


def channel_emoji(channel: Union[discord.TextChannel, discord.VoiceChannel]) -> str:

    overwrites = channel.overwrites_for(channel.guild.default_role)

    if isinstance(channel, discord.VoiceChannel):
        emoji = 'voice' if overwrites.connect else 'voice_locked'
    else:
        if channel.is_news():
            emoji = 'news' if overwrites.read_messages else 'news_locked'
        elif channel.is_nsfw():
            emoji = 'text_nsfw'
        else:
            emoji = 'text' if overwrites.read_messages else 'text_locked'

    return config.CHANNEL_EMOJIS[emoji]


def darken_colour(r, g, b, factor: float = 0.1) -> tuple[float, float, float]:

    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    r, g, b = colorsys.hls_to_rgb(h, max(min(l * (1 - factor), 1.0), 0.0), s)
    return int(r * 255), int(g * 255), int(b * 255)


def lighten_colour(r, g, b, factor: float = 0.1) -> tuple[float, float, float]:
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    r, g, b = colorsys.hls_to_rgb(h, max(min(l * (1 + factor), 1.0), 0.0), s)
    return int(r * 255), int(g * 255), int(b * 255)


def name(person: Union[discord.Member, discord.User], *, guild: discord.Guild = None) -> str:

    if guild and isinstance(person, discord.User):
        member = guild.get_member(person.id)
        return member.nick or member.name if isinstance(member, discord.Member) else person.name

    return person.nick or person.name if isinstance(person, discord.Member) else person.name


def find_font_size(text: str, font: PIL.ImageFont, size: int, draw: PIL.ImageDraw, x_bound: int, y_bound: int) -> PIL.ImageFont:

    font_sized = ImageFont.truetype(font=font, size=size)

    while draw.textsize(text=text, font=font_sized) > (x_bound, y_bound):
        size -= 1
        font_sized = ImageFont.truetype(font=font, size=size)

    return font_sized


def voice_region(x: Union[discord.VoiceChannel, discord.StageChannel, discord.Guild]) -> str:

    x = x.rtc_region if isinstance(x, (discord.VoiceChannel, discord.StageChannel)) else x.region
    if not x:
        return 'Automatic'

    region = x.name.title().replace('Vip', 'VIP').replace('_', '-').replace('Us-', 'US-')
    if x == discord.VoiceRegion.hongkong:
        region = 'Hong Kong'
    if x == discord.VoiceRegion.southafrica:
        region = 'South Africa'

    return region
