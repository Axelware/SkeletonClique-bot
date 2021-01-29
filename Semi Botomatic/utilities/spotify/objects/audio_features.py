from typing import Optional

from utilities.spotify import objects


class AudioFeatures:

    __slots__ = 'data', 'acousticness', 'analysis_url', 'danceability', 'duration_ms', 'energy', 'id', 'instrumentalness', 'key', 'liveness', 'loudness', 'mode', 'speechiness', \
                'tempo', 'time_signature', 'track_href', 'type', 'uri', 'valence'

    def __init__(self, data: dict) -> None:
        self.data = data

        self.acousticness: float = data.get('acousticness', 0)
        self.analysis_url: Optional[str] = data.get('analysis_url', None)
        self.danceability: float = data.get('danceability', 0)
        self.duration_ms: int = data.get('duration_ms', 0)
        self.energy: float = data.get('energy', 0)
        self.id: Optional[str] = data.get('id', None)
        self.instrumentalness: float = data.get('instrumentalness', 0)
        self.key: objects.Key = objects.Key(data.get('key', 0))
        self.liveness: float = data.get('liveness', 0)
        self.loudness: float = data.get('loudness', 0)
        self.mode: objects.Mode = objects.Mode(data.get('mode', 0))
        self.speechiness: float = data.get('speechiness', 0)
        self.tempo: float = data.get('tempo', 0)
        self.time_signature: int = data.get('time_signature', 0)
        self.track_href: Optional[str] = data.get('track_href', None)
        self.type: str = data.get('type', 'audio_features')
        self.uri: Optional[str] = data.get('uri', None)
        self.valence: float = data.get('valence', 0)

    def __repr__(self) -> str:
        return f'<spotify.AudioFeatures id=\'{self.id}\'>'
