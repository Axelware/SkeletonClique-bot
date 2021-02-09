class SpotifyException(Exception):
    pass


class AuthentificationError(SpotifyException):
    pass


class TooManyIDs(SpotifyException):
    pass


class SpotifyRequestError(SpotifyException):

    def __init__(self, error: dict) -> None:

        self.status = error.get('status')
        self.message = error.get('message')


class BadRequest(SpotifyRequestError):

    def __init__(self, data: dict) -> None:
        super().__init__(data)


class Unauthorized(SpotifyRequestError):

    def __init__(self, data: dict) -> None:
        super().__init__(data)


class Forbidden(SpotifyRequestError):

    def __init__(self, data: dict) -> None:
        super().__init__(data)


class NotFound(SpotifyRequestError):

    def __init__(self, data: dict) -> None:
        super().__init__(data)


class TooManyRequests(SpotifyRequestError):

    def __init__(self, data: dict) -> None:
        super().__init__(data)


class InternalServerError(SpotifyRequestError):

    def __init__(self, data: dict) -> None:
        super().__init__(data)


class BadGatewayError(SpotifyRequestError):

    def __init__(self, data: dict) -> None:
        super().__init__(data)


class ServiceUnavailable(SpotifyRequestError):

    def __init__(self, data: dict) -> None:
        super().__init__(data)
