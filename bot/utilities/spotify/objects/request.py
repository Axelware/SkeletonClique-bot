from urllib.parse import quote

BASE_ENDPOINT = 'https://api.spotify.com/v1'


class Request:

    __slots__ = 'method', 'route', 'parameters', 'url'

    def __init__(self, method, route, **parameters):

        self.method = method
        self.route = route
        self.parameters = parameters

        self.url = BASE_ENDPOINT + route
        if parameters:
            self.url = self.url.format(**{key: quote(value) if isinstance(value, str) else value for key, value in parameters.items()})

    def __repr__(self) -> str:
        return f'<spotify.Request method=\'{self.method}\' url=\'{self.url}\'>'
