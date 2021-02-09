from typing import Dict, List, Mapping, Optional, Type, Union

from bot import SemiBotomatic
from utilities.spotify import exceptions, objects

BASE_ENDPOINT: str
EXCEPTIONS: Mapping[int, Type[exceptions.SpotifyException]]
SCOPES: List[str]


class Client:

    bot: SemiBotomatic = ...
    client_id: str = ...
    client_secret: str = ...
    app_auth_token: Optional[objects.AppAuthToken] = ...
    user_auth_tokens: Dict[int, objects.UserAuthToken] = ...
    user_auth_states: Dict[str, int] = ...

    def __init__(self, bot: SemiBotomatic) -> None: ...
    def __repr__(self) -> str: ...

    async def _get_auth_token(self, auth_token: int = None) -> Union[objects.AppAuthToken, objects.UserAuthToken]: ...
    async def _request(self, request: objects.Request, auth_token: int = None, *, parameters=None) -> Dict: ...

    # SEARCH API

    async def search(self, query: str, _type: List[objects.SearchType] = None, market: str = None, limit: int = 50, offset: int = 0, include_external: bool = False, auth_token: int = None) -> objects.SearchResult: ...

    # BROWSE API

    async def get_new_releases(self): ...
    async def get_featured_playlists(self): ...
    async def get_all_categories(self): ...
    async def get_category(self): ...
    async def get_category_playlist(self): ...
    async def get_recommendations(self, seed: objects.Seed, *, limit: int = 50, market: str = None, auth_token: int = None) -> objects.Recommendation: ...
    async def get_recommendation_genres(self, *, auth_token: int = None) -> List[str]: ...

    # ARTISTS API

    async def get_artists(self, artist_ids: List[str], *, market: str = None, auth_token: int = None) -> Dict[str, objects.Artist]: ...
    async def get_artist(self, artist_id: str, *, market: str = None, auth_token: int = None) -> objects.Artist: ...
    async def get_artists_top_tracks(self, artist_id: str, *, market: str = None, auth_token: str = None) -> List[objects.Track]: ...
    async def get_related_artists(self, artist_id: str, *, market: str = None, auth_token: int = None) -> List[objects.Artist]: ...
    async def get_artist_albums(self, artist_id: str, *, market: str = None, include_groups: List[objects.IncludeGroups] = None, limit: int = 50, offset: int = 0, auth_token: int = None) -> List[objects.SimpleAlbum]: ...
    async def get_all_artist_albums(self, artist_id: str, *, market: str = None, include_groups: List[objects.IncludeGroups] = None, auth_token: int = None) -> List[objects.SimpleAlbum]: ...

    # PLAYER API

    ...

    # ALBUMS API

    async def get_albums(self, album_ids: List[str], *, market: str = None, auth_token: int = None) -> Dict[str, objects.album.Album]: ...
    async def get_album(self, album_id: str, *, market: str = None, auth_token: int = None) -> objects.album.Album: ...
    async def get_full_album(self, album_id: str, *, market: str = None, auth_token: int = None) -> objects.album.Album: ...
    async def get_album_tracks(self, album_id: str, *, market: str = None, limit: int = 50, offset: int = 0, auth_token: int = None) -> List[objects.track.SimpleTrack]: ...
    async def get_all_album_tracks(self, album_id: str, *, market: str = None, auth_token: int = None) -> List[objects.track.SimpleTrack]: ...

    # TRACKS API

    async def get_tracks(self, track_ids: List[str], *, market: str = None, auth_token: int = None) -> Dict[str, objects.Track]: ...
    async def get_track(self, track_id: str, *, market: str = None, auth_token: int = None) -> objects.Track: ...
    async def get_tracks_audio_features(self, track_ids: List[str], auth_token: int = None) -> Dict[str, objects.AudioFeatures]: ...
    async def get_track_audio_features(self, track_id: str, auth_token: int = None) -> objects.AudioFeatures: ...

    #