from typing import List
import datetime as dt

import pendulum


class DefaultUserConfig:

    __slots__ = ('id', 'created_at', 'timezone', 'timezone_private', 'birthday', 'birthday_private', 'reminders', 'requires_db_update')

    def __init__(self) -> None:

        self.id = 0
        self.created_at = pendulum.now(tz='UTC')

        self.timezone = pendulum.timezone('UTC')
        self.timezone_private = False
        
        self.birthday = pendulum.DateTime(2020, 1, 1, 0, 0, 0, tzinfo=pendulum.timezone('UTC'))
        self.birthday_private = False

        self.reminders = []
        self.requires_db_update = []

    def __repr__(self) -> str:
        return f'<DefaultUserConfig id=\'{self.id}\'>'

    @property
    def time(self) -> pendulum.datetime:
        return pendulum.now(tz=self.timezone)

    @property
    def age(self) -> int:
        return (pendulum.now(tz='UTC') - self.birthday).in_years()

    @property
    def next_birthday(self) -> pendulum.datetime:
        return self.birthday.replace(year=self.birthday.year + self.age + 1)


class UserConfig(DefaultUserConfig):

    def __init__(self, data: dict) -> None:
        super().__init__()

        self.id: int = data.get('id', 0)
        self.created_at: pendulum.datetime = pendulum.instance(data.get('created_at', dt.datetime.now()), tz=self.timezone)

        self.timezone: pendulum.timezone = pendulum.timezone(data.get('timezone', 'UTC'))
        self.timezone_private: bool = data.get('timezone_private', False)

        self.birthday: pendulum.datetime = pendulum.instance(data.get('birthday', dt.datetime.now()), tz=self.timezone)
        self.birthday_private: bool = data.get('birthday_private', False)

        self.reminders: List[Reminder] = []
        self.requires_db_update: List[str] = []

    def __repr__(self) -> str:
        return f'<UserConfig id=\'{self.id}\'>'


class Tag:

    def __init__(self, data: dict) -> None:

        self.owner_id = data.get('owner_id')
        self.name = data.get('name')
        self.content = data.get('content')
        self.alias = data.get('alias')
        self.created_at = pendulum.instance(data.get('created_at'), tz='UTC')

    def __repr__(self) -> str:
        return f'<Tag owner_id=\'{self.owner_id}\' name=\'{self.name}\' alias=\'{self.alias}\'>'
