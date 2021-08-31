# Future
from __future__ import annotations

# Standard Library
from typing import TYPE_CHECKING, Any, Optional

# Packages
import aioscheduler.task
import discord
import pendulum

# My stuff
from core import colours
from utilities import enums, objects, utils


if TYPE_CHECKING:
    # My stuff
    from core.bot import SkeletonClique


REPEAT_TYPES = {
    1:  lambda dt: dt.add(minutes=30),
    2:  lambda dt: dt.add(hours=1),
    3:  lambda dt: dt.add(hours=2),
    4:  lambda dt: dt.add(hours=12),
    5:  lambda dt: dt.add(days=1),
    6:  lambda dt: dt.add(days=2),
    7:  lambda dt: dt.add(days=7),
    8:  lambda dt: dt.add(days=14),
    9:  lambda dt: dt.add(weeks=2),
    10: lambda dt: dt.add(months=1),
    11: lambda dt: dt.add(months=2),
    12: lambda dt: dt.add(months=6),
    13: lambda dt: dt.add(years=1),
    14: lambda dt: dt.add(years=2),
    15: lambda dt: dt.add(seconds=30)
}


class Reminder:

    def __init__(self, bot: SkeletonClique, user_config: objects.user.UserConfig, data: dict[str, Any]) -> None:

        self._bot = bot
        self._user_config = user_config

        self._id: int = data["id"]
        self._user_id: int = data["user_id"]
        self._channel_id: int = data["channel_id"]
        self._created_at: pendulum.DateTime = pendulum.instance(data["created_at"], tz="UTC")
        self._content: str = data["content"]
        self._jump_url: str = data["jump_url"]
        self._repeat_type: enums.ReminderRepeatType = enums.ReminderRepeatType(data["repeat_type"])
        self._notified: bool = data["notified"]
        self._datetime: pendulum.DateTime = pendulum.instance(data["datetime"], tz="UTC")

        self._task: Optional[aioscheduler.task.Task] = None

    def __repr__(self) -> str:
        return f"<Reminder id=\"{self.id}\" channel_id=\"{self.channel_id}\" user_id=\"{self.user_id}\" datetime={self.datetime} notified={self.notified} done={self.done}>"

    # Properties

    @property
    def bot(self) -> SkeletonClique:
        return self._bot

    @property
    def user_config(self) -> objects.UserConfig:
        return self._user_config

    @property
    def id(self) -> int:
        return self._id

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def channel_id(self) -> int:
        return self._channel_id

    @property
    def created_at(self) -> pendulum.DateTime:
        return self._created_at

    @property
    def content(self) -> str:
        return self._content

    @property
    def jump_url(self) -> str:
        return self._jump_url

    @property
    def repeat_type(self) -> enums.ReminderRepeatType:
        return self._repeat_type

    @property
    def notified(self) -> bool:
        return self._notified

    @property
    def datetime(self) -> pendulum.DateTime:
        return self._datetime

    @property
    def task(self) -> Optional[aioscheduler.task.Task]:
        return self._task

    #

    @property
    def done(self) -> bool:
        return pendulum.now(tz="UTC") > self.datetime

    # Misc

    async def delete(self) -> None:

        if not self.done:
            self.bot.scheduler.cancel(self.task)

        await self.bot.db.execute("DELETE FROM reminders WHERE id = $1", self.id)
        del self.user_config.reminders[self.id]

    # Handling

    def schedule(self) -> None:
        self._task = self.bot.scheduler.schedule(self.handle_notification(), when=self.datetime.naive())

    async def handle_notification(self) -> None:

        # TODO user user_configs user attribute here.

        user = self.bot.get_user(self.user_id)
        channel: Any = self.bot.get_channel(self.channel_id)

        embed = discord.Embed(
            colour=colours.MAIN,
            title="Reminder:",
            description=f"[`{utils.format_difference(self.created_at)} ago:`]({self.jump_url})\n\n{self.content}"
        )

        try:
            await channel.send(f"{user.mention if isinstance(user, discord.User) else f'<@{self.user_id}>'}", embed=embed)
        except (discord.Forbidden, AttributeError):
            try:
                await user.send(embed=embed)
            except (discord.Forbidden, AttributeError):
                return

        await self.set_notified()
        if self.repeat_type != enums.ReminderRepeatType.NEVER:
            await self.handle_repeat()

    async def handle_repeat(self) -> None:

        self._task = None

        await self.change_datetime(REPEAT_TYPES[self.repeat_type.value](self._datetime))
        await self.set_notified(False)

        self.schedule()

    # Config

    async def set_notified(self, notified: bool = True) -> None:

        data = await self.bot.db.fetchrow("UPDATE reminders SET notified = $1 WHERE id = $2 RETURNING notified", notified, self.id)
        self._notified = data["notified"]

    async def change_datetime(self, datetime: pendulum.DateTime) -> None:

        data = await self.bot.db.fetchrow("UPDATE reminders SET datetime = $1 WHERE id = $2 RETURNING datetime", datetime, self.id)
        self._datetime = pendulum.instance(data["datetime"], tz="UTC")

    async def change_content(self, content: str, *, jump_url: Optional[str] = None) -> None:

        data = await self.bot.db.fetchrow("UPDATE reminders SET content = $1, jump_url = $2 WHERE id = $3 RETURNING content, jump_url", content, jump_url, self.id)
        self._content = data["content"]
        self._jump_url = data["jump_url"] or self.jump_url

    async def change_repeat_type(self, repeat_type: enums.ReminderRepeatType) -> None:

        data = await self.bot.db.fetchrow("UPDATE reminders SET repeat_type = $1 WHERE id = $2 RETURNING repeat_type", repeat_type.value, self.id)
        self._repeat_type = enums.ReminderRepeatType(data["repeat_type"])
