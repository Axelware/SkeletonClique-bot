from typing import Optional, Literal


class Copyright:

    def __init__(self, data: dict) -> None:
        self.data = data

        self.text: Optional[str] = data.get('text', None)
        self.type: Optional[Literal['C', 'P']] = data.get('type', None)

    def __repr__(self) -> str:
        return f'<spotify.Copyright type={self.type}>'
