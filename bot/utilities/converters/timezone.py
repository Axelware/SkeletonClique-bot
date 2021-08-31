from abc import ABC

import pendulum
import rapidfuzz
from discord.ext import commands

from utilities import context, exceptions


class TimezoneConverter(commands.Converter, ABC):

    async def convert(self, ctx: context.Context, argument: str) -> pendulum.timezone:

        if argument not in pendulum.timezones:
            msg = '\n'.join(f'- `{match[0]}`' for index, match in rapidfuzz.process.extract(query=argument, choices=pendulum.timezones, processor=lambda s: s))
            raise exceptions.ArgumentError(f'That was not a recognised timezone. Maybe you meant one of these?\n{msg}')

        return pendulum.timezone(argument)
