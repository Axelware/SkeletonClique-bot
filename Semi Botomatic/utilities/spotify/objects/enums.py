import enum


class IncludeGroups(enum.Enum):
    album = 'album'
    single = 'single'
    appears_on = 'appears_on'
    compilation = 'compilation'

    all = 'album,single,appears_on,compilation'


class Key(enum.Enum):
    C = 0
    C_SHARP = 1
    D = 2
    D_SHARP = 3
    E = 4
    F = 5
    F_SHARP = 6
    G = 7
    G_SHARP = 8
    A = 9
    A_SHARP = 10
    B = 11


class Mode(enum.Enum):
    MAJOR = 1
    MINOR = 0
