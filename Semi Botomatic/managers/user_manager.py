from __future__ import annotations

import io
import logging
import math
import os
from typing import Any, TYPE_CHECKING, Union

import pendulum
from PIL import Image, ImageDraw, ImageFont
from discord.ext import tasks

from utilities import exceptions, objects
from utilities.enums import Editables, Operations

if TYPE_CHECKING:
    from bot import SemiBotomatic

__log__ = logging.getLogger(__name__)


class UserManager:

    def __init__(self, bot: SemiBotomatic) -> None:
        self.bot = bot

        self.default_config = objects.DefaultUserConfig()
        self.configs = {}

        self.update_database.start()

    async def load(self) -> None:

        configs = await self.bot.db.fetch('SELECT * FROM users')
        for config in configs:
            self.configs[config['id']] = objects.UserConfig(data=dict(config))

        __log__.info(f'[USER MANAGER] Loaded user configs. [{len(configs)} users]')
        print(f'[USER MANAGER] Loaded user configs. [{len(configs)} users]')

        await self.bot.reminder_manager.load()
        await self.bot.todo_manager.load()

    #

    @tasks.loop(seconds=60)
    async def update_database(self) -> None:

        if not self.configs:
            return

        need_updating = {user_id: user_config for user_id, user_config in self.configs.items() if len(user_config.requires_db_update) >= 1}

        async with self.bot.db.acquire(timeout=300) as db:
            for user_id, user_config in need_updating.items():

                query = ','.join(f'{editable.value} = ${index + 2}' for index, editable in enumerate(user_config.requires_db_update))
                await db.execute(f'UPDATE users SET {query} WHERE id = $1', user_id, *[getattr(user_config, attribute.value) for attribute in user_config.requires_db_update])

                user_config.requires_db_update = []

    @update_database.before_loop
    async def before_update_database(self) -> None:
        await self.bot.wait_until_ready()

    #

    async def create_user_config(self, *, user_id: int) -> objects.UserConfig:

        data = await self.bot.db.fetchrow('INSERT INTO users (id) values ($1) ON CONFLICT (id) DO UPDATE SET id = excluded.id RETURNING *', user_id)
        self.configs[user_id] = objects.UserConfig(data=dict(data))

        __log__.info(f'[USER MANAGER] Created config for user with id \'{user_id}\'')
        return self.configs[user_id]

    def get_user_config(self, *, user_id: int) -> Union[objects.DefaultUserConfig, objects.UserConfig]:
        return self.configs.get(user_id, self.default_config)

    async def get_or_create_user_config(self, *, user_id: int) -> objects.UserConfig:

        user_config = self.get_user_config(user_id=user_id)
        if isinstance(user_config, objects.DefaultUserConfig):
            user_config = await self.create_user_config(user_id=user_id)

        return user_config

    async def edit_user_config(self, *, user_id: int, editable: Editables, operation: Operations, value: Any = None) -> objects.UserConfig:

        user_config = self.get_user_config(user_id=user_id)
        if isinstance(user_config, objects.DefaultUserConfig):
            user_config = await self.create_user_config(user_id=user_id)

        __log__.info(f'[USER MANAGERS] Edited user config for user with id \'{user_id}\'. Editable: {editable.value} | Operation: {operation.value} | Value: {value}')

        if editable == Editables.blacklist:

            operations = {
                Operations.set.value:
                    ('UPDATE users SET blacklisted = $1, blacklisted_reason = $2 WHERE id = $3 RETURNING blacklisted, blacklisted_reason', True, value, user_id),
                Operations.reset.value:
                    ('UPDATE users SET blacklisted = $1, blacklisted_reason = $2 WHERE id = $3 RETURNING blacklisted, blacklisted_reason', False, None, user_id)
            }

            data = await self.bot.db.fetchrow(*operations[operation.value])
            user_config.blacklisted = data['blacklisted']
            user_config.blacklisted_reason = data['blacklisted_reason']

        elif editable == Editables.timezone:

            operations = {
                Operations.set.value: ('UPDATE users SET timezone = $1 WHERE id = $2 RETURNING timezone', value, user_id),
                Operations.reset.value: ('UPDATE users SET timezone = $1 WHERE id = $2 RETURNING timezone', 'UTC', user_id)
            }

            data = await self.bot.db.fetchrow(*operations[operation.value])
            user_config.timezone = pendulum.timezone(data['timezone'])

        elif editable == Editables.timezone_private:

            operations = {
                Operations.set.value: ('UPDATE users SET timezone_private = $1 WHERE id = $2 RETURNING timezone_private', True, user_id),
                Operations.reset.value: ('UPDATE users SET timezone_private = $1 WHERE id = $2 RETURNING timezone_private', False, user_id)
            }

            data = await self.bot.db.fetchrow(*operations[operation.value])
            user_config.timezone_private = data['timezone_private']

        elif editable == Editables.birthday:

            operations = {
                Operations.set.value: ('UPDATE users SET birthday = $1 WHERE id = $2 RETURNING birthday', value, user_id),
                Operations.reset.value: ('UPDATE users SET birthday = $1 WHERE id = $2 RETURNING birthday', pendulum.datetime(year=2020, month=1, day=1), user_id)
            }

            data = await self.bot.db.fetchrow(*operations[operation.value])
            user_config.birthday = pendulum.parse(data['birthday'].isoformat(), tz='UTC')

        elif editable == Editables.birthday_private:

            operations = {
                Operations.set.value: ('UPDATE users SET birthday_private = $1 WHERE id = $2 RETURNING birthday_private', True, user_id),
                Operations.reset.value: ('UPDATE users SET birthday_private = $1 WHERE id = $2 RETURNING birthday_private', False, user_id)
            }

            data = await self.bot.db.fetchrow(*operations[operation.value])
            user_config.birthday_private = data['birthday_private']

        elif editable == Editables.spotify_refresh_token:

            operations = {
                Operations.set.value: ('UPDATE users SET spotify_refresh_token = $1 WHERE id = $2 RETURNING spotify_refresh_token', value, user_id),
                Operations.reset.value: ('UPDATE users SET spotify_refresh_token = $1 WHERE id = $2 RETURNING spotify_refresh_token', None, user_id),
            }

            data = await self.bot.db.fetchrow(*operations[operation.value])
            user_config.spotify_refresh_token = data['spotify_refresh_token']

        return user_config

    #

    async def create_timecard(self, *, guild_id: int) -> io.BytesIO:

        guild = self.bot.get_guild(guild_id)
        if not guild:
            raise exceptions.ArgumentError('Guild with that id not found.')

        configs = sorted(self.configs.items(), key=lambda kv: kv[1].time.offset_hours)
        timezone_users = {}

        for user_id, config in configs:

            user = guild.get_member(user_id)
            if not user:
                continue

            if config.timezone_private or config.timezone == pendulum.timezone('UTC'):
                continue

            if timezone_users.get(config.time.format('HH:mm (ZZ)')) is None:
                timezone_users[config.time.format('HH:mm (ZZ)')] = [io.BytesIO(await user.avatar_url_as(format='png', size=256).read())]
            else:
                timezone_users[config.time.format('HH:mm (ZZ)')].append(io.BytesIO(await user.avatar_url_as(format='png', size=256).read()))

        if not timezone_users:
            raise exceptions.ArgumentError('There are no users with timezones set in this server.')

        buffer = await self.bot.loop.run_in_executor(None, self.create_timecard_image, timezone_users)
        return buffer

    @staticmethod
    def create_timecard_image(timezone_users: dict) -> io.BytesIO:

        width_x = (1600 * (len(timezone_users.keys()) if len(timezone_users.keys()) < 5 else 5)) + 100
        height_y = (1800 * math.ceil(len(timezone_users.keys()) / 5)) + 100

        image = Image.new('RGBA', (width_x, height_y), color='#f1c30f')
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(os.path.abspath(os.path.join(os.path.dirname(__file__), '../resources/arial.ttf')), 120)

        x = 100
        y = 100

        for timezone, users in timezone_users.items():

            draw.text((x, y), timezone, font=font, fill='#1b1a1c')

            user_x = x
            user_y = y + 200

            for user in users[:36]:

                avatar = Image.open(user)
                avatar = avatar.resize((250, 250))

                image.paste(avatar, (user_x, user_y))

                if user_x < x + 1200:
                    user_x += 250
                else:
                    user_y += 250
                    user_x = x

            if x > 6400:
                y += 1800
                x = 100
            else:
                x += 1600

        buffer = io.BytesIO()
        image.save(buffer, 'png')
        buffer.seek(0)

        image.close()
        del image
        del draw
        del font

        return buffer
