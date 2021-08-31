# Future
from __future__ import annotations

# Packages
import discord
from discord.ext import commands

# My stuff
from utilities import context


class PersonConverter(commands.Converter):

    async def convert(self, ctx: context.Context, argument: str) -> discord.Member | discord.User:

        person = None

        try:
            person = await commands.MemberConverter().convert(ctx, argument)
        except commands.MemberNotFound:
            pass

        if not person:
            try:
                person = await commands.Converter().convert(ctx, argument)
            except commands.UserNotFound:
                pass

        if not person:
            raise commands.MemberNotFound(argument)

        return person
