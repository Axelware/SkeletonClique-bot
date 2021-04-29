import asyncio
import math
from typing import Optional

import pendulum
from pendulum.datetime import DateTime
from pendulum.tz.timezone import Timezone

from utilities import enums

__all__ = ['DefaultUserConfig', 'UserConfig', 'DefaultGuildConfig', 'GuildConfig', 'Reminder', 'Todo', 'Tag']


class DefaultUserConfig:

    __slots__ = 'data', 'id', 'created_at', 'timezone', 'timezone_private', 'birthday', 'birthday_private', 'blacklisted', 'blacklisted_reason', 'spotify_refresh_token', 'xp', \
                'coins', 'notifications', 'reminders', 'todos', 'requires_db_update'

    def __init__(self) -> None:
        self.data = None

        self.id: int = 0
        self.created_at: DateTime = pendulum.now(tz='UTC')

        self.timezone: Timezone = pendulum.timezone('UTC')
        self.timezone_private: bool = False

        self.birthday: DateTime = pendulum.DateTime(2020, 1, 1, tzinfo=pendulum.timezone('UTC'))
        self.birthday_private: bool = False

        self.blacklisted: bool = False
        self.blacklisted_reason: Optional[str] = None

        self.spotify_refresh_token: Optional[str] = None

        self.xp: int = 0
        self.coins: int = 0

        self.notifications: Notifications = Notifications(data={})

        self.reminders: dict[int, Reminder] = {}
        self.todos: dict[int, Todo] = {}

        self.requires_db_update: set = set()

    def __repr__(self) -> str:
        return f'<DefaultUserConfig id=\'{self.id}\'>'


class UserConfig:

    __slots__ = 'data', 'id', 'created_at', 'timezone', 'timezone_private', 'birthday', 'birthday_private', 'blacklisted', 'blacklisted_reason', 'spotify_refresh_token', 'xp', \
                'coins', 'notifications', 'reminders', 'todos', 'requires_db_update'

    def __init__(self, data: dict) -> None:
        self.data = data

        self.id: int = data.get('id')
        self.created_at: DateTime = pendulum.instance(data.get('created_at'), tz='UTC')

        self.timezone: Timezone = pendulum.timezone(data.get('timezone'))
        self.timezone_private: bool = data.get('timezone_private')

        self.birthday: DateTime = pendulum.parse(data.get('birthday').isoformat(), tz='UTC')
        self.birthday_private: bool = data.get('birthday_private')

        self.blacklisted: bool = data.get('blacklisted')
        self.blacklisted_reason: Optional[str] = data.get('blacklisted_reason')

        self.spotify_refresh_token: Optional[str] = data.get('spotify_refresh_token')

        self.xp: int = data.get('xp')
        self.coins: int = data.get('coins')

        self.notifications: Optional[Notifications] = None

        self.reminders: dict[int, Reminder] = {}
        self.todos: dict[int, Todo] = {}

        self.requires_db_update: set = set()

    def __repr__(self) -> str:
        return f'<UserConfig id=\'{self.id}\'>'

    @property
    def time(self) -> DateTime:
        return pendulum.now(tz=self.timezone)

    @property
    def age(self) -> int:
        return (pendulum.now(tz='UTC') - self.birthday).in_years()

    @property
    def next_birthday(self) -> pendulum.datetime:

        now = pendulum.now(tz='UTC')

        return now.replace(month=self.birthday.month, day=self.birthday.day + 1, hour=0, minute=0, second=0, microsecond=0) if now < self.birthday.add(years=self.age) else \
            now.replace(month=self.birthday.month, day=self.birthday.day + 1, year=self.birthday.year + self.age + 1, hour=0, minute=0, second=0, microsecond=0)

    @property
    def level(self) -> int:
        return math.floor((((self.xp / 100) ** (1.0 / 1.5)) / 3))

    @property
    def next_level_xp(self) -> int:
        return round((((((self.level + 1) * 3) ** 1.5) * 100) - self.xp))


class DefaultGuildConfig:

    __slots__ = 'data', 'id', 'created_at', 'embed_size'

    def __init__(self) -> None:
        self.data = None

        self.id: int = 0
        self.created_at: DateTime = pendulum.now(tz='UTC')

        self.embed_size: enums.EmbedSize = enums.EmbedSize(0)

    def __repr__(self) -> str:
        return f'<DefaultGuildConfig id=\'{self.id}\'>'


class GuildConfig:

    __slots__ = 'data', 'id', 'created_at', 'embed_size'

    def __init__(self, data: dict) -> None:
        self.data = data

        self.id: int = data.get('id')
        self.created_at: DateTime = pendulum.instance(data.get('created_at'), tz='UTC')

        self.embed_size = enums.EmbedSize(data.get('embed_size'))

    def __repr__(self) -> str:
        return f'<GuildConfig id=\'{self.id}\'>'


class Reminder:

    __slots__ = 'data', 'id', 'user_id', 'channel_id', 'created_at', 'datetime', 'content', 'jump_url', 'repeat_type', 'notified', 'task'

    def __init__(self, data: dict) -> None:
        self.data = data

        self.id: int = data.get('id')
        self.user_id: int = data.get('user_id')
        self.channel_id: int = data.get('channel_id')
        self.created_at: DateTime = pendulum.instance(data.get('created_at'), tz='UTC')
        self.datetime: DateTime = pendulum.instance(data.get('datetime'), tz='UTC')
        self.content: str = data.get('content')
        self.jump_url: str = data.get('jump_url')
        self.repeat_type: enums.ReminderRepeatType = enums.ReminderRepeatType(value=data.get('repeat_type'))
        self.notified: bool = data.get('notified')

        self.task: Optional[asyncio.Task] = None

    def __repr__(self) -> str:
        return f'<Reminder id=\'{self.id}\' user_id=\'{self.user_id}\' datetime={self.datetime} done={self.done}>'

    @property
    def done(self) -> bool:
        return pendulum.now(tz='UTC') > self.datetime


class Tag:

    __slots__ = 'data', 'id', 'user_id', 'guild_id', 'created_at', 'name', 'alias', 'content', 'jump_url'

    def __init__(self, data: dict) -> None:
        self.data = data

        self.id: int = data.get('id')
        self.user_id: int = data.get('user_id')
        self.guild_id: int = data.get('guild_id')
        self.created_at: DateTime = pendulum.instance(data.get('created_at'), tz='UTC')
        self.name: str = data.get('name')
        self.alias: Optional[str] = data.get('alias')
        self.content: str = data.get('content')
        self.jump_url: Optional[str] = data.get('jump_url')

    def __repr__(self) -> str:
        return f'<Tag id=\'{self.id}\' user_id=\'{self.user_id}\' guild_id=\'{self.guild_id}\' name=\'{self.name}\' alias=\'{self.alias}\'>'


class Todo:

    __slots__ = 'data', 'id', 'user_id', 'created_at', 'content', 'jump_url'

    def __init__(self, data: dict) -> None:
        self.data = data

        self.id: int = data.get('id')
        self.user_id: int = data.get('user_id')
        self.created_at: DateTime = pendulum.instance(data.get('created_at'), tz='UTC')
        self.content: str = data.get('content')
        self.jump_url: Optional[str] = data.get('jump_url')

    def __repr__(self) -> str:
        return f'<Todo id=\'{self.id}\' user_id=\'{self.user_id}\'>'


class Notifications:

    __slots__ = 'data', 'id', 'user_id', 'level_ups'

    def __init__(self, data: dict) -> None:
        self.data = data

        self.id: int = data.get('id')
        self.user_id: int = data.get('user_id')

        self.level_ups: bool = data.get('level_ups', True)

    def __repr__(self) -> str:
        return f'<Notifications id={self.id} user_id={self.user_id} level_ups={self.level_ups}>'
