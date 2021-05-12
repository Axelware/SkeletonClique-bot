from __future__ import annotations

import io
import logging
import math
import os
import pathlib
import random
from typing import Literal, TYPE_CHECKING, Union

import discord
from PIL import Image, ImageDraw, ImageFont
from colorthief import ColorThief
from discord.ext import tasks

from utilities import exceptions, objects, utils

if TYPE_CHECKING:
    from bot import SemiBotomatic


__log__ = logging.getLogger('utilities.managers.users')

IMAGES = {
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

ARIAL_FONT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../resources/fonts/arial.ttf'))
KABEL_BLACK_FONT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../resources/fonts/kabel_black.otf'))


class UserManager:

    def __init__(self, bot: SemiBotomatic) -> None:
        self.bot = bot

        self.default_config = objects.UserConfig(bot=self.bot, data={})
        self.configs: dict[int, objects.UserConfig] = {}

    async def load(self) -> None:

        configs = await self.bot.db.fetch('SELECT * FROM users')

        for config in configs:
            self.configs[config['id']] = objects.UserConfig(bot=self.bot, data=config)

        __log__.info(f'[USER MANAGER] Loaded user configs. [{len(configs)} users]')
        print(f'[USER MANAGER] Loaded user configs. [{len(configs)} users]')

        await self.load_notifications()
        await self.load_reminders()
        await self.load_todos()

        self.update_database_task.start()

    async def load_notifications(self) -> None:

        notifications = await self.bot.db.fetch('SELECT * FROM notifications')

        for notification in notifications:
            user_config = self.get_config(notification['user_id'])
            user_config._notifications = objects.Notifications(bot=self.bot, user_config=user_config, data=notification)

    async def load_reminders(self) -> None:

        reminders = await self.bot.db.fetch('SELECT * FROM reminders')

        for reminder in reminders:
            user_config = self.get_config(reminder['user_id'])

            reminder = objects.Reminder(bot=self.bot, user_config=user_config, data=reminder)
            if not reminder.done:
                reminder.schedule()

            user_config._reminders[reminder.id] = reminder

        __log__.info(f'[USER MANAGER] Loaded reminders. [{len(reminders)} reminders]')
        print(f'[USER MANAGER] Loaded reminders. [{len(reminders)} reminders]')

    async def load_todos(self) -> None:

        todos = await self.bot.db.fetch('SELECT * FROM todos')

        for todo in todos:
            user_config = self.get_config(todo['user_id'])
            todo = objects.Todo(bot=self.bot, user_config=user_config, data=todo)
            user_config._todos[todo.id] = todo

        __log__.info(f'[USER MANAGER] Loaded todos. [{len(todos)} todos]')
        print(f'[USER MANAGER] Loaded todos. [{len(todos)} todos]')

    # Background task

    @tasks.loop(seconds=60)
    async def update_database_task(self) -> None:

        async with self.bot.db.acquire(timeout=300) as db:

            requires_updating = {user_id: user_config for user_id, user_config in self.configs.items() if len(user_config._requires_db_update) >= 1}
            for user_id, user_config in requires_updating.items():

                query = ','.join(f'{editable.value} = ${index + 2}' for index, editable in enumerate(user_config._requires_db_update))
                args = [getattr(user_config, attribute.value) for attribute in user_config._requires_db_update]
                await db.execute(f'UPDATE users SET {query} WHERE id = $1', user_id, *args)

                user_config._requires_db_update = set()

    # Config management

    async def create_config(self, user_id: int) -> objects.UserConfig:

        data = await self.bot.db.fetchrow('INSERT INTO users (id) values ($1) ON CONFLICT (id) DO UPDATE SET id = excluded.id RETURNING *', user_id)
        notifications = await self.bot.db.fetchrow('INSERT INTO notifications (user_id) values ($1) ON CONFLICT (id) DO UPDATE SET id = excluded.user_id RETURNING *', user_id)

        user_config = objects.UserConfig(bot=self.bot, data=data)
        user_config._notifications = objects.Notifications(bot=self.bot, user_config=user_config, data=notifications)

        self.configs[user_config.id] = user_config

        __log__.info(f'[USER MANAGER] Created config for user with id \'{user_config.id}\'.')
        return user_config

    def get_config(self, user_id: int) -> objects.UserConfig:
        return self.configs.get(user_id, self.default_config)

    async def delete_config(self, user_id: int) -> None:

        if not (config := self.get_config(user_id)):
            return

        await config.delete()

    # Ranking

    def leaderboard(self, leaderboard_type: Literal['level', 'xp', 'coins'] = 'xp', *, guild_id: int = None) -> list[objects.UserConfig]:

        if not (guild := self.bot.get_guild(guild_id)) and guild_id:
            raise ValueError(f'guild with id \'{guild_id}\' was not found.')

        return sorted(
                filter(
                        lambda user_config: (self.bot.get_user(user_config.id) if not guild else guild.get_member(user_config.id)) is not None
                                            and getattr(user_config, leaderboard_type) != 0,
                        self.configs.values()
                ),
                key=lambda user_config: getattr(user_config, leaderboard_type), reverse=True
        )

    def rank(self, user_id: int, *, guild_id: int = None) -> int:

        if not (guild := self.bot.get_guild(guild_id)) and guild_id:
            raise ValueError(f'guild with id \'{guild_id}\' was not found.')

        configs = sorted(
                filter(lambda user_config: (self.bot.get_user(user_config.id) if not guild else guild.get_member(user_config.id)) and user_config.xp != 0, self.configs.values()),
                key=lambda user_config: user_config.xp, reverse=True
        )

        try:
            return configs.index(self.get_config(user_id)) + 1
        except ValueError:
            raise exceptions.ArgumentError('That user does not have any XP yet, so they have not been ranked.')

    # Level image

    async def create_level_card(self, user_id: int, *, guild_id: int = None) -> discord.File:

        if not (guild := self.bot.get_guild(guild_id)) and guild_id:
            raise ValueError(f'guild with id \'{guild_id}\' was not found.')

        user = self.bot.get_user(user_id) if not guild else guild.get_member(user_id)
        user_config = self.get_config(user_id)

        avatar_bytes = io.BytesIO(await user.avatar_url_as(format='png', size=512).read())
        buffer = await self.bot.loop.run_in_executor(None, self.create_level_card_image, (user, user_config, avatar_bytes), guild)

        file = discord.File(fp=buffer, filename='level.png')

        avatar_bytes.close()
        buffer.close()

        return file

    def create_level_card_image(self, data: tuple[Union[discord.User, discord.Member], objects.UserConfig, io.BytesIO], guild: discord.Guild = None) -> io.BytesIO:

        user, user_config, user_avatar_bytes = data

        buffer = io.BytesIO()

        with Image.open(random.choice(IMAGES['SAI']['level_cards'])) as image:

            draw = ImageDraw.Draw(image)

            with Image.open(user_avatar_bytes) as avatar:

                avatar = avatar.resize((256, 256), resample=Image.LANCZOS) if avatar.size != (256, 256) else avatar
                image.paste(avatar, (22, 22), avatar.convert('RGBA'))

                colour = ColorThief(user_avatar_bytes).get_color(quality=1)

            # Username

            name_text = getattr(user, 'nick', None) or user.name
            name_fontsize = 56
            name_font = ImageFont.truetype(KABEL_BLACK_FONT, name_fontsize)

            while draw.textsize(name_text, font=name_font) > (690, 45):
                name_fontsize -= 1
                name_font = ImageFont.truetype(KABEL_BLACK_FONT, name_fontsize)

            draw.text((300, 22 - name_font.getoffset(name_text)[1]), name_text, font=name_font, fill=colour)

            # Level

            level_text = f'Level: {user_config.level}'
            level_font = ImageFont.truetype(KABEL_BLACK_FONT, 40)

            draw.text((300, 72 - level_font.getoffset(level_text)[1]), level_text, font=level_font, fill='#1F1E1C')

            # XP

            xp_text = f'XP: {user_config.xp} / {user_config.xp + user_config.next_level_xp}'
            xp_font = ImageFont.truetype(KABEL_BLACK_FONT, 40)

            draw.text((300, 112 - xp_font.getoffset(xp_text)[1]), xp_text, font=xp_font, fill='#1F1E1C')

            # XP BAR

            bar_len = 678
            outline = utils.darken_colour(*colour, 0.2)

            draw.rounded_rectangle(((300, 152), (300 + bar_len, 192)), radius=10, outline=outline, fill='#1F1E1C', width=5)

            if user_config.xp > 0:
                filled_len = int(round(bar_len * user_config.xp / float(user_config.xp + user_config.next_level_xp)))
                draw.rounded_rectangle(((300, 152), (300 + filled_len, 192)), radius=10, outline=outline, fill=colour, width=5)

            # Rank

            rank_text = f'#{self.rank(user.id, guild_id=getattr(guild, "id", None))}'
            rank_font = ImageFont.truetype(KABEL_BLACK_FONT, 110)

            draw.text((300, 202 - rank_font.getoffset(rank_text)[1]), rank_text, font=rank_font, fill='#1F1E1C')

            #

            image.save(buffer, 'png')

        buffer.seek(0)
        return buffer

    # Leaderboard image

    async def create_leaderboard(self, page: int = 1, *, guild_id: int = None) -> discord.File:

        if not (guild := self.bot.get_guild(guild_id)) and guild_id:
            raise ValueError(f'guild with id \'{guild_id}\' was not found.')

        leaderboard = self.leaderboard(guild_id=guild.id if guild else None)
        data = []

        for user_config in [leaderboard[index:index + 10] for index in range(0, len(leaderboard), 10)][page - 1]:

            user = guild.get_member(user_config.id) if guild else self.bot.get_user(user_config.id)
            avatar_bytes = io.BytesIO(await user.avatar_url_as(format='png', size=256).read())

            data.append((user, user_config, avatar_bytes))

        buffer = await self.bot.loop.run_in_executor(None, self.create_leaderboard_image, data, guild)
        file = discord.File(fp=buffer, filename='level.png')

        for _, _, avatar_bytes in data:
            avatar_bytes.close()
        buffer.close()

        return file

    def create_leaderboard_image(self, data: list[tuple[Union[discord.User, discord.Member], objects.UserConfig, io.BytesIO]], guild: discord.Guild = None) -> io.BytesIO:

        buffer = io.BytesIO()
        leaderboard_image = random.choice(IMAGES['SAI']['leaderboard'])

        with Image.open(leaderboard_image) as image:
            draw = ImageDraw.Draw(image)

            # Title

            title_text = f'XP Leaderboard:'
            title_font = ImageFont.truetype(font=KABEL_BLACK_FONT, size=93)
            draw.text(xy=(10, 10 - title_font.getoffset(title_text)[1]), text=title_text, font=title_font, fill='#1F1E1C')

            # Actual content

            y = 100

            for user, user_config, user_avatar_bytes in data:

                # Avatar

                with Image.open(user_avatar_bytes) as avatar:
                    avatar = avatar.resize((80, 80), resample=Image.LANCZOS)
                    image.paste(avatar, (10, y), avatar.convert('RGBA'))

                # Username

                name_text = f'{getattr(user, "nick", None) or user.name}'
                name_fontsize = 45
                name_font = ImageFont.truetype(font=KABEL_BLACK_FONT, size=name_fontsize)

                while draw.textsize(text=name_text, font=name_font) > (600, 30):
                    name_fontsize -= 1
                    name_font = ImageFont.truetype(font=KABEL_BLACK_FONT, size=name_fontsize)

                draw.text(xy=(100, y - name_font.getoffset(name_text)[1]), text=name_text, font=name_font, fill='#1F1E1C')

                #

                y += 45

                # Rank

                rank_text = f'#{self.rank(user.id, guild_id=getattr(guild, "id", None))}'
                rank_fontsize = 40
                rank_font = ImageFont.truetype(font=KABEL_BLACK_FONT, size=rank_fontsize)

                while draw.textsize(text=rank_text, font=rank_font) > (600, 30):
                    rank_fontsize -= 1
                    rank_font = ImageFont.truetype(font=KABEL_BLACK_FONT, size=rank_fontsize)

                draw.text(xy=(100, y - rank_font.getoffset(rank_text)[1]), text=rank_text, font=rank_font, fill='#1F1E1C')

                # Xp

                xp_text = f'XP: {user_config.xp}/{user_config.xp + user_config.next_level_xp}'
                xp_fontsize = 40
                xp_font = ImageFont.truetype(font=KABEL_BLACK_FONT, size=xp_fontsize)

                while draw.textsize(text=xp_text, font=xp_font) > (320, 30):
                    xp_fontsize -= 1
                    xp_font = ImageFont.truetype(font=KABEL_BLACK_FONT, size=xp_fontsize)

                draw.text(xy=(220, y - xp_font.getoffset(xp_text)[1]), text=xp_text, font=xp_font, fill='#1F1E1C')

                # Level

                level_text = f'Level: {user_config.level}'
                level_fontsize = 40
                level_font = ImageFont.truetype(font=KABEL_BLACK_FONT, size=level_fontsize)

                while draw.textsize(text=level_text, font=level_font) > (150, 30):
                    level_fontsize -= 1
                    level_font = ImageFont.truetype(font=KABEL_BLACK_FONT, size=level_fontsize)

                draw.text(xy=(545, y - level_font.getoffset(xp_text)[1]), text=level_text, font=level_font, fill='#1F1E1C')

                #

                y += 45

            image.save(buffer, 'png')

        buffer.seek(0)
        return buffer

    # Timecard image

    async def create_timecard(self, *, guild_id: int = None) -> discord.File:

        if not (guild := self.bot.get_guild(guild_id)) and guild_id:
            raise ValueError(f'guild with id \'{guild_id}\' was not found.')

        configs = sorted(
                filter(
                        lambda user_config: (self.bot.get_user(user_config.id) if not guild else guild.get_member(user_config.id)) is not None
                                            and not user_config.timezone_private and user_config.timezone is not None, self.bot.user_manager.configs.values()),
                key=lambda user_config: user_config.time.offset_hours
        )
        if not configs:
            raise exceptions.ArgumentError('There are no users who have set their timezone, or everyone has set them to be private.')

        timezone_avatars = {}

        for config in configs:

            avatar_bytes = io.BytesIO(await self.bot.get_user(config.id).avatar_url_as(format='png', size=256).read())
            timezone = config.time.format('HH:mm (ZZ)')

            if users := timezone_avatars.get(timezone, []):
                if len(users) > 36:
                    break
                timezone_avatars[timezone].append(avatar_bytes)
            else:
                timezone_avatars[timezone] = [avatar_bytes]

        buffer = await self.bot.loop.run_in_executor(None, self.create_timecard_image, timezone_avatars)
        file = discord.File(fp=buffer, filename='level.png')

        buffer.close()
        for avatar_bytes in timezone_avatars.values():
            [buffer.close() for buffer in avatar_bytes]

        return file

    @staticmethod
    def create_timecard_image(data: dict[str, io.BytesIO]) -> io.BytesIO:

        buffer = io.BytesIO()
        width_x, height_y = (1600 * (len(data) if len(data) < 5 else 5)) + 100, (1800 * math.ceil(len(data) / 5)) + 100

        with Image.new(mode='RGBA', size=(width_x, height_y), color='#F1C30F') as image:

            draw = ImageDraw.Draw(im=image)
            font = ImageFont.truetype(font=ARIAL_FONT, size=120)

            x, y = 100, 100

            for timezone, avatars in data.items():

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
