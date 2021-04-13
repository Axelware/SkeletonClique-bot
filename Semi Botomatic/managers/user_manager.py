from __future__ import annotations

import contextlib
import io
import logging
import math
import os
import pathlib
import random
from typing import Literal, TYPE_CHECKING, Union

import discord
import pendulum
from PIL import Image, ImageDraw, ImageFont
from colorthief import ColorThief
from discord.ext import tasks
from pendulum import DateTime

import config
from utilities import enums, exceptions, objects, utils

if TYPE_CHECKING:
    from bot import SemiBotomatic

__log__ = logging.getLogger(__name__)


class UserManager:

    def __init__(self, bot: SemiBotomatic) -> None:
        self.bot = bot

        self.default_config = objects.DefaultUserConfig()
        self.configs = {}

        self.update_database.start()

        self.IMAGES = {
            'SAI': {
                'level_cards': [
                    pathlib.Path('./resources/SAI/level_cards/1.png'),
                    pathlib.Path('./resources/SAI/level_cards/2.png'),
                    pathlib.Path('./resources/SAI/level_cards/3.png'),
                    pathlib.Path('./resources/SAI/level_cards/4.png'),
                    pathlib.Path('./resources/SAI/level_cards/5.png'),
                    pathlib.Path('./resources/SAI/level_cards/6.png'),
                    pathlib.Path('./resources/SAI/level_cards/7.png'),
                    pathlib.Path('./resources/SAI/level_cards/8.png'),
                    pathlib.Path('./resources/SAI/level_cards/9.png'),
                ],
                'leaderboard': [
                    pathlib.Path('./resources/SAI/leaderboard/1.png'),
                    pathlib.Path('./resources/SAI/leaderboard/2.png'),
                    pathlib.Path('./resources/SAI/leaderboard/3.png'),
                    pathlib.Path('./resources/SAI/leaderboard/4.png'),
                    pathlib.Path('./resources/SAI/leaderboard/5.png'),
                    pathlib.Path('./resources/SAI/leaderboard/6.png'),
                ]
            }
        }

        self.ARIAL_FONT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../resources/fonts/arial.ttf'))
        self.KABEL_BLACK_FONT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../resources/fonts/kabel_black.otf'))

    async def load(self) -> None:

        configs = await self.bot.db.fetch('SELECT * FROM users')
        notifications = await self.bot.db.fetch('SELECT * FROM notifications')

        for config_data, notification_data in zip(configs, notifications):
            user_config = objects.UserConfig(data=config_data)
            user_config.notifications = objects.Notifications(data=notification_data)
            self.configs[user_config.id] = user_config

        __log__.info(f'[USER MANAGER] Loaded user configs. [{len(configs)} users]')
        print(f'[USER MANAGER] Loaded user configs. [{len(configs)} users]')

        await self.bot.reminder_manager.load()
        await self.bot.todo_manager.load()

    # Background tasks.

    @tasks.loop(seconds=60)
    async def update_database(self) -> None:

        if not self.configs:
            return

        need_updating = {user_id: user_config for user_id, user_config in self.configs.items() if len(user_config.requires_db_update) >= 1}

        async with self.bot.db.acquire(timeout=300) as db:
            for user_id, user_config in need_updating.items():

                query = ','.join(f'{editable.value} = ${index + 2}' for index, editable in enumerate(user_config.requires_db_update))
                await db.execute(f'UPDATE users SET {query} WHERE id = $1', user_id, *[getattr(user_config, attribute.value) for attribute in user_config.requires_db_update])

                user_config.requires_db_update = set()

    @update_database.before_loop
    async def before_update_database(self) -> None:
        await self.bot.wait_until_ready()

    # User management

    def get_config(self, user_id: int) -> Union[objects.DefaultUserConfig, objects.UserConfig]:
        return self.configs.get(user_id, self.default_config)

    async def create_config(self, user_id: int) -> objects.UserConfig:

        data = await self.bot.db.fetchrow('INSERT INTO users (id) values ($1) ON CONFLICT (id) DO UPDATE SET id = excluded.id RETURNING *', user_id)
        notifications = await self.bot.db.fetchrow('INSERT INTO notifications (user_id) values ($1) ON CONFLICT (id) DO UPDATE SET id = excluded.user_id RETURNING *', user_id)

        user_config = objects.UserConfig(data=data)
        user_config.notifications = objects.Notifications(data=notifications)

        self.configs[user_id] = user_config
        __log__.info(f'[USER MANAGER] Created config for user with id \'{user_id}\'')

        return user_config

    async def get_or_create_config(self, user_id: int) -> objects.UserConfig:

        if isinstance(user_config := self.get_config(user_id), objects.DefaultUserConfig):
            user_config = await self.create_config(user_id)

        return user_config

    # Regular settings

    async def set_timezone(self, user_id: int, *, timezone: str = 'UTC', private: bool = False) -> None:

        user_config = await self.get_or_create_config(user_id)
        timezone = str(user_config.timezone) if timezone is None else timezone

        data = await self.bot.db.fetchrow('UPDATE users SET timezone = $1, timezone_private = $2 WHERE id = $3 RETURNING timezone, timezone_private', timezone, private, user_id)
        user_config.timezone = pendulum.timezone(data['timezone'])
        user_config.timezone_private = private

    async def set_birthday(self, user_id: int, *, birthday: pendulum.datetime = None, private: bool = None) -> None:

        user_config = await self.get_or_create_config(user_id)
        birthday = user_config.birthday if birthday is None else birthday
        private = user_config.timezone_private if private is None else private

        data = await self.bot.db.fetchrow('UPDATE users SET birthday = $1, birthday_private = $2 WHERE id = $3 RETURNING birthday, birthday_private', birthday, private, user_id)
        user_config.birthday = pendulum.parse(data['birthday'].isoformat(), tz='UTC')
        user_config.birthday_private = private

    async def set_blacklisted(self, user_id: int, *, blacklisted: bool = True, reason: str = None) -> None:

        user_config = await self.get_or_create_config(user_id)

        query = 'UPDATE users SET blacklisted = $1, blacklisted_reason = $2 WHERE id = $3 RETURNING blacklisted, blacklisted_reason'
        data = await self.bot.db.fetchrow(query, blacklisted, reason, user_id)
        user_config.blacklisted = data['blacklisted']
        user_config.blacklisted_reason = data['blacklisted_reason']

    async def set_spotify_token(self, user_id: int, *, token: str) -> None:

        user_config = await self.get_or_create_config(user_id)

        data = await self.bot.db.fetchrow('UPDATE users SET spotify_refresh_token = $1 WHERE id = $2 RETURNING spotify_refresh_token', token, user_id)
        user_config.spotify_refresh_token = data['spotify_refresh_token']

    # Economy stuff

    async def set_coins(self, user_id: int, *, coins: int, operation: enums.Operation = enums.Operation.ADD) -> None:

        user_config = await self.get_or_create_config(user_id)

        if operation == enums.Operation.SET:
            user_config.coins = coins
        elif operation == enums.Operation.ADD:
            user_config.coins += coins
        elif operation == enums.Operation.MINUS:
            user_config.coins -= coins

        user_config.requires_db_update.add(enums.Updateable.COINS)

    async def set_xp(self, user_id: int, *, xp: int, operation: enums.Operation = enums.Operation.ADD) -> None:

        user_config = await self.get_or_create_config(user_id)

        if operation == enums.Operation.SET:
            user_config.xp = xp
        elif operation == enums.Operation.ADD:
            user_config.xp += xp
        elif operation == enums.Operation.MINUS:
            user_config.xp -= xp

        user_config.requires_db_update.add(enums.Updateable.XP)

    async def set_bundle_collection(
            self, user_id: int, *, collection_type: Union[enums.Updateable.DAILY_COLLECTED, enums.Updateable.WEEKLY_COLLECTED, enums.Updateable.MONTHLY_COLLECTED],
            when: DateTime = pendulum.now(tz='UTC')
    ) -> None:

        user_config = await self.get_or_create_config(user_id)

        data = await self.bot.db.fetchrow(f'UPDATE users SET {collection_type.value} = $1 WHERE id = $2 RETURNING {collection_type.value}', when, user_id)
        setattr(user_config, collection_type.value, pendulum.instance(data[collection_type.value], tz='UTC'))

    async def set_bundle_streak(
            self, user_id: int, *, bundle_type: Union[enums.Updateable.DAILY_STREAK, enums.Updateable.WEEKLY_STREAK, enums.Updateable.MONTHLY_STREAK],
            operation: enums.Operation = enums.Operation.SET, count: int = 0
    ) -> None:

        user_config = await self.get_or_create_config(user_id)

        streak = None
        if operation == enums.Operation.SET:
            streak = count
        elif operation == enums.Operation.ADD:
            streak = getattr(user_config, bundle_type.value) + count
        elif operation == enums.Operation.MINUS:
            streak = getattr(user_config, bundle_type.value) - count
        elif operation == enums.Operation.RESET:
            streak = 0

        data = await self.bot.db.fetchrow(f'UPDATE users SET {bundle_type.value} = $1 WHERE id = $2 RETURNING {bundle_type.value}', streak, user_id)
        setattr(user_config, bundle_type.value, data[bundle_type.value])

    # Rankings

    def rank(self, user_id: int, *, guild_id: int = config.SKELETON_CLIQUE_GUILD_ID) -> Union[int, Literal['Unranked']]:

        guild = self.bot.get_guild(guild_id)

        with contextlib.suppress(ValueError):
            return list(dict(filter(
                    lambda kv: guild.get_member(kv[0]) is not None,
                    sorted(self.configs.items(), key=lambda kv: kv[1].xp, reverse=True)
            )).keys()).index(user_id) + 1

        return 'Unranked'

    def leaderboard(self, lb_type: Literal['xp', 'coins'] = 'xp', *, guild_id: int = config.SKELETON_CLIQUE_GUILD_ID) -> dict[int, objects.UserConfig]:

        guild = self.bot.get_guild(guild_id)
        return dict(filter(
                lambda kv: guild.get_member is not None and getattr(kv[1], lb_type) != 0,
                sorted(self.configs.items(), key=lambda kv: getattr(kv[1], lb_type), reverse=True)
        ))

    # Timecard image

    async def create_timecard(self, *, guild_id: int = config.SKELETON_CLIQUE_GUILD_ID) -> discord.File:

        guild = self.bot.get_guild(guild_id)

        user_configs = dict(filter(
                lambda kv: guild.get_member(kv[0]) is not None and not kv[1].timezone_private and not kv[1].timezone == pendulum.timezone('UTC'),
                sorted(self.configs.items(), key=lambda kv: kv[1].time.offset_hours)
        ))
        timezone_avatars = {}

        for user_config in user_configs.values():

            avatar_bytes = io.BytesIO(await guild.get_member(user_config.id).avatar_url_as(format='png', size=256).read())
            timezone = user_config.time.format('HH:mm (ZZ)')

            if not (users := timezone_avatars.get(timezone), []):
                if len(users) > 36:
                    break
                timezone_avatars[timezone].append(avatar_bytes)
            else:
                timezone_avatars[timezone] = [avatar_bytes]

        if not timezone_avatars:
            raise exceptions.ArgumentError('There are no users with timezones set in this server.')

        buffer = await self.bot.loop.run_in_executor(None, self.create_timecard_image, timezone_avatars)
        file = discord.File(fp=buffer, filename='level.png')

        buffer.close()
        for avatar_bytes in timezone_avatars.values():
            [buffer.close() for buffer in avatar_bytes]

        return file

    def create_timecard_image(self, timezone_users: dict) -> io.BytesIO:

        buffer = io.BytesIO()
        width_x, height_y = (1600 * (len(timezone_users) if len(timezone_users) < 5 else 5)) + 100, (1800 * math.ceil(len(timezone_users) / 5)) + 100

        with Image.new(mode='RGBA', size=(width_x, height_y), color='#F1C30F') as image:

            draw = ImageDraw.Draw(im=image)
            font = ImageFont.truetype(font=self.ARIAL_FONT, size=120)

            x, y = 100, 100

            for timezone, avatars in timezone_users.items():

                draw.text(xy=(x, y), text=timezone, font=font, fill='#1B1A1C')
                user_x, user_y = x, y + 200

                for avatar_bytes in avatars:

                    with Image.open(fp=avatar_bytes) as avatar:
                        avatar = avatar.resize(size=(250, 250), resample=Image.LANCZOS)
                        image.paste(im=avatar, box=(user_x, user_y), mask=avatar.convert(mode='RGBA'))

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

            image.save(fp=buffer, format='png')

        buffer.seek(0)
        return buffer

    # Level image

    async def create_level_card(self, user_id: int, *, guild_id: int = config.SKELETON_CLIQUE_GUILD_ID) -> discord.File:

        guild = self.bot.get_guild(guild_id)

        user = guild.get_member(user_id) if guild else self.bot.get_user(user_id)
        user_config = await self.get_or_create_config(user.id)
        avatar_bytes = io.BytesIO(await user.avatar_url_as(format='png', size=512).read())

        buffer = await self.bot.loop.run_in_executor(None, self.create_level_card_image, user, user_config, avatar_bytes)
        file = discord.File(fp=buffer, filename='level.png')

        buffer.close()
        avatar_bytes.close()

        return file

    def create_level_card_image(self, user: Union[discord.User, discord.Member], user_config: objects.UserConfig, avatar_bytes: io.BytesIO) -> io.BytesIO:

        buffer = io.BytesIO()
        card_image = random.choice(self.IMAGES['SAI']['level_cards'])

        with Image.open(fp=card_image) as image:

            draw = ImageDraw.Draw(im=image)

            with Image.open(fp=avatar_bytes) as avatar:
                avatar = avatar.resize(size=(256, 256), resample=Image.LANCZOS)
                image.paste(im=avatar, box=(22, 22), mask=avatar.convert('RGBA'))

                colour = ColorThief(file=avatar_bytes).get_color(quality=1)

            # Username

            text = utils.name(person=user)
            font = utils.find_font_size(text=text, font=self.KABEL_BLACK_FONT, size=56, draw=draw, x_bound=690, y_bound=45)
            draw.text(xy=(300, 22 - font.getoffset(text)[1]), text=text, font=font, fill=colour)

            # Level

            text = f'Level: {user_config.level}'
            font = ImageFont.truetype(font=self.KABEL_BLACK_FONT, size=40)
            draw.text(xy=(300, 72 - font.getoffset(text)[1]), text=text, font=font, fill='#1F1E1C')

            # XP

            text = f'XP: {user_config.xp} / {user_config.xp + user_config.next_level_xp}'
            font = ImageFont.truetype(font=self.KABEL_BLACK_FONT, size=40)
            draw.text(xy=(300, 112 - font.getoffset(text)[1]), text=text, font=font, fill='#1F1E1C')

            # XP BAR

            bar_len = 678
            outline = utils.darken_colour(*colour, 0.2)

            draw.rounded_rectangle(xy=((300, 152), (300 + bar_len, 192)), radius=10, outline=outline, fill='#1F1E1C', width=5)

            if user_config.xp > 0:
                filled_len = int(round(bar_len * user_config.xp / float(user_config.xp + user_config.next_level_xp)))
                draw.rounded_rectangle(xy=((300, 152), (300 + filled_len, 192)), radius=10, outline=outline, fill=colour, width=5)

            # Rank

            text = f'#{self.rank(user.id)}'
            font = ImageFont.truetype(self.KABEL_BLACK_FONT, 110)
            draw.text(xy=(300, 202 - font.getoffset(text)[1]), text=text, font=font, fill='#1F1E1C')

            #

            image.save(fp=buffer, format='png')

        buffer.seek(0)
        return buffer
