from typing import Dict, List, Optional

from utilities.spotify.objects import base, followers, image, track, user


class SimplePlaylist(base.BaseObject):

    def __init__(self, data: dict) -> None:
        super().__init__(data)

        self.collaborative: bool = data.get('collaborative', False)
        self.description: Optional[str] = data.get('description', None)
        self.external_urls: Dict[Optional[str], Optional[str]] = data.get('external_urls', {})
        self.images: List[Optional[image.Image]] = [image.Image(image_data) for image_data in data.get('images', [])]
        self.owner: user.User = user.User(data.get('owner'))
        self.primary_colour: Optional[str] = data.get('primary_color', None)
        self.is_public: bool = data.get('public', False)
        self.snapshot_id: Optional[str] = data.get('snapshot_id', None)
        self.total_tracks: int = data.get('tracks', {}).get('total', 0)

    def __repr__(self) -> str:
        return f'<spotify.SimplePlaylist name=\'{self.name}\' id=\'{self.id}\' url=\'<{self.url}>\'>'

    @property
    def url(self) -> Optional[str]:
        return self.external_urls.get('spotify')


class Playlist(base.BaseObject):

    def __init__(self, data: dict) -> None:
        super().__init__(data)

        self.collaborative: bool = data.get('collaborative', False)
        self.description: Optional[str] = data.get('description', None)
        self.external_urls: Dict[Optional[str], Optional[str]] = data.get('external_urls', {})
        self.followers: followers.Followers = followers.Followers(data.get('followers'))
        self.images: List[Optional[image.Image]] = [image.Image(image_data) for image_data in data.get('images', [])]
        self.owner: user.User = user.User(data.get('owner'))
        self.primary_colour: Optional[str] = data.get('primary_color', None)
        self.is_public: bool = data.get('public', False)
        self.snapshot_id: Optional[str] = data.get('snapshot_id', None)
        self.total_tracks: int = data.get('tracks', {}).get('total', 0)
        self.tracks: List[Optional[track.PlaylistTrack]] = [track.PlaylistTrack(track_data) for track_data in base.PagingObject(data.get('tracks', [])).items]

    def __repr__(self) -> str:
        return f'<spotify.Playlist name=\'{self.name}\' id=\'{self.id}\' url=\'<{self.url}>\'>'

    @property
    def url(self) -> Optional[str]:
        return self.external_urls.get('spotify')

