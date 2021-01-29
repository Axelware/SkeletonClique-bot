from typing import Optional


class Image:

    __slots__ = 'data', 'url', 'width', 'height'

    def __init__(self, data: dict) -> None:
        self.data = data

        self.url: str = data.get('url')
        self.width: Optional[int] = data.get('width', None)
        self.height: Optional[int] = data.get('height', None)

    def __repr__(self) -> str:
        return f'<spotify.Image url=\'<{self.url}>\' width=\'{self.width}\' height=\'{self.height}\'>'

    def __str__(self) -> str:
        return self.url
