import random

import discord
from discord.ext import commands

from bot import SemiBotomatic
from utilities import context, exceptions, objects, utils


class Economy(commands.Cog):

    def __init__(self, bot: SemiBotomatic) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:

        if message.author.bot:
            return

        if await self.bot.redis.exists(f'{message.author.id}_xp_gain') is True:
            return

        if not (user_config := self.bot.user_manager.get_config(message.author.id)):
            user_config = await self.bot.user_manager.create_config(message.author.id)

        xp = random.randint(10, 25)

        if xp >= user_config.next_level_xp:
            self.bot.dispatch('xp_level_up', user_config, message)

        user_config.change_xp(xp)
        await self.bot.redis.setex(name=f'{message.author.id}_xp_gain', time=60, value=None)

    @commands.Cog.listener()
    async def on_xp_level_up(self, user_config: objects.UserConfig, message: discord.Message) -> None:

        if not user_config.notifications.level_ups:
            return

        await message.reply(f'You are now level `{user_config.level}`!')

    #

    @commands.command(name='level', aliases=['xp', 'score', 'rank'])
    async def level(self, ctx: context.Context, *, member: discord.Member = None) -> None:
        """
        Display yours, or someone else's level / xp information.

        `member`: The member of which to get the level for. Can be their ID, Username, Nickname or @Mention. Defaults to you.
        """

        if not member:
            member = ctx.author

        async with ctx.typing():
            file = await self.bot.user_manager.create_level_card(member.id, guild_id=getattr(ctx.guild, 'id', None))
            await ctx.reply(file=file)

    @commands.group(name='leaderboard', aliases=['lb'], invoke_without_command=True)
    async def leaderboard(self, ctx: context.Context, *, page: int = 1) -> None:
        """
        Display the leaderboard for xp, rank, and level.
        """

        async with ctx.typing():
            file = await self.bot.user_manager.create_leaderboard(page=page, guild_id=getattr(ctx.guild, 'id', None))
            await ctx.reply(file=file)

    @leaderboard.command(name='text')
    async def leaderboard_text(self, ctx: context.Context) -> None:
        """
        Display the xp leaderboard in a text table.
        """

        if not (leaderboard := self.bot.user_manager.leaderboard()):
            raise exceptions.ArgumentError('There are no leaderboard stats.')

        header =  '╔═══════╦═══════════╦═══════╦═══════════════════════════════════════╗\n' \
                  '║ Rank  ║ XP        ║ Level ║ Name                                  ║\n' \
                  '╠═══════╬═══════════╬═══════╬═══════════════════════════════════════╣\n'

        footer =  '\n' \
                  '║       ║           ║       ║                                       ║\n' \
                 f'║ {self.bot.user_manager.rank(ctx.author.id):<5} ║ {ctx.user_config.xp:<9} ║ {ctx.user_config.level:<5} ║ {str(ctx.author):<37} ║\n' \
                  '╚═══════╩═══════════╩═══════╩═══════════════════════════════════════╝\n\n'

        entries = [
            f'║ {index + 1:<5} ║ {user_config.xp:<9} ║ {user_config.level:<5} ║ {utils.name(person=self.bot.get_user(user_config.id), guild=ctx.guild):<37} ║'
            for index, user_config in enumerate(leaderboard)
        ]

        await ctx.paginate(entries=entries, per_page=10, header=header, footer=footer, codeblock=True)


def setup(bot: SemiBotomatic) -> None:
    bot.add_cog(Economy(bot=bot))
