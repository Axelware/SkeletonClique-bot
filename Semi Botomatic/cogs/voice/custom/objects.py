from typing import Union

import slate
import spotify


class SearchResult:

    __slots__ = 'source', 'search_type', 'search_result', 'tracks'

    def __init__(self, source: str, search_type: str, search_result: Union[spotify.Album, spotify.Playlist, spotify.Track, list[slate.Track], slate.Playlist],
                 tracks: list[slate.Track]) -> None:

        self.source = source
        self.search_type = search_type
        self.search_result = search_result
        self.tracks = tracks

    def __repr__(self) -> str:
        return f'<life.SearchResult source={self.source} search_type={self.search_type} search_result={self.search_result}>'
