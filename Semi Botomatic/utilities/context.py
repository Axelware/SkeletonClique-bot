from __future__ import annotations

import asyncio
from typing import Any, Optional, TYPE_CHECKING, Union

import discord
from discord.ext import commands

import config
from utilities import exceptions, objects, paginators

if TYPE_CHECKING:
    from cogs.voice.custom.player import Player
    from bot import SemiBotomatic


class Context(commands.Context):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.bot: SemiBotomatic = kwargs.get('bot')

    #

    @property
    def voice_client(self) -> Player:
        return self.guild.voice_client if self.guild else None

    #

    @property
    def user_config(self) -> Union[objects.DefaultUserConfig, objects.UserConfig]:
        return self.bot.user_manager.configs.get(getattr(self.author, 'id', None), self.bot.user_manager.default_config)

    @property
    def guild_config(self) -> Union[objects.DefaultGuildConfig, objects.GuildConfig]:
        return self.bot.guild_manager.configs.get(getattr(self.guild, 'id', None), self.bot.guild_manager.default_config)

    @property
    def colour(self) -> discord.Colour:

        if isinstance(self.author, discord.Member):  # skipcq: PTC-W0048
            if roles := list(reversed([role for role in self.author.roles if role.colour.value != 0])):
                return roles[0].colour

        return discord.Colour(config.COLOUR)

    #

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
            response = await self.bot.wait_for('message', check=lambda msg: msg.author.id == self.author.id and msg.channel.id == self.channel.id, timeout=30.0)
        except asyncio.TimeoutError:
            raise exceptions.ArgumentError('You took too long to respond.')

        response = await commands.clean_content().convert(ctx=self, argument=response.content)
        try:
            response = int(response) - 1
        except ValueError:
            raise exceptions.ArgumentError('That was not a valid number.')
        if response < 0 or response >= len(kwargs.get('entries')):
            raise exceptions.ArgumentError('That was not one of the available choices.')

        await paginator.stop()
        return response

    async def try_dm(self, **kwargs) -> Optional[discord.Message]:

        try:
            return await self.author.send(**kwargs)
        except discord.Forbidden:
            try:
                return await self.reply(**kwargs)
            except discord.Forbidden:
                return None
