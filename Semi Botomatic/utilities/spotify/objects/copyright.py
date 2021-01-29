from typing import Optional

from utilities.spotify import objects


class Copyright:

    __slots__ = 'data', 'text', 'type'

    def __init__(self, data: dict) -> None:
        self.data = data

        self.text: Optional[str] = data.get('text')
        self.type: objects.CopyrightType = objects.CopyrightType(data.get('type', 'C'))

    def __repr__(self) -> str:
        return f'<spotify.Copyright type={self.type!r}>'
