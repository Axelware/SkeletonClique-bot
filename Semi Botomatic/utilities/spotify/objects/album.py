from typing import Dict, List, Literal, Optional

from utilities.spotify import objects


class AlbumRestriction:

    __slots__ = 'data', 'reason'

    def __init__(self, data: dict) -> None:
        self.data = data

        self.reason: Literal['market', 'product', 'explicit'] = data.get('reason')

    def __repr__(self) -> str:
        return f'<spotify.AlbumRestriction reason=\'{self.reason}\'>'


class SimpleAlbum(objects.BaseObject):

    __slots__ = 'album_type', 'artists', 'available_markets', 'external_urls', 'images', 'release_date', 'release_data_precision', 'total_tracks'

    def __init__(self, data: dict) -> None:
        super().__init__(data)

        self.album_type: Literal['album', 'single', 'compilation', 'unknown'] = data.get('album_type', 'unknown')
        self.artists: List[Optional[objects.SimpleArtist]] = [objects.SimpleArtist(artist_data) for artist_data in data.get('artists', [])]
        self.available_markets: List[Optional[str]] = data.get('available_markets', [])
        self.external_urls: Dict[Optional[str], Optional[str]] = data.get('external_urls', {})
        self.images: List[Optional[objects.Image]] = [objects.Image(image_data) for image_data in data.get('images', [])]
        self.release_date: Optional[str] = data.get('release_date', None)
        self.release_data_precision: Literal['year', 'month', 'day', 'unknown'] = data.get('release_date_precision', 'unknown')
        self.total_tracks: int = data.get('total_tracks', 0)

    def __repr__(self) -> str:
        return f'<spotify.SimpleAlbum name=\'{self.name}\' id=\'{self.id}\' url=\'<{self.url}>\' total_tracks=\'{self.total_tracks}\'>'

    @property
    def url(self) -> Optional[str]:
        return self.external_urls.get('spotify')

    @property
    def restriction(self) -> Optional[AlbumRestriction]:
        if (restriction_data := self.data.get('restrictions')) is None:
            return None
        return AlbumRestriction(restriction_data)


class Album(objects.BaseObject):

    __slots__ = 'album_type', 'artists', 'available_markets', 'copyrights', 'external_ids', 'external_urls', 'genres', 'images', 'label', 'popularity', 'release_date', \
                'release_data_precision', 'total_tracks', '_tracks_paging', 'tracks'

    def __init__(self, data: dict) -> None:
        super().__init__(data)

        self.album_type: Literal['album', 'single', 'compilation', 'unknown'] = data.get('album_type', 'unknown')
        self.artists: List[Optional[objects.SimpleArtist]] = [objects.SimpleArtist(artist_data) for artist_data in data.get('artists', [])]
        self.available_markets: List[Optional[str]] = data.get('available_markets', [])
        self.copyrights: List[Optional[objects.Copyright]] = [objects.Copyright(copyright_data) for copyright_data in data.get('copyrights', {})]
        self.external_ids: Dict[Optional[str], Optional[str]] = data.get('external_ids', {})
        self.external_urls: Dict[Optional[str], Optional[str]] = data.get('external_urls', {})
        self.genres: List[Optional[str]] = data.get('genres', [])
        self.images: List[Optional[objects.Image]] = [objects.Image(image_data) for image_data in data.get('images', [])]
        self.label: Optional[str] = data.get('label', None)
        self.popularity: int = data.get('popularity', 0)
        self.release_date: Optional[str] = data.get('release_date', None)
        self.release_data_precision: Literal['year', 'month', 'day', 'unknown'] = data.get('release_date_precision', 'unknown')
        self.total_tracks: int = data.get('total_tracks', 0)

        self._tracks_paging = objects.PagingObject(data.get('tracks', []))
        self.tracks: List[Optional[objects.SimpleTrack]] = [objects.SimpleTrack(track_data) for track_data in self._tracks_paging.items]

    def __repr__(self) -> str:
        return f'<spotify.Album name=\'{self.name}\' id=\'{self.id}\' url=\'<{self.url}>\' total_tracks=\'{self.total_tracks}\'>'

    @property
    def url(self) -> Optional[str]:
        return self.external_urls.get('spotify')