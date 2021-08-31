import collections
import random
import urllib.parse
from typing import Optional, Union

import discord
from discord.ext import commands

from bot import SemiBotomatic
from utilities import context, exceptions


class Fun(commands.Cog):

    def __init__(self, bot: SemiBotomatic) -> None:
        self.bot = bot

        self.RESPONSES = ['Yeah!', 'Hell yeah!!', 'I think so?', 'Maybe, not sure', 'Totally', 'Of course', 'Yes', 'Perhaps...',
                          'If you believe in yourself, you can surely do it.', 'Nah', 'Nope', 'Definitely not', 'WHAT, are you insane???',
                          'Sorry I had you muted, can you ask me again?', 'I didn’t quite catch that, can you repeat']

        self.RATINGS = [
            '-100, I don\'t ever want to hear that name again!',
            '-10 :nauseated_face:',
            '0.',
            '1.',
            '2, who even is that?? never heard of them...',
            '3.',
            '4, they\'re ok, I guess :rolling_eyes:',
            '5.',
            '6.',
            '7.',
            '8.',
            '9.',
            '10 :fire:',
            '100 :star_struck: :star_struck:',
            '1000 :flushed:'
        ]

        self.RATES = {}
        self.PREDICTIONS = {}

    @commands.command(name='8ball')
    async def _8ball(self, ctx: context.Context, *, question: str = None) -> None:
        """
        Predicts the future of your question...

        `question`: The question that would like to be answered.
        """

        if not question:
            raise exceptions.ArgumentError('c\'mon kid, you have to ask me something, how can I predict something from nothing?')

        question = ''.join(str(question).split('\n'))

        if self.PREDICTIONS.get(question) is None:
            self.PREDICTIONS[question] = random.choice(self.RESPONSES)

        await ctx.reply(self.PREDICTIONS[question])

    @commands.command(name='rate', aliases=['rateme'])
    async def rate(self, ctx: context.Context, *, thing: Union[discord.Member, str] = None) -> None:
        """
        Rates someone, or something.

        `thing`: The thing to rate, can be anything from a members id or name to a sport like football!
        """

        if thing is None:
            thing = ctx.author

        thing = ''.join(str(thing).split('\n'))

        if self.RATES.get(thing) is None:
            self.RATES[thing] = random.choice(self.RATINGS)

        await ctx.reply(f'I\'d rate {thing} a {self.RATES[thing]}')

    @commands.command(name='choose', aliases=['choice'])
    async def choose(self, ctx: context.Context, *choices: commands.clean_content) -> None:
        """
        Chooses something from a list of choices.

        `choices`: A list of choices to choose from. These should be separated using just quotes. For example `!choose "Do coding" "Do gaming"`
        """

        if len(choices) <= 1:
            raise exceptions.ArgumentError('Not enough choices to choose from.')

        await ctx.reply(random.choice(list(map(str, choices))))

    @commands.command(name='choosebestof', aliases=['cbo', 'bestof'])
    async def choosebestof(self, ctx: context.Context, times: Optional[int], *choices: commands.clean_content) -> None:
        """
        Chooses the best option from a list of choices.

        `times`: An amount of times to calculate choices with, more times will equal more 'accurate' results.
        `choices`: A list of choices to choose from. These should be separated using just quotes. For example `!bestof 99999 "Do coding" "Do gaming"`
        """

        if len(choices) <= 1:
            raise exceptions.ArgumentError('Not enough choices to choose from.')
        if times and times > 9999999:
            raise exceptions.ArgumentError('That a bit too many times...')

        times = min(10001, max(1, (len(choices) ** 2) + 1 if times is None else times))

        counter = collections.Counter(random.choice(list(map(str, choices))) for _ in range(times))
        entries = [f'{item[:15] + (item[15:] and ".."):17} | {count / times:.2%}' for item, count in counter.most_common()]
        await ctx.paginate_embed(entries=entries, per_page=10, codeblock=True, header='Choice            | Percentage\n')

    @commands.command(name='book')
    async def book(self, ctx: context.Context, *, language: str = None) -> None:

        if language:
            async with self.bot.session.get(f'https://senpy.tk/api/v1/{urllib.parse.quote(language)}') as request:

                if await request.text() == 'Invalid API Endpoint.':
                    raise exceptions.ArgumentError('That was not a valid language.')

                data = await request.json()
                language = data.get('language')
                image = data.get('random')

        else:

            async with self.bot.session.get('https://senpy.tk/api/v1') as request:
                data = await request.json()
                language = data.get('imagerandomlanguage')
                image = data.get('imagerandom')

        embed = discord.Embed(colour=ctx.colour, title=f'{language}!')
        embed.set_image(url=f'https://github.com/laynH/Anime-Girls-Holding-Programming-Books/blob/master/{urllib.parse.quote(language)}/{urllib.parse.quote(image)}?raw=true')
        await ctx.reply(embed=embed)


def setup(bot: SemiBotomatic) -> None:
    bot.add_cog(Fun(bot=bot))
