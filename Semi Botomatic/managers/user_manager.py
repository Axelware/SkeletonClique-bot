from __future__ import annotations

import io
import logging
import math
import os
from typing import TYPE_CHECKING, Union

import pendulum
from PIL import Image, ImageDraw, ImageFont

from utilities import exceptions, objects

if TYPE_CHECKING:
    from bot import SemiBotomatic

__log__ = logging.getLogger(__name__)


class UserManager:

    def __init__(self, bot: SemiBotomatic) -> None:
        self.bot = bot

        self.default_config = objects.DefaultUserConfig()
        self.configs = {}

    async def load(self) -> None:

        configs = await self.bot.db.fetch('SELECT * FROM users')
        for config in configs:
            self.configs[config['id']] = objects.UserConfig(data=dict(config))

        __log__.info(f'[USER MANAGER] Loaded user configs. [{len(configs)} users]')
        print(f'[USER MANAGER] Loaded user configs. [{len(configs)} users]')

        await self.bot.reminder_manager.load()
        await self.bot.todo_manager.load()

    #

    async def create_config(self, *, user_id: int) -> objects.UserConfig:

        data = await self.bot.db.fetchrow('INSERT INTO users (id) values ($1) ON CONFLICT (id) DO UPDATE SET id = excluded.id RETURNING *', user_id)
        self.configs[user_id] = objects.UserConfig(data=dict(data))

        __log__.info(f'[USER MANAGER] Created config for user with id \'{user_id}\'')
        return self.configs[user_id]

    async def get_or_create_config(self, *, user_id: int) -> objects.UserConfig:

        user_config = self.get_config(user_id=user_id)
        if isinstance(user_config, objects.DefaultUserConfig):
            user_config = await self.create_config(user_id=user_id)

        return user_config

    def get_config(self, *, user_id: int) -> Union[objects.DefaultUserConfig, objects.UserConfig]:
        return self.configs.get(user_id, self.default_config)

    #

    async def set_timezone(self, *, user_id: int, timezone: str = 'UTC', private: bool = False) -> None:

        user_config = await self.get_or_create_config(user_id=user_id)
        timezone = str(user_config.timezone) if timezone is None else timezone

        data = await self.bot.db.fetchrow('UPDATE users SET timezone = $1, timezone_private = $2 WHERE id = $3 RETURNING timezone, timezone_private', timezone, private, user_id)
        user_config.timezone = pendulum.timezone(data['timezone'])
        user_config.timezone_private = private

    async def set_birthday(self, *, user_id: int, birthday: pendulum.datetime = None, private: bool = None) -> None:

        user_config = await self.get_or_create_config(user_id=user_id)
        birthday = user_config.birthday if birthday is None else birthday
        private = user_config.timezone_private if private is None else private

        data = await self.bot.db.fetchrow('UPDATE users SET birthday = $1, birthday_private = $2 WHERE id = $3 RETURNING birthday, birthday_private', birthday, private, user_id)
        user_config.birthday = pendulum.parse(data['birthday'].isoformat(), tz='UTC')
        user_config.birthday_private = private

    async def set_blacklisted(self, *, user_id: int, blacklisted: bool = True, reason: str = None) -> None:

        user_config = await self.get_or_create_config(user_id=user_id)

        query = 'UPDATE users SET blacklisted = $1, blacklisted_reason = $2 WHERE id = $3 RETURNING blacklisted, blacklisted_reason'
        data = await self.bot.db.fetchrow(query, blacklisted, reason, user_id)
        user_config.blacklisted = data['blacklisted']
        user_config.blacklisted_reason = data['blacklisted_reason']

    async def set_spotify_token(self, user_id: int, token: str) -> None:

        user_config = await self.get_or_create_config(user_id=user_id)

        data = await self.bot.db.fetchrow('UPDATE users SET spotify_refresh_token = $1 WHERE id = $2 RETURNING spotify_refresh_token', token, user_id)
        user_config.spotify_refresh_token = data['spotify_refresh_token']

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
        return buffer
