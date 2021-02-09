import datetime as dt
from typing import List, Optional

import pendulum
from pendulum.datetime import DateTime
from pendulum.tz.timezone import Timezone


class DefaultUserConfig:

    __slots__ = 'id', 'created_at', 'timezone', 'timezone_private', 'birthday', 'birthday_private', 'reminders', 'requires_db_update', 'spotify_refresh_token'

    def __init__(self) -> None:

        self.id: int = 0

        self.timezone: Timezone = pendulum.timezone('UTC')
        self.timezone_private: bool = False
        
        self.birthday: DateTime = pendulum.DateTime(2020, 1, 1, 0, 0, 0, tzinfo=pendulum.timezone('UTC'))
        self.birthday_private: bool = False

        self.spotify_refresh_token: Optional[str] = None

        self.reminders = []
        self.requires_db_update = []

        self.created_at: DateTime = pendulum.now(tz='UTC')

    def __repr__(self) -> str:
        return f'<DefaultUserConfig id=\'{self.id}\'>'

    @property
    def time(self) -> DateTime:
        return pendulum.now(tz=self.timezone)

    @property
    def age(self) -> int:
        return (pendulum.now(tz='UTC') - self.birthday).in_years()

    @property
    def next_birthday(self) -> pendulum.datetime:
        return self.birthday.replace(year=self.birthday.year + self.age + 1)


class UserConfig:

    __slots__ = 'id', 'created_at', 'timezone', 'timezone_private', 'birthday', 'birthday_private', 'reminders', 'requires_db_update', 'spotify_refresh_token'

    def __init__(self, data: dict) -> None:

        self.id: int = data.get('id', 0)

        self.timezone: Timezone = pendulum.timezone(data.get('timezone', 'UTC'))
        self.timezone_private: bool = data.get('timezone_private', False)

        self.birthday: DateTime = pendulum.parse(data.get('birthday', dt.datetime.now()).isoformat(), tz=self.timezone)
        self.birthday_private: bool = data.get('birthday_private', False)

        self.spotify_refresh_token: Optional[str] = data.get('spotify_refresh_token', None)

        self.reminders: List[Reminder] = []
        self.requires_db_update: List[str] = []

        self.created_at: DateTime = pendulum.instance(data.get('created_at', dt.datetime.now()), tz=self.timezone)

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


class DefaultGuildConfig:

    __slots__ = 'embed_size'

    def __init__(self) -> None:
        self.embed_size = 'small'

    def __repr__(self) -> str:
        return f'<DefaultGuildConfig>'


class GuildConfig:

    __slots__ = 'embed_size'

    def __init__(self, data: dict) -> None:

        self.embed_size = data.get('embed_size', 'small')

    def __repr__(self) -> str:
        return f'<GuildConfig>'


class Tag:

    __slots__ = 'owner_id', 'name', 'content', 'alias', 'created_at'

    def __init__(self, data: dict) -> None:

        self.owner_id: int = data.get('owner_id')
        self.name: str = data.get('name')
        self.content: str = data.get('content')
        self.alias: str = data.get('alias')
        self.created_at: DateTime = pendulum.instance(data.get('created_at'), tz='UTC')

    def __repr__(self) -> str:
        return f'<Tag owner_id=\'{self.owner_id}\' name=\'{self.name}\' alias=\'{self.alias}\'>'


class Reminder:

    __slots__ = 'owner_id', 'id', 'created_at', 'datetime', 'content', 'message_link', 'message_id', 'task'

    def __init__(self, data: dict) -> None:

        self.owner_id: int = data.get('owner_id')
        self.id: int = data.get('id')
        self.created_at: DateTime = pendulum.instance(data.get('created_at'), tz='UTC')
        self.datetime: DateTime = pendulum.instance(data.get('datetime'), tz='UTC')
        self.content: str = data.get('content')
        self.message_link: str = data.get('message_link')
        self.message_id: int = data.get('message_id')

        self.task = None

    def __repr__(self) -> str:
        return f'<Reminder owner_id=\'{self.owner_id}\' id=\'{self.id}\' datetime={self.datetime} done={self.done}>'

    @property
    def done(self) -> bool:
        return pendulum.now(tz='UTC') > self.datetime
