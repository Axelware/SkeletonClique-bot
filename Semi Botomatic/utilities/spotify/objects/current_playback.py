from typing import Dict, Literal, Optional

from utilities.spotify import objects


class Context:

    __slots__ = 'data', 'external_urls', 'href', 'type', 'uri'

    def __init__(self, data: dict) -> None:
        self.data = data

        self.external_urls: Dict[Optional[str], Optional[str]] = data.get('external_urls', {})
        self.href: str = data.get('href')
        self.type: str = data.get('type')
        self.uri: str = data.get('uri')

    def __repr__(self) -> str:
        return f'<spotify.Context uri=\'{self.uri}\''

    @property
    def url(self) -> Optional[str]:
        return self.external_urls.get('spotify', None)


class Disallows:

    __slots__ = 'data', 'interrupting_playback', 'pausing', 'resuming', 'seeking', 'skipping_next', 'skipping_previous', 'toggling_repeat_context', 'toggling_repeat_track', \
                'toggling_shuffle', 'transferring_playback'

    def __init__(self, data: dict) -> None:
        self.data = data

        self.interrupting_playback: bool = data.get('interrupting_playback', False)
        self.pausing: bool = data.get('pausing', False)
        self.resuming: bool = data.get('resuming', False)
        self.seeking: bool = data.get('seeking', False)
        self.skipping_next: bool = data.get('skipping_next', False)
        self.skipping_previous: bool = data.get('skipping_prev', False)
        self.toggling_repeat_context: bool = data.get('toggling_repeat_context', False)
        self.toggling_repeat_track: bool = data.get('toggling_repeat_track', False)
        self.toggling_shuffle: bool = data.get('toggling_shuffle', False)
        self.transferring_playback: bool = data.get('transferring_playback', False)

    def __repr__(self) -> str:
        return '<spotify.Disallows>'


class Device:

    __slots__ = 'data', 'id', 'is_active', 'is_private_session', 'is_restricted', 'name', 'type', 'volume_percent'

    def __init__(self, data: dict) -> None:
        self.data = data

        self.id: int = data.get('id', 0)
        self.is_active: bool = data.get('is_active', False)
        self.is_private_session: bool = data.get('is_private_session', False)
        self.is_restricted: bool = data.get('is_restricted', False)
        self.name: str = data.get('name', 'unknown')
        self.type: str = data.get('type', 'unknown')
        self.volume_percent: int = data.get('volume_percent', 100)

    def __repr__(self) -> str:
        return f'<spotify.Device id=\'{self.id}\' name=\'{self.name}\'>'


class CurrentlyPlaying:

    __slots__ = 'data', 'context', 'item', 'currently_playing_type', 'is_playing', 'progress', 'timestamp'

    def __init__(self, data: dict) -> None:
        self.data = data

        context = data.get('context')
        self.context: Optional[Context] = Context(context) if context else None

        item = data.get('item')
        self.item: Optional[objects.Track] = objects.Track(item) if item else None

        self.currently_playing_type: Literal['track', 'episode', 'ad', 'unknown'] = data.get('currently_playing_type', 'unknown')
        self.is_playing: bool = data.get('is_playing', True)

        self.progress: int = data.get('progress', 0)
        self.timestamp: int = data.get('timestamp', 0)

    def __repr__(self) -> str:
        return f'<spotify.CurrentlyPlaying item={self.item!r} is_playing={self.is_playing}>'


class CurrentlyPlayingContext(CurrentlyPlaying):

    __slots__ = 'actions', 'device', 'repeat_state', 'shuffle_state'

    def __init__(self, data: dict) -> None:
        super().__init__(data)

        actions = data.get('actions', {}).get('disallows')
        self.actions: Optional[Disallows] = Disallows(actions) if actions else None

        device = data.get('device')
        self.device: Optional[Device] = Device(device) if device else None

        self.repeat_state: Literal['off', 'track', 'context', 'unknown'] = data.get('repeat_state', 'unknown')
        self.shuffle_state: bool = data.get('shuffle_state', False)

    def __repr__(self) -> str:
        return f'<spotify.CurrentlyPlayingContext item={self.item!r} device={self.device} is_playing={self.is_playing}>'
