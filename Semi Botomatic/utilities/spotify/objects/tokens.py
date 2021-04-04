from __future__ import annotations

import time
from typing import List, TYPE_CHECKING

from utilities.spotify import exceptions

if TYPE_CHECKING:
    from utilities.spotify.client import Client

TOKEN_URL = 'https://accounts.spotify.com/api/token'


class AppAuthToken:

    __slots__ = 'access_token', 'token_type', 'expires_in', 'scope', '_time_last_authorized'

    def __init__(self, *, access_token: str, token_type: str, expires_in: int, scope: str = None) -> None:

        self.access_token: str = access_token
        self.token_type: str = token_type
        self.expires_in: int = expires_in
        self.scope: str = scope

        self._time_last_authorized = time.time()

    def __repr__(self) -> str:
        return f'<spotify.AppAuthToken token_type=\'{self.token_type}\' expires_in=\'{self.expires_in}\'>'

    @property
    def has_expired(self) -> bool:
        return (time.time() - self._time_last_authorized) >= self.expires_in

    @classmethod
    async def create(cls, *, client: Client) -> AppAuthToken:

        request_data = {
            'grant_type':    'client_credentials',

            'client_id':     client.client_id,
            'client_secret': client.client_secret
        }

        async with client.bot.session.post(TOKEN_URL, data=request_data) as post:
            data = await post.json()

            if (error := data.get('error')) is not None:
                raise exceptions.AuthentificationError(f'Error while initially requesting application application access tokens: {error}')

        return cls(**data)

    async def refresh(self, *, client: Client) -> None:

        data = {
            'grant_type':    'client_credentials',

            'client_id':     client.client_id,
            'client_secret': client.client_secret
        }

        async with client.bot.session.post(TOKEN_URL, data=data) as post:
            data = await post.json()

            if (error := data.get('error')) is not None:
                raise exceptions.AuthentificationError(f'Error while refreshing application application access tokens: {error}')

        self.access_token = data.get('access_token')
        self.token_type = data.get('token_type')
        self.expires_in = data.get('expires_in')

        self._time_last_authorized = time.time()


class UserAuthToken:

    __slots__ = 'access_token', 'token_type', 'expires_in', 'scopes', 'refresh_token', '_time_last_authorized'

    def __init__(self, *, access_token: str, token_type: str, expires_in: int, scope: str, refresh_token: str = None) -> None:

        self.access_token: str = access_token
        self.token_type: str = token_type
        self.scopes: List[str] = scope.split(' ')
        self.expires_in: int = expires_in
        self.refresh_token: str = refresh_token

        self._time_last_authorized = time.time()

    def __repr__(self) -> str:
        return f'<spotify.UserAuthToken token_type=\'{self.token_type}\' expires_in=\'{self.expires_in}\'>'

    @property
    def has_expired(self) -> bool:
        return (time.time() - self._time_last_authorized) >= self.expires_in

    async def refresh(self, client: Client) -> None:

        request_data = {
            'grant_type':   'refresh_token',
            'refresh_token': self.refresh_token,

            'client_id':     client.client_id,
            'client_secret': client.client_secret
        }

        async with client.bot.session.post(TOKEN_URL, data=request_data) as post:
            data = await post.json()

            if (error := data.get('error')) is not None:
                raise exceptions.AuthentificationError(f'Error while refreshing user access token: {error}')

        self.access_token = data.get('access_token')
        self.token_type = data.get('token_type')
        self.scopes = data.get('scope', '').split(' ')
        self.expires_in = data.get('expires_in')
        self.refresh_token = data.get('refresh_token')

        self._time_last_authorized = time.time()

    @classmethod
    async def create_from_refresh_token(cls, client: Client, refresh_token: str) -> UserAuthToken:

        request_data = {
            'grant_type':   'refresh_token',
            'refresh_token': refresh_token,

            'client_id':     client.client_id,
            'client_secret': client.client_secret
        }

        async with client.bot.session.post(TOKEN_URL, data=request_data) as post:
            data = await post.json()

            if (error := data.get('error')) is not None:
                raise exceptions.AuthentificationError(f'Error while refreshing user access token: {error}')

        return cls(**data)