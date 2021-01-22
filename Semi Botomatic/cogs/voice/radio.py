import secrets

import discord
from discord.ext import commands

import config
from bot import SemiBotomatic
from utilities import context, exceptions
from utilities.spotify import client


class Radio(commands.Cog):

    def __init__(self, bot: SemiBotomatic) -> None:
        self.bot = bot

        self.bot.spotify = client.Client(bot=self.bot)

    @commands.command(name='authorise', aliases=['auth'])
    async def authorise(self, ctx: context.Context) -> None:

        if ctx.author.id not in self.bot.spotify.user_auth_states.values():
            self.bot.spotify.user_auth_states[secrets.token_urlsafe(nbytes=32)] = ctx.author.id

        url = f'https://accounts.spotify.com/authorize/?' \
              f'client_id={config.SPOTIFY_CLIENT_ID}&' \
              f'response_type=code&' \
              f'redirect_uri=http://{config.WEB_URL}/api/spotify/callback&' \
              f'state={list(self.bot.spotify.user_auth_states.keys())[list(self.bot.spotify.user_auth_states.values()).index(ctx.author.id)]}&' \
              f'scope=user-read-recently-played+user-top-read+user-read-currently-playing+playlist-read-private+playlist-read-collaborative+user-read-private&' \
              f'show_dialog=True'

        embed = discord.Embed(colour=ctx.colour, title='Spotify authorisation link:',
                              description=f'Please click [this link]({url}) to authorise this discord account with your spotify account. Do not share this link with anyone as '
                                          f'it will allow people to link their spotify with your account.')

        try:
            await ctx.author.send(embed=embed)
        except discord.Forbidden:
            raise exceptions.VoiceError('I am unable to send direct messages to you, please enable them so that I can DM you your spotify authorisation link.')


def setup(bot: SemiBotomatic):
    bot.add_cog(Radio(bot=bot))
