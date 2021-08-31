# Future
from __future__ import annotations

# Packages
from discord.ext import commands, tasks

# My stuff
from core.bot import SkeletonClique


class Background(commands.Cog):

    def __init__(self, bot: SkeletonClique) -> None:
        self.bot = bot
        self.clear.start()

    def cog_unload(self) -> None:
        self.clear.cancel()

    @tasks.loop(minutes=5)
    async def clear(self) -> None:

        if (fun := self.bot.get_cog('Fun')) is not None:
            fun.RATES = {}
            fun.PREDICTIONS = {}

    @clear.before_loop
    async def before_clear_states(self) -> None:
        await self.bot.wait_until_ready()


def setup(bot: SkeletonClique) -> None:
    bot.add_cog(Background(bot=bot))
