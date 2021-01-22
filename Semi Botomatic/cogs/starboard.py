import discord
from discord.ext import commands

import config
from bot import SemiBotomatic


class Starboard(commands.Cog):

    def __init__(self, bot: SemiBotomatic) -> None:
        self.bot = bot

        self.STARBOARD = discord.Webhook.from_url(url=config.STARBOARD_WEBHOOK, adapter=discord.AsyncWebhookAdapter(session=self.bot.session))

        self.STAR_EMOJI = {
            'basic':     '\U00002b50',
            'glowing':   '\U0001f31f',
            'sparkles':  '\U00002728',
            'shooting':  '\U0001f4ab',
            'star_eyes': '\U0001f929'
        }
        self.STAR_COLOURS = {
            'basic':     0xFFE226,
            'glowing':   0xDEAD23,
            'sparkles':  0xFFAD33,
            'shooting':  0xE87523,
            'star_eyes': 0xFF5626,
        }

    async def load(self) -> None:
        pass

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        pass

    @commands.Cog.listener()
    async def on_raw_reaction_clear(self, payload: discord.RawReactionActionEvent) -> None:
        pass

    @commands.Cog.listener()
    async def on_raw_reaction_clear_emoji(self, payload: discord.RawReactionActionEvent) -> None:
        pass


def setup(bot: SemiBotomatic) -> None:
    bot.add_cog(Starboard(bot=bot))
