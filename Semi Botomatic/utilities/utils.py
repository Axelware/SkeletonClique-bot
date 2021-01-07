import logging

import humanize
import pendulum
import datetime as dt
from typing import Union
import discord
import mystbin


__log__ = logging.getLogger(__name__)


def convert_datetime(*, datetime: Union[dt.datetime, pendulum.datetime]) -> pendulum.datetime:
    return pendulum.instance(datetime) if isinstance(datetime, dt.datetime) else datetime


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
    return datetime.format(f'dddd MMMM do YYYY [at] hh:mm{":ss" if seconds else ""} A zz{"ZZ" if datetime.timezone.name != "UTC" else ""}')


def format_date(*, datetime: Union[dt.datetime, pendulum.datetime]) -> str:
    return convert_datetime(datetime=datetime).format(f'dddd MMMM do YYYY')


def format_difference(*, datetime: Union[dt.datetime, pendulum.datetime], suppress=None) -> str:

    if suppress is None:
        suppress = ['seconds']

    return humanize.precisedelta(pendulum.now(tz='UTC').diff(convert_datetime(datetime=datetime)), format='%0.0f', suppress=suppress)


def person_avatar(*, person: Union[discord.User, discord.Member]) -> str:
    return str(person.avatar_url_as(format='gif' if person.is_avatar_animated() else 'png'))


async def safe_text(*, mystbin_client: mystbin.Client, text: str) -> str:

    if len(text) <= 1024:
        return text

    try:
        mystbin_link = await mystbin_client.post(text, syntax='python')
    except mystbin.APIError as error:
        __log__.warning(f'[ERRORS] Error while uploading error traceback to mystbin | Code: {error.status_code} | Message: {error.message}')
        mystbin_link = f'{text[:1024]}'

    return mystbin_link
