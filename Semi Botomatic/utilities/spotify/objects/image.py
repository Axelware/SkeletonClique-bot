from typing import Optional


class Image:

    def __init__(self, data: dict) -> None:
        self.data = data

        self.url: Optional[str] = data.get('url', None)
        self.width: Optional[int] = data.get('width', None)
        self.height: Optional[int] = data.get('height', None)

    def __repr__(self) -> str:
        return f'<spotify.Image url=\'<{self.url}>\' width=\'{self.width}\' height=\'{self.height}\'>'

    def __str__(self):
        return self.url
