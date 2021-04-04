import secrets

import discord
from discord.ext import commands

import config
from bot import SemiBotomatic
from utilities import context, exceptions


class Radio(commands.Cog):

    def __init__(self, bot: SemiBotomatic) -> None:
        self.bot = bot

    @commands.command(name='authorise', aliases=['auth'])
    async def authorise(self, ctx: context.Context) -> None:

        if ctx.author.id not in self.bot.spotify.user_auth_states.values():
            self.bot.spotify.user_auth_states[secrets.token_urlsafe(nbytes=32)] = ctx.author.id

        url = f'https://accounts.spotify.com/authorize/?' \
              f'client_id={config.SPOTIFY_CLIENT_ID}&' \
              f'response_type=code&' \
              f'redirect_uri={config.SPOTIFY_CALLBACK_URI}api/spotify/callback&' \
              f'state={list(self.bot.spotify.user_auth_states.keys())[list(self.bot.spotify.user_auth_states.values()).index(ctx.author.id)]}&' \
              f'scope=user-read-recently-played+user-top-read+user-read-currently-playing+playlist-read-private+playlist-read-collaborative+user-read-private+' \
              f'user-read-playback-state&' \
              f'show_dialog=True'

        embed = discord.Embed(colour=ctx.colour, title='Spotify authorisation link:',
                              description=f'Please click [this link]({url}) to authorise this discord account with your spotify account. Do not share this link with anyone as '
                                          f'it will allow people to link their spotify with your account.')

        try:
            await ctx.author.send(embed=embed)
            await ctx.send('Sent you a DM!')
        except discord.Forbidden:
            raise exceptions.VoiceError('I am unable to send direct messages to you, please enable them so that I can DM you your spotify authorisation link.')

    @commands.group(name='radio', aliases=['r'], invoke_without_command=True)
    async def radio(self, ctx: context.Context) -> None:
        await ctx.send('hi yes radio time :pog:')

    @radio.command(name='start')
    async def radio_start(self, ctx: context.Context) -> None:

        if not ctx.voice_client or not ctx.voice_client.is_connected:
            await ctx.invoke(self.bot.cogs['Music'].join)

        channel = getattr(ctx.author.voice, 'channel', None)
        if not channel or channel.id != ctx.voice_client.channel.id:
            raise exceptions.VoiceError(f'You must be connected to the same voice channel as me to use this command.')



def setup(bot: SemiBotomatic):
    bot.add_cog(Radio(bot=bot))
