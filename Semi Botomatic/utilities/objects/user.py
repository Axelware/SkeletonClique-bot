from __future__ import annotations

import logging
import math
from typing import Optional, TYPE_CHECKING

import pendulum

from utilities import enums, objects

if TYPE_CHECKING:
    from bot import SemiBotomatic


__log__ = logging.getLogger('utilities.objects.user')


class UserConfig:

    __slots__ = '_bot', '_id', '_created_at', '_blacklisted', '_blacklisted_reason', '_colour', '_timezone', '_timezone_private', '_birthday', '_birthday_private', \
                '_xp', '_coins', '_notifications', '_reminders', '_todos', '_requires_db_update'

    def __init__(self, bot: SemiBotomatic, data: dict) -> None:

        self._bot = bot

        self._id: int = data.get('id', 0)
        self._created_at: pendulum.datetime = pendulum.instance(created_at, tz='UTC') if (created_at := data.get('created_at')) else pendulum.now(tz='UTC')

        self._blacklisted: bool = data.get('blacklisted', False)
        self._blacklisted_reason: Optional[str] = data.get('blacklisted_reason')

        self._timezone: Optional[pendulum.timezone] = pendulum.timezone(data.get('timezone')) if data.get('timezone') else None
        self._timezone_private: bool = data.get('timezone_private', False)

        self._birthday: Optional[pendulum.datetime] = pendulum.parse(data.get('birthday').isoformat(), tz='UTC') if data.get('birthday') else None
        self._birthday_private: bool = data.get('birthday_private', False)

        self._xp: int = data.get('xp', 0)
        self._coins: int = data.get('coins', 0)

        self._notifications: Optional[objects.Notifications] = None
        self._todos: dict[int, objects.Todo] = {}
        self._reminders: dict[int, objects.Reminder] = {}

        self._requires_db_update: set = set()

    def __repr__(self) -> str:
        return f'<UserConfig id=\'{self.id}\' blacklisted={self.blacklisted} timezone=\'{self.timezone}\' xp={self.xp} coins={self.coins} ' \
               f'level={self.level}>'

    # Properties

    @property
    def bot(self) -> SemiBotomatic:
        return self._bot

    @property
    def id(self) -> int:
        return self._id

    @property
    def created_at(self) -> pendulum.datetime:
        return self._created_at

    @property
    def blacklisted(self) -> bool:
        return self._blacklisted

    @property
    def blacklisted_reason(self) -> str:
        return self._blacklisted_reason

    @property
    def timezone(self) -> Optional[pendulum.timezone]:
        return self._timezone

    @property
    def timezone_private(self) -> bool:
        return self._timezone_private

    @property
    def birthday(self) -> Optional[pendulum.timezone]:
        return self._birthday

    @property
    def birthday_private(self) -> bool:
        return self._birthday_private

    @property
    def xp(self) -> int:
        return self._xp

    @property
    def coins(self) -> int:
        return self._coins

    @property
    def notifications(self) -> Optional[objects.Notifications]:
        return self._notifications

    @property
    def todos(self) -> dict[int, objects.Todo]:
        return self._todos

    @property
    def reminders(self) -> dict[int, objects.Reminder]:
        return self._reminders

    #

    @property
    def age(self) -> Optional[int]:

        if not self.birthday:
            return None

        return (pendulum.now(tz='UTC') - self.birthday).in_years()

    @property
    def next_birthday(self) -> Optional[pendulum.datetime]:

        if not self.birthday:
            return None

        now = pendulum.now(tz='UTC')

        return now.replace(
                year=now.year + 1 if now > self.birthday.add(years=self.age) else now.year,
                month=self.birthday.month,
                day=self.birthday.day,
                hour=12, minute=0, second=0, microsecond=0
        )

    @property
    def time(self) -> Optional[pendulum.datetime]:

        if not self.timezone:
            return None

        return pendulum.now(tz=self.timezone)

    @property
    def level(self) -> int:
        return math.floor((((self.xp / 100) ** (1.0 / 1.5)) / 3))

    @property
    def next_level_xp(self) -> int:
        return round((((((self.level + 1) * 3) ** 1.5) * 100) - self.xp))

    # Misc

    async def delete(self) -> None:

        await self.bot.db.execute('DELETE FROM users WHERE id = $1', self.id)

        for reminder in self.reminders.values():
            if not reminder.done:
                self.bot.scheduler.cancel(reminder.task)

        del self.bot.user_manager.configs[self.id]

    # Config

    async def set_blacklisted(self, blacklisted: bool, *, reason: str = None) -> None:

        data = await self.bot.db.fetchrow(
                'UPDATE users SET blacklisted = $1, blacklisted_reason = $2 WHERE id = $3 RETURNING blacklisted, blacklisted_reason',
                blacklisted, reason, self.id
        )

        self._blacklisted = data['blacklisted']
        self._blacklisted_reason = data['blacklisted_reason']

    async def set_timezone(self, timezone: str, *, private: bool = None) -> None:

        private = private or self.timezone_private

        data = await self.bot.db.fetchrow('UPDATE users SET timezone = $1, timezone_private = $2 WHERE id = $3 RETURNING timezone, timezone_private', timezone, private, self.id)
        self._timezone = pendulum.timezone(data.get('timezone')) if data.get('timezone') else None
        self._timezone_private = private

    async def set_birthday(self, birthday: pendulum.datetime, *, private: bool = None) -> None:

        private = private or self.birthday_private

        data = await self.bot.db.fetchrow('UPDATE users SET birthday = $1, birthday_private = $2 WHERE id = $3 RETURNING birthday, birthday_private', birthday, private, self.id)
        self._birthday = pendulum.parse(data.get('birthday').isoformat(), tz='UTC') if data.get('birthday') else None
        self._birthday_private = private

    def change_coins(self, coins: int, *, operation: enums.Operation = enums.Operation.ADD) -> None:

        if operation == enums.Operation.SET:
            self._coins = coins
        elif operation == enums.Operation.ADD:
            self._coins += coins
        elif operation == enums.Operation.MINUS:
            self._coins -= coins

        self._requires_db_update.add(enums.Updateable.COINS)

    def change_xp(self, xp: int, *, operation: enums.Operation = enums.Operation.ADD) -> None:

        if operation == enums.Operation.SET:
            self._xp = xp
        elif operation == enums.Operation.ADD:
            self._xp += xp
        elif operation == enums.Operation.MINUS:
            self._xp -= xp

        self._requires_db_update.add(enums.Updateable.XP)

    # Reminders

    async def create_reminder(
            self, *, channel_id: int, datetime: pendulum.datetime, content: str, jump_url: str = None, repeat_type: enums.ReminderRepeatType = enums.ReminderRepeatType.NEVER
    ) -> objects.Reminder:

        data = await self.bot.db.fetchrow(
                'INSERT INTO reminders (user_id, channel_id, datetime, content, jump_url, repeat_type) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *',
                self.id, channel_id, datetime, content, jump_url, repeat_type.value
        )

        reminder = objects.Reminder(bot=self.bot, user_config=self, data=data)
        self._reminders[reminder.id] = reminder

        if not reminder.done:
            reminder.schedule()

        __log__.info(f'[REMINDERS] Created reminder with id \'{reminder.id}\'for user with id \'{reminder.user_id}\'.')
        return reminder

    def get_reminder(self, reminder_id: int) -> Optional[objects.Reminder]:
        return self.reminders.get(reminder_id)

    async def delete_reminder(self, reminder_id: int) -> None:

        if not (reminder := self.get_reminder(reminder_id)):
            return

        await reminder.delete()

    # Todos

    async def create_todo(self, *, content: str, jump_url: str = None) -> objects.Todo:

        data = await self.bot.db.fetchrow('INSERT INTO todos (user_id, content, jump_url) VALUES ($1, $2, $3) RETURNING *', self.id, content, jump_url)

        todo = objects.Todo(bot=self.bot, user_config=self, data=data)
        self._todos[todo.id] = todo

        __log__.info(f'[TODOS] Created todo with id \'{todo.id}\'for user with id \'{todo.user_id}\'.')
        return todo

    def get_todo(self, todo_id: int) -> Optional[objects.Todo]:
        return self.todos.get(todo_id)

    async def delete_todo(self, todo_id: int) -> None:

        if not (todo := self.get_todo(todo_id)):
            return

        await todo.delete()
