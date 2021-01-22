from __future__ import annotations

from typing import TYPE_CHECKING

import aiohttp.web

import config
from utilities.enums import Editables, Operations
from utilities.spotify import exceptions, objects

if TYPE_CHECKING:
    from bot import SemiBotomatic


class Spotify:

    async def get(self, request: aiohttp.web.Request):

        bot: SemiBotomatic = request.app.bot

        if (state := request.query.get('state')) is None:
            return aiohttp.web.json_response({'error': 'state parameter not found.'}, status=401)

        if (user := bot.get_user(bot.spotify.user_auth_states.get(state))) is None:
            return aiohttp.web.json_response({'error': 'user matching state parameter not found.'}, status=401)

        #

        if (error := request.query.get('error')) is not None:
            await user.send(f'Something went wrong while connecting your spotify account, please try again.')
            return aiohttp.web.json_response({'error': error}, status=401)

        elif (code := request.query.get('code')) is not None:

            data = {
                'grant_type':   'authorization_code',
                'code':         code,
                'redirect_uri': f'http://{config.WEB_URL}/api/spotify/callback',

                'client_id':     config.SPOTIFY_CLIENT_ID,
                'client_secret': config.SPOTIFY_CLIENT_SECRET
            }

            async with request.app.session.post('https://accounts.spotify.com/api/token', data=data) as post:

                data = await post.json()

                if (error := data.get('error')) is not None:
                    raise exceptions.AuthentificationError(f'Error while requesting user access/refresh tokens: {error}')

            await bot.user_manager.edit_user_config(user_id=user.id, editable=Editables.spotify_refresh_token, operation=Operations.set, value=data.get('refresh_token'))

            bot.spotify.user_auth_tokens[user.id] = objects.tokens.UserAuthToken(**data)
            del bot.spotify.user_auth_states[state]

            await user.send(f'Your spotify account was successfully linked.')
            return aiohttp.web.Response(body='Spotify account link was successful, you can close this page now.')

        return aiohttp.web.Response(status=500)


def setup(app: aiohttp.web.Application) -> None:

    spotify = Spotify()

    app.add_routes([
        aiohttp.web.get(r'/api/spotify/callback', spotify.get),
    ])
