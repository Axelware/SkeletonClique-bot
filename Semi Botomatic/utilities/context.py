import asyncio
from typing import Any, Optional

import discord
from discord.ext import commands

import config
from utilities import exceptions, paginators


class Context(commands.Context):

    @property
    def colour(self):
        return self.top_colour_role if isinstance(self.author, discord.Member) else discord.Colour(config.COLOUR)

    @property
    def top_colour_role(self) -> Optional[discord.Colour]:

        colour_roles = [role for role in self.author.roles if role.colour.value != 0]

        if not colour_roles:
            return None

        return colour_roles[0].colour

    async def paginate(self, **kwargs) -> paginators.Paginator:
        paginator = paginators.Paginator(ctx=self, **kwargs)
        await paginator.paginate()
        return paginator

    async def paginate_embed(self, **kwargs) -> paginators.EmbedPaginator:
        paginator = paginators.EmbedPaginator(ctx=self, **kwargs)
        await paginator.paginate()
        return paginator

    async def paginate_embeds(self, **kwargs) -> paginators.EmbedsPaginator:
        paginator = paginators.EmbedsPaginator(ctx=self, **kwargs)
        await paginator.paginate()
        return paginator

    async def paginate_choice(self, **kwargs) -> Any:

        paginator = await self.paginate_embed(**kwargs)

        try:
            response = await self.bot.wait_for('message', check=lambda msg: msg.author == self.author and msg.channel == self.channel, timeout=30.0)
        except asyncio.TimeoutError:
            raise exceptions.ArgumentError('You took too long to respond.')

        response = await commands.clean_content().convert(ctx=self, argument=response.content)
        try:
            response = int(response) - 1
        except ValueError:
            raise exceptions.ArgumentError('That was not a valid number.')
        if response < 0 or response >= len(kwargs.get('entries')):
            raise exceptions.ArgumentError('That was not one of the available options.')

        await paginator.stop()
        return kwargs.get('entries')[response]