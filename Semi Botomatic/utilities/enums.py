import enum


class Operation(enum.Enum):

    SET = 'set'
    UPDATE = SET

    RESET = 'reset'

    ADD = 'add'
    PLUS = ADD

    MINUS = 'remove'
    REMOVE = MINUS


class Updateable(enum.Enum):

    COINS = 'coins'
    XP = 'xp'

    DAILY_COLLECTED = 'daily_collected'
    WEEKLY_COLLECTED = 'weekly_collected'
    MONTHLY_COLLECTED = 'monthly_collected'

    DAILY_STREAK = 'daily_streak'
    WEEKLY_STREAK = 'weekly_streak'
    MONTHLY_STREAK = 'monthly_streak'


class EmbedSize(enum.Enum):

    LARGE = 0
    MEDIUM = 1
    SMALL = 2


class ReminderRepeat(enum.Enum):

    NEVER = 0

    EVERY_HOUR = 1
    EVERY_DAY = 2
    EVERY_WEEK = 3
    EVERY_MONTH = 4
    EVERY_YEAR = 5

    EVERY_OTHER_HOUR = 6
    EVERY_OTHER_DAY = 7
    EVERY_OTHER_WEEK = 8
    EVERY_OTHER_MONTH = 9
    EVERY_OTHER_YEAR = 10

    EVERY_HALF_HOUR = 11
    EVERY_HALF_DAY = 12
    EVERY_HALF_MONTH = 13
    EVERY_HALF_YEAR = 14
