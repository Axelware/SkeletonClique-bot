from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING

import discord
import rapidfuzz

from utilities import objects

if TYPE_CHECKING:
    from bot import SemiBotomatic


__log__ = logging.getLogger(__name__)


class TagManager:

    def __init__(self, bot: SemiBotomatic) -> None:
        self.bot = bot

        self.tags: dict[str, objects.Tag] = {}

    async def load(self) -> None:

        tags = await self.bot.db.fetch('SELECT * FROM tags')
        for tag_data in tags:
            self.tags[tag_data['name']] = objects.Tag(data=dict(tag_data))

        __log__.info(f'[TAG MANAGER] Loaded tags. [{len(self.tags)} tags]')
        print(f'[TAG MANAGER] Loaded tags. [{len(self.tags)} tags]')

    #

    def get_tag(self, *, name: str) -> Optional[objects.Tag]:
        return self.tags.get(name)

    def get_tags(self) -> Optional[list[objects.Tag]]:
        return list(self.tags.values())

    def get_tags_matching(self, *, name: str, limit: int = 5) -> Optional[list[objects.Tag]]:
        return [self.tags[tag_name] for tag_name in [match[0] for match in rapidfuzz.process.extract(query=name, choices=self.tags.keys(), limit=limit, processor=lambda s: s)]]

    def get_tags_owned_by(self, member: discord.Member) -> Optional[list[objects.Tag]]:
        return [tag for tag in self.tags.values() if tag.user_id == member.id]

    #

    async def create_tag(self, *, user_id: str, name: str, content: str, jump_url: str = None) -> None:

        tag_data = await self.bot.db.fetchrow(
                'INSERT INTO tags (user_id, name, content, jump_url) VALUES ($1, $2, $3, $4) RETURNING *',
                user_id, name, content, jump_url
        )
        self.tags[tag_data['name']] = objects.Tag(data=tag_data)

    async def create_tag_alias(self, *, user_id: int, alias: str, original: str, jump_url: str = None) -> None:

        tag_data = await self.bot.db.fetchrow(
                'INSERT INTO tags (user_id, name, alias, jump_url) VALUES ($1, $2, $3, $4) RETURNING *',
                user_id, alias, original, jump_url
        )
        self.tags[tag_data['name']] = objects.Tag(data=dict(tag_data))

    async def edit_tag_content(self, *, name: str, content: str, jump_url: str = None) -> None:

        await self.bot.db.execute('UPDATE tags SET content = $1, jump_url = $2 WHERE name = $3', content, jump_url, name)
        self.tags[name].content = content
        if jump_url:
            self.tags[name].jump_url = jump_url

    async def edit_tag_owner(self, *, name: str, user_id: int) -> None:

        await self.bot.db.execute('UPDATE tags SET user_id = $1 WHERE name = $2', user_id, name)
        self.tags[name].user_id = user_id


    async def delete_tag(self, *, name: str) -> None:

        await self.bot.db.execute('DELETE FROM tags WHERE name = $1', name)
        aliases = await self.bot.db.fetch('DELETE FROM tags WHERE alias = $1 RETURNING name', name)

        del self.tags[name]
        for alias in aliases:
            del self.tags[alias['name']]