from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING

import aioscheduler
import discord
from pendulum.datetime import DateTime

import config
from utilities import objects, utils

if TYPE_CHECKING:
    from bot import SemiBotomatic

__log__ = logging.getLogger(__name__)


class ReminderManager:

    def __init__(self, bot: SemiBotomatic) -> None:
        self.bot = bot

        self.scheduler = aioscheduler.Manager(2)

    async def load(self) -> None:

        self.scheduler.start()

        reminders = await self.bot.db.fetch('SELECT * FROM reminders order by datetime')
        for reminder_data in reminders:

            user_config = await self.bot.user_manager.get_or_create_user_config(user_id=reminder_data['user_id'])

            reminder = objects.Reminder(data=reminder_data)
            if not reminder.done:
                await self.schedule_reminder(reminder=reminder)

            user_config.reminders[reminder.id] = reminder

        __log__.info(f'[REMINDER MANAGER] Loaded reminders. [{len(reminders)} reminders]')
        print(f'[REMINDER MANAGER] Loaded reminders. [{len(reminders)} reminders]')

    #

    async def schedule_reminder(self, *, reminder: objects.Reminder) -> None:

        reminder.task = self.scheduler.schedule(self.do_reminder(reminder=reminder), when=reminder.datetime.naive())
        __log__.info(f'[REMINDER MANAGER] Scheduled reminder with id \'{reminder.id}\' for \'{reminder.datetime}\'')

    async def do_reminder(self, *, reminder: objects.Reminder) -> None:

        user = self.bot.get_user(reminder.user_id)
        if not user:
            __log__.warning(f'[REMINDER MANAGER] Attempted reminder with id \'{reminder.id}\' but user with \'{reminder.user_id}\' was not found.')
            return

        embed = discord.Embed(colour=discord.Colour(config.COLOUR),
                              description=f'**Reminder:**\n'
                                          f'You said this `{utils.format_difference(datetime=reminder.created_at, suppress=[])}` ago:\n'
                                          f'{reminder.content}\n\n'
                                          f'**[Jump to message]({reminder.jump_url})**'
        )

        try:
            await user.send(embed=embed)
        except discord.Forbidden:
            __log__.warning(f'[REMINDER MANAGER] Attempted reminder with id \'{reminder.id}\' but user with \'{reminder.user_id}\' was not able to be DM\'ed.')

    #

    async def get_reminder(self, *, user_id: int, reminder_id: int) -> Optional[objects.Reminder]:

        user_config = await self.bot.user_manager.get_or_create_user_config(user_id=user_id)
        return user_config.reminders.get(reminder_id)

    async def create_reminder(self, *, user_id: int, datetime: DateTime, content: str, jump_url: str = None) -> objects.Reminder:

        user_config = await self.bot.user_manager.get_or_create_user_config(user_id=user_id)

        data = await self.bot.db.fetchrow('INSERT INTO reminders (user_id, datetime, content, jump_url) VALUES ($1, $2, $3, $4) RETURNING *', user_id, datetime, content, jump_url)
        __log__.info(f'[REMINDER MANAGER] Created reminder with id \'{data["id"]}\'for user with id \'{user_id}\'')

        reminder = objects.Reminder(data=data)
        if not reminder.done:
            await self.schedule_reminder(reminder=reminder)

        user_config.reminders[reminder.id] = reminder
        return reminder

    async def delete_reminder(self, user_id: int, reminder_id: int) -> None:

        user_config = await self.bot.user_manager.get_or_create_user_config(user_id=user_id)
        reminder = await self.get_reminder(user_id=user_id, reminder_id=reminder_id)
        if not reminder:
            return

        if reminder.task:
            self.scheduler.cancel(reminder.task)

        await self.bot.db.execute('DELETE FROM reminders WHERE id = $1', reminder.id)
        del user_config.reminders[reminder_id]

    async def edit_reminder_content(self, user_id: int, reminder_id: int, content: str, jump_url: str = None) -> None:

        reminder = await self.get_reminder(user_id=user_id, reminder_id=reminder_id)
        if not reminder:
            return

        await self.bot.db.execute('UPDATE reminders SET content = $1, jump_url = $2 WHERE id = $3', content, jump_url, reminder.id)
        reminder.content = content

        if jump_url:
            reminder.jump_url = jump_url
