import enum


class Operations(enum.Enum):

    set = 'set'
    update = 'set'

    reset = 'reset'
    clear = 'reset'

    add = 'add'

    remove = 'remove'
    minus = 'remove'


class Editables(enum.Enum):

    timezone = 'timezone'
    timezone_private = 'timezone_private'

    birthday = 'birthday'
    birthday_private = 'birthday_private'

    spotify_refresh_token = 'spotify_refresh_token'


class EmbedSize(enum.Enum):

    LARGE = 0
    MEDIUM = 1
    SMALL = 2
