from __future__ import annotations

import json
import math
from typing import Dict, Literal, Optional, TYPE_CHECKING, Union, List
from urllib.parse import quote

import discord

import config
from utilities.spotify import exceptions, objects

if TYPE_CHECKING:
    from bot import SemiBotomatic

BASE_ENDPOINT = 'https://api.spotify.com/v1'

EXCEPTIONS = {
    400: exceptions.BadRequest,
    401: exceptions.Unauthorized,
    403: exceptions.Forbidden,
    404: exceptions.NotFound,
    429: exceptions.TooManyRequests,
    500: exceptions.InternalServerError,
    502: exceptions.BadGatewayError,
    503: exceptions.ServiceUnavailable
}

SCOPES = [
    'ugc-image-upload',

    'user-read-recently-player'
    'user-top-read',
    'user-read-playback-position',

    'user-read-playback-state',
    'user-modify-playback-state',
    'user-read-currently-playing',

    'app-remote-control',
    'streaming',

    'playlist-modify-public',
    'playlist-modify-private',
    'playlist-read-private',
    'playlist-read-collaborative',

    'user-follow-modify',
    'user-follow-read',

    'user-library-modify',
    'user-library-read',

    'user-read-email',
    'user-read-private',
]


class Request:

    def __init__(self, method: Literal['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'PATCH'], route: str, **params):

        self.method = method
        self.params = params

        self.url = BASE_ENDPOINT + route
        if params:
            self.url = self.url.format(**{key: quote(value) if isinstance(value, str) else value for key, value in params.items()})


class Client:

    def __init__(self, bot: SemiBotomatic) -> None:

        self.bot = bot
        self.client_id = config.SPOTIFY_CLIENT_ID
        self.client_secret = config.SPOTIFY_CLIENT_SECRET

        self.app_auth_token: Optional[objects.tokens.AppAuthToken] = None

        self.user_auth_tokens: Dict[int, objects.tokens.UserAuthToken] = {}
        self.user_auth_states: Dict[str, int] = {}

    def __repr__(self) -> str:
        return f'<spotify.Client bot={self.bot}>'

    #

    async def _request(
            self, request: Request, auth_token: Union[objects.tokens.AppAuthToken, objects.tokens.UserAuthToken, discord.User, discord.Member, int] = None, *, params=None
    ):

        if not auth_token:  # If an AuthToken was not provided, we'll use the app AuthToken.

            if not self.app_auth_token:
                self.app_auth_token = await objects.tokens.AppAuthToken.create(client=self)
            auth_token = self.app_auth_token

        else:

            if isinstance(auth_token, int):  # If the AuthToken was an int, try and fetch a user with the id.
                if (auth_token := self.bot.get_user(auth_token)) is None:
                    raise exceptions.SpotifyException(f'User with id \'{auth_token}\' was not found.')

            if isinstance(auth_token, (discord.User, discord.Member)):  # If the AuthToken is now a user or a member, fetch their refresh_token and create an object from it.

                user_config = self.bot.user_manager.get_user_config(user_id=auth_token.id)
                if user_config.spotify_refresh_token is None:
                    raise exceptions.SpotifyException(f'User with id \'{auth_token.id}\' has not linked spotify account.')

                auth_token = await objects.tokens.UserAuthToken.create_from_refresh_token(client=self, refresh_token=user_config.spotify_refresh_token)

        if auth_token.has_expired:  # By this point we either have an AppAuthToken or a UserAuthToken, so we should check if they need refreshing.
            await auth_token.refresh(client=self)

        headers = {
            'Content-Type':  f'application/json',
            'Authorization': f'Bearer {auth_token.access_token}'
        }

        async with self.bot.session.request(request.method, request.url, headers=headers, params=params) as request:

            if request.headers['Content-Type'] == 'application/json; charset=utf-8':
                data = await request.json()
            else:
                data = await request.text()

            print(json.dumps(data, indent=4))

            if 200 <= request.status < 300:
                return data

            if error := data.get('error'):
                raise EXCEPTIONS.get(error.get('status'))(error)

    #

    async def get_albums(self, album_ids: List[str], market: str = None) -> Dict[str, objects.album.Album]:

        if len(album_ids) > 20:
            raise exceptions.TooManyIDs('\'get_albums\' can only take a maximum of 20 album ids.')

        params = {'ids': ','.join(album_ids)}
        if market:
            params['market'] = market

        response = await self._request(Request('GET', '/albums'), params=params)

        albums = [album or objects.album.Album(album) for album in response.get('albums')]
        return {album_id: album for album_id, album in zip(album_ids, albums)}

    async def get_album(self, album_id: str, market: str = None) -> objects.album.Album:

        response = await self._request(Request('GET', '/albums/{album_id}', album_id=album_id, params={'market': market} if market else None))
        return objects.album.Album(response)

    async def get_album_tracks(self, album: Union[str, objects.album.Album, objects.album.SimpleAlbum], market: str = None, limit: int = None, offset: int = None):

        if isinstance(album, str):
            album = await self.get_album(album_id=album, market=market)

        params = {}
        if market:
            params['market'] = market
        if not limit:
            params['limit'] = 50

        if not offset or not limit:  # Fetch all the album's tracks.

            if isinstance(album, objects.album.SimpleAlbum):

                first50 = await self._request(Request('GET', '/albums/{album_id}/tracks', album_id=album.id, params=params))


                for i in range(math.ceil(album.total_tracks // 50)):
                    params['offset'] = i * 50

                    response = await self._request(Request('GET', '/albums/{album_id}/tracks', album_id=album.id, params=params))
                    tracks.extend([objects.track.SimpleTrack(track_data) for track_data in objects.base.PagingObject(response).items])



        if limit:
            params['limit'] = limit
        if offset:
            params['offset'] = offset



        response = await self._request(Request('GET', '/albums/{album_id}/tracks', album_id=album_id, params={'market': market} if market else None))






    async def get_artist(self, artist_id: str) -> objects.artist.Artist:
        request = await self._request(Request('GET', '/artists/{artist_id}', artist_id=artist_id))
        return objects.artist.Artist(request)

    async def get_track(self, track_id: str) -> objects.track.Track:
        request = await self._request(Request('GET', '/tracks/{track_id}', track_id=track_id))
        return objects.track.Track(request)

    async def get_playlist(self, playlist_id: str) -> objects.playlist.Playlist:
        request = await self._request(Request('GET', '/playlists/{playlist_id}', playlist_id=playlist_id))
        return objects.playlist.Playlist(request)

    #

    async def recommendations(self, *, limit: int = 5, **p):

        params = dict(limit=limit)

        # TODO: Limit seeds to a total of 5
        valid_seeds = {"seed_artists", "seed_genres", "seed_tracks"}
        for seed in valid_seeds:
            if values := p.get(seed):
                params[seed] = ",".join(values)

        r = await self._request(Request("GET", "recommendations"), params=params)
        return objects.Recommendations(r)