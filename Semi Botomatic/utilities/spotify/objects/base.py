
class BaseObject:

    __slots__ = 'data', 'href', 'id', 'name', 'type', 'uri'

    def __init__(self, data: dict) -> None:
        self.data = data

        self.href = data.get('href')
        self.id = data.get('id')
        self.name = data.get('name')
        self.type = data.get('type')
        self.uri = data.get('uri')

    def __repr__(self) -> str:
        return f'<spotify.BaseObject id=\'{self.id}\' name=\'{self.name}\'>'

    def __str__(self) -> str:
        return self.name


class PagingObject:

    __slots__ = 'data', 'href', 'items', 'limit', 'next', 'offset', 'previous', 'total'

    def __init__(self, data: dict) -> None:
        self.data = data

        self.href = data.get('href')
        self.items = data.get('items')
        self.limit = data.get('limit')
        self.next = data.get('next')
        self.offset = data.get('offset')
        self.previous = data.get('previous')
        self.total = data.get('total')

    def __repr__(self) -> str:
        return f'<spotify.PagingObject total={self.total} offset={self.offset} limit={self.limit}>'
