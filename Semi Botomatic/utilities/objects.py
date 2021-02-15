import asyncio
from typing import Dict, Optional

import pendulum
from pendulum.datetime import DateTime
from pendulum.tz.timezone import Timezone


class DefaultUserConfig:

    __slots__ = 'id', 'created_at', 'timezone', 'timezone_private', 'birthday', 'birthday_private', 'blacklisted', 'blacklisted_reason', 'spotify_refresh_token', 'reminders', \
                'requires_db_update'

    def __init__(self) -> None:

        self.id: int = 0
        self.created_at: DateTime = pendulum.now(tz='UTC')

        self.timezone: Timezone = pendulum.timezone('UTC')
        self.timezone_private: bool = False

        self.birthday: DateTime = pendulum.DateTime(2020, 1, 1, tzinfo=pendulum.timezone('UTC'))
        self.birthday_private: bool = False

        self.blacklisted: bool = False
        self.blacklisted_reason: Optional[str] = None

        self.spotify_refresh_token: Optional[str] = None

        self.reminders: Dict[int, Reminder] = {}
        self.requires_db_update = []

    def __repr__(self) -> str:
        return f'<DefaultUserConfig id=\'{self.id}\'>'


class UserConfig:

    __slots__ = 'id', 'created_at', 'timezone', 'timezone_private', 'birthday', 'birthday_private', 'blacklisted', 'blacklisted_reason', 'spotify_refresh_token', 'reminders', \
                'requires_db_update'

    def __init__(self, data: dict) -> None:

        self.id: int = data.get('id')
        self.created_at: DateTime = pendulum.instance(data.get('created_at'), tz='UTC')

        self.timezone: Timezone = pendulum.timezone(data.get('timezone'))
        self.timezone_private: bool = data.get('timezone_private')

        self.birthday: DateTime = pendulum.parse(data.get('birthday').isoformat(), tz='UTC')
        self.birthday_private: bool = data.get('birthday_private')

        self.blacklisted: bool = data.get('blacklisted')
        self.blacklisted_reason: Optional[str] = data.get('blacklisted_reason')

        self.spotify_refresh_token: Optional[str] = data.get('spotify_refresh_token')

        self.reminders: Dict[int, Reminder] = {}
        self.requires_db_update = []

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
        return self.birthday.replace(year=self.birthday.year + self.age + 1)


class Reminder:

    __slots__ = 'id', 'user_id', 'created_at', 'datetime', 'content', 'jump_url', 'task'

    def __init__(self, data: dict) -> None:

        self.id: int = data.get('id')
        self.user_id: int = data.get('user_id')
        self.created_at: DateTime = pendulum.instance(data.get('created_at'), tz='UTC')
        self.datetime: DateTime = pendulum.instance(data.get('datetime'), tz='UTC')
        self.content: str = data.get('content')
        self.jump_url: str = data.get('jump_url')

        self.task: Optional[asyncio.Task] = None

    def __repr__(self) -> str:
        return f'<Reminder id=\'{self.id}\' user_id=\'{self.user_id}\' datetime={self.datetime} done={self.done}>'

    @property
    def done(self) -> bool:
        return pendulum.now(tz='UTC') > self.datetime


class Tag:

    __slots__ = 'id', 'user_id', 'guild_id', 'created_at', 'name', 'alias', 'content', 'jump_url'

    def __init__(self, data: dict) -> None:

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

    __slots__ = 'id', 'user_id', 'created_at', 'content', 'jump_url'

    def __init__(self, data: dict) -> None:

        self.id: int = data.get('id')
        self.user_id: int = data.get('user_id')
        self.created_at: DateTime = pendulum.instance(data.get('created_at'), tz='UTC')
        self.content: str = data.get('content')
        self.jump_url: Optional[str] = data.get('jump_url')

    def __repr__(self) -> str:
        return f'<Todo id=\'{self.id}\' user_id=\'{self.user_id}\'>'