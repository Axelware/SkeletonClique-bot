class SpotifyException(Exception):
    pass


class AuthentificationError(SpotifyException):
    pass


class TooManyIDs(SpotifyException):
    pass


class SpotifyRequestError(SpotifyException):

    def __init__(self, data: dict) -> None:
        super().__init__(data)

        self.data = data


class BadRequest(SpotifyRequestError):

    def __init__(self, data: dict) -> None:
        super().__init__(data)

        self.data = data


class Unauthorized(SpotifyRequestError):

    def __init__(self, data: dict) -> None:
        super().__init__(data)

        self.data = data


class Forbidden(SpotifyRequestError):

    def __init__(self, data: dict) -> None:
        super().__init__(data)

        self.data = data


class NotFound(SpotifyRequestError):

    def __init__(self, data: dict) -> None:
        super().__init__(data)

        self.data = data


class TooManyRequests(SpotifyRequestError):

    def __init__(self, data: dict) -> None:
        super().__init__(data)

        self.data = data


class InternalServerError(SpotifyRequestError):

    def __init__(self, data: dict) -> None:
        super().__init__(data)

        self.data = data


class BadGatewayError(SpotifyRequestError):

    def __init__(self, data: dict) -> None:
        super().__init__(data)

        self.data = data


class ServiceUnavailable(SpotifyRequestError):

    def __init__(self, data: dict) -> None:
        super().__init__(data)

        self.data = data
