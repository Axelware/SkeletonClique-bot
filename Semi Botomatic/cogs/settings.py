from typing import Literal

import discord
from discord.ext import commands

from bot import SemiBotomatic
from utilities import context, enums, exceptions


class Settings(commands.Cog):

    def __init__(self, bot: SemiBotomatic) -> None:
        self.bot = bot

    @commands.group(name='settings', aliases=['config'], invoke_without_command=True)
    async def settings(self, ctx: context.Context) -> None:
        """
        Display this servers settings.
        """

        embed = discord.Embed(
                colour=ctx.colour,
                title=f'Guild settings:',
                description=f'`Embed size`: {ctx.guild_config.embed_size.name.title()}'
        )
        await ctx.send(embed=embed)

    @settings.command(name='embed-size', aliases=['embedsize', 'es'])
    async def config_embed_size(self, ctx: context.Context, operation: Literal['set', 'reset'] = None, size: Literal['large', 'medium', 'small'] = None) -> None:
        """
        Manage this servers embed size settings.

        Please note that to view the the current size, no permissions are needed, however to change it you require the `manage_guild` permission.

        `operation`: The operation to perform, `set` to change it or `reset` to revert it to the default. If not provided the current size will be displayed.
        `size`: The size to set embeds too. Can be `large`, `medium` or `small`.
        """

        if not operation:
            await ctx.send(f'This servers embed size is `{ctx.guild_config.embed_size.name.title()}`.')
            return

        if await self.bot.is_owner(person=ctx.author) is False:
            await commands.has_guild_permissions(manage_guild=True).predicate(ctx=ctx)

        if operation == 'set':

            if not size:
                raise exceptions.ArgumentError('You did not provide a valid size. Available sizes are `large`, `medium` or `small`.')

            await self.bot.guild_manager.set_embed_size(guild_id=ctx.guild.id, embed_size=getattr(enums.EmbedSize, size.upper()))
            await ctx.send(f'Set this servers embed size to `{size.title()}`.')

        elif operation == 'reset':

            await self.bot.guild_manager.set_embed_size(guild_id=ctx.guild.id)
            await ctx.send(f'Set this servers embed size to `Large`.')


def setup(bot: SemiBotomatic):
    bot.add_cog(Settings(bot))