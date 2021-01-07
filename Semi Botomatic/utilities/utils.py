import humanize
import pendulum
import datetime as dt
from typing import Union


def convert_datetime(*, datetime: Union[pendulum.datetime, dt.datetime]) -> pendulum.datetime:

    if isinstance(datetime, dt.datetime):
        datetime = pendulum.instance(datetime)

    return datetime


def format_seconds(*, seconds: int, friendly: bool = False) -> str:

    minute, second = divmod(seconds, 60)
    hour, minute = divmod(minute, 60)
    day, hour = divmod(hour, 24)

    days, hours, minutes, seconds = round(day), round(hour), round(minute), round(second)

    if friendly is True:
        return f'{f"{days}d " if not days == 0 else ""}{f"{hours}h " if not hours == 0 or not days == 0 else ""}{minutes}m {seconds}s'

    return f'{f"{days:02d}:" if not days == 0 else ""}{f"{hours:02d}:" if not hours == 0 or not days == 0 else ""}{minutes:02d}:{seconds:02d}'


def format_datetime(*, datetime: Union[pendulum.datetime, dt.datetime], seconds: bool = False) -> str:
    datetime = convert_datetime(datetime=datetime)
    return datetime.format(f'dddd Do [of] MMMM YYYY [at] HH:mm{":ss" if seconds else ""} A (zz{"ZZ" if datetime.timezone != "UTC" else ""})')


def format_date(*, datetime: Union[pendulum.datetime, dt.datetime]) -> str:
    return convert_datetime(datetime=datetime).format(f'dddd Do [of] MMMM YYYY')


def format_difference(*, datetime: Union[pendulum.datetime, dt.datetime], suppress=None) -> str:
    if suppress is None:
        suppress = ['seconds']

    return humanize.precisedelta(pendulum.now(tz='UTC').diff(convert_datetime(datetime=datetime)), format='%0.0f', suppress=suppress)