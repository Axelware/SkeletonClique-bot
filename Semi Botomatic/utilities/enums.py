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
