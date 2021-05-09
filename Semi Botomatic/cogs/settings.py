from typing import Literal

import discord
from discord.ext import commands

import config
from bot import SemiBotomatic
from utilities import context, enums, exceptions


class Settings(commands.Cog):

    def __init__(self, bot: SemiBotomatic) -> None:
        self.bot = bot

    @commands.group(name='settings', aliases=['config'], invoke_without_command=True)
    async def settings(self, ctx: context.Context) -> None:
        pass

    #

    @settings.group(name='user', invoke_without_command=True)
    async def settings_user(self, ctx: context.Context) -> None:
        pass

    #

    @settings.group(name='guild', invoke_without_command=True)
    async def settings_guild(self, ctx: context.Context) -> None:
        pass

    @settings_guild.command(name='colour', aliases=['color'])
    async def settings_guild_colour(self, ctx: context.Context, operation: Literal['set', 'reset'] = None, *, colour: commands.ColourConverter = None) -> None:
        """
        Manage this servers colour settings.

        Please note that to view the colour, no permissions are needed, however to change it you require the `manage_guild` permission.

        `operation`: The operation to perform, `set` to set the colour, `reset` to revert to the default. If not provided the current colour will be displayed.
        `colour`: The colour to set. Possible formats include `0x<hex>`, `#<hex>`, `0x#<hex>` and `rgb(<number>, <number>, <number>)`. `<number>` can be `0 - 255` or `0% to 100%` and `<hex>` can be `#FFF` or `#FFFFFF`.
        """

        if not operation:
            await ctx.send(embed=discord.Embed(colour=ctx.guild_config.colour, title=str(ctx.guild_config.colour).upper()))
            return

        if await self.bot.is_owner(ctx.author) is False:
            await commands.has_guild_permissions(manage_guild=True).predicate(ctx=ctx)

        old_colour = ctx.guild_config.colour

        if operation == 'reset':

            if ctx.guild_config.colour == discord.Colour(config.COLOUR):
                raise exceptions.ArgumentError('This servers colour is already the default.')

            await ctx.guild_config.set_colour()

        elif operation == 'set':

            if not colour:
                raise exceptions.ArgumentError('You did not provide a valid colour argument.')
            if ctx.guild_config.colour == colour:
                raise exceptions.ArgumentError(f'This servers colour is already `{str(colour).upper()}`.')

            # noinspection PyTypeChecker
            await ctx.guild_config.set_colour(colour)

        await ctx.send(embed=discord.Embed(colour=old_colour, title=f'Old: {str(old_colour).upper()}'))
        await ctx.send(embed=discord.Embed(colour=ctx.guild_config.colour, title=f'New: {str(ctx.guild_config.colour).upper()}'))

    @settings_guild.command(name='embed-size', aliases=['embedsize', 'es'])
    async def settings_guild_embed_size(self, ctx: context.Context, operation: Literal['set', 'reset'] = None, size: Literal['large', 'medium', 'small'] = None) -> None:
        """
        Manage this servers embed size settings.

        Please note that to view the current size, no permissions are needed, however to change it you require the `manage_guild` permission.

        `operation`: The operation to perform, `set` to change it or `reset` to revert it to the default. If not provided the current size will be displayed.
        `size`: The size to set embeds too. Can be `large`, `medium` or `small`.
        """

        if not operation:
            await ctx.send(f'This servers embed size is `{ctx.guild_config.embed_size.name.title()}`.')
            return

        if await self.bot.is_owner(user=ctx.author) is False:
            await commands.has_guild_permissions(manage_guild=True).predicate(ctx=ctx)

        if operation == 'reset':

            if ctx.guild_config.embed_size == enums.EmbedSize.LARGE:
                raise exceptions.ArgumentError('This servers embed size is already the default.')

            await ctx.guild_config.set_embed_size()
            await ctx.send('Reset this servers embed size.')

        elif operation == 'set':

            if not size:
                raise exceptions.ArgumentError('You did not provide a valid size.')
            if ctx.guild_config.embed_size == getattr(enums.EmbedSize, size.upper()):
                raise exceptions.ArgumentError(f'This servers embed size is already `{ctx.guild_config.embed_size.name.title()}`.')

            await ctx.guild_config.set_embed_size(getattr(enums.EmbedSize, size.upper()))
            await ctx.send(f'Set this servers embed size to `{ctx.guild_config.embed_size.name.title()}`.')


def setup(bot: SemiBotomatic) -> None:
    bot.add_cog(Settings(bot=bot))
