

class PagingObject:

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
        return '<spotify.PagingObject>'


class BaseObject:

    def __init__(self, data: dict) -> None:

        self.data = data

        self.href: str = data.get('href')
        self.id: str = data.get('id')
        self.name: str = data.get('name')
        self.type: str = data.get('type')
        self.uri: str = data.get('uri')

    def __str__(self) -> str:
        return self.name
