# Future
from __future__ import annotations

# Standard Library
from typing import Literal

# Packages
from discord.ext import commands

# My stuff
from core import colours, emojis
from core.bot import SkeletonClique
from utilities import checks, context, enums, exceptions, utils


def setup(bot: SkeletonClique) -> None:
    bot.add_cog(Settings(bot=bot))


class Settings(commands.Cog):

    def __init__(self, bot: SkeletonClique) -> None:
        self.bot = bot

    @commands.command(name="embedsize", aliases=["embed-size", "embed_size", "es"])
    async def embed_size(
        self,
        ctx: context.Context,
        operation: Literal["set", "reset"] = utils.MISSING,
        size: Literal["large", "medium", "small"] = utils.MISSING
    ) -> None:
        """
        Manage this servers embed size settings.

        **operation**: The operation to perform, can be **set** or **reset**.
        **size**: The size to set embeds too. Can be **large**, **medium** or **small**.
        """

        guild_config = await self.bot.guild_manager.get_config(ctx.guild.id)

        if not operation:
            embed = utils.embed(
                description=f"The embed size is **{guild_config.embed_size.name.title()}**."
            )
            await ctx.reply(embed=embed)
            return

        try:
            await checks.is_mod().predicate(ctx=ctx)
        except commands.CheckAnyFailure:
            raise exceptions.EmbedError(
                colour=colours.RED,
                emoji=emojis.CROSS,
                description=f"You do not have permission to edit the bots embed size in this server."
            )

        if operation == "set":

            if not size:
                raise exceptions.EmbedError(
                    colour=colours.RED,
                    emoji=emojis.CROSS,
                    description=f"You didn't provide an embed size."
                )

            embed_size = getattr(enums.EmbedSize, size.upper(), None)

            if guild_config.embed_size is embed_size:
                raise exceptions.EmbedError(
                    colour=colours.RED,
                    emoji=emojis.CROSS,
                    description=f"The embed size is already **{embed_size.name.title()}**."
                )

            await guild_config.set_embed_size(embed_size)

            embed = utils.embed(
                colour=colours.GREEN,
                emoji=emojis.TICK,
                description=f"Set the embed size to **{embed_size.name.title()}**."
            )
            await ctx.reply(embed=embed)

        elif operation == "reset":

            if guild_config.embed_size is enums.EmbedSize.MEDIUM:
                raise exceptions.EmbedError(
                    colour=colours.RED,
                    emoji=emojis.CROSS,
                    description=f"The embed size is already the default of **Medium**."
                )

            await guild_config.set_embed_size(enums.EmbedSize.MEDIUM)

            embed = utils.embed(
                colour=colours.GREEN,
                emoji=emojis.TICK,
                description=f"Reset the embed size to **Medium**."
            )
            await ctx.reply(embed=embed)
