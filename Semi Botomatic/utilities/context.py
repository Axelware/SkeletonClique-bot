import asyncio
from typing import Any, Optional, Union

import discord
from discord.ext import commands

import config
from utilities import exceptions, objects, paginators


class Context(commands.Context):

    _guild_config = objects.GuildConfig(data={'embed_size': 'small'})

    @property
    def user_config(self) -> Union[objects.DefaultUserConfig, objects.UserConfig]:

        if not self.author:
            return self.bot.user_manager.default_user_config

        return self.bot.user_manager.get_user_config(user_id=self.author.id)

    @property
    def guild_config(self) -> Union[objects.DefaultGuildConfig, objects.GuildConfig]:
        return self._guild_config

    @property
    def top_role_colour(self) -> Optional[discord.Colour]:

        roles = list(reversed([role for role in self.author.roles if role.colour.value != 0]))
        if not roles:
            return discord.Colour(config.COLOUR)

        return roles[0].colour

    @property
    def colour(self):
        return self.top_role_colour if isinstance(self.author, discord.Member) else discord.Colour(config.COLOUR)

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
                return await self.channel.send(**kwargs)
            except discord.Forbidden:
                return None
