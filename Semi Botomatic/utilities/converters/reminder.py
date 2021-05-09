from abc import ABC

from discord.ext import commands

import config
from utilities import context, enums, exceptions


class ReminderRepeatTypeConverter(commands.Converter, ABC):

    async def convert(self, ctx: context.Context, argument: str) -> enums.ReminderRepeatType:

        if enum := getattr(enums.ReminderRepeatType, argument.replace(' ', '_').upper(), None):
            return enum

        valid = [f"{repeat_type.name.replace('_', ' ').lower()}" for repeat_type in enums.ReminderRepeatType]
        raise exceptions.ArgumentError(f'Repeat type must be one of:\n{f"{config.NL}".join([f"- {v}" for v in valid])}')
