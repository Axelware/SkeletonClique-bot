from __future__ import annotations

import logging
from typing import Dict, List, Optional, TYPE_CHECKING

import discord
import rapidfuzz

from utilities import objects

if TYPE_CHECKING:
    from bot import SemiBotomatic


__log__ = logging.getLogger(__name__)


class TagManager:

    def __init__(self, bot: SemiBotomatic) -> None:
        self.bot = bot

        self.tags: Dict[str, objects.Tag] = {}

    async def load(self) -> None:

        tags = await self.bot.db.fetch('SELECT * FROM tags')
        for tag_data in tags:
            self.tags[tag_data['name']] = objects.Tag(data=dict(tag_data))

        __log__.info(f'[TAG MANAGER] Loaded tags. [{len(self.tags)} tags]')
        print(f'[TAG MANAGER] Loaded tags. [{len(self.tags)} tags]')

    #

    def get_tag(self, *, name: str) -> Optional[objects.Tag]:
        return self.tags.get(name, None)

    def get_tags(self) -> Optional[List[objects.Tag]]:
        return list(self.tags.values())

    def get_tags_matching(self, *, name: str, limit: int = 5) -> Optional[List[objects.Tag]]:
        return [self.tags[tag_name] for tag_name in [match[0] for match in rapidfuzz.process.extract(query=name, choices=self.tags.keys(), limit=limit)]]

    def get_tags_owned_by(self, member: discord.Member) -> Optional[List[objects.Tag]]:
        return [tag for tag in self.tags.values() if tag.owner_id == member.id]

    #

    async def create_tag(self, *, author: discord.Member, name: str, content: str) -> None:

        tag_data = await self.bot.db.fetchrow('INSERT INTO tags (owner_id, name, content, alias) VALUES ($1, $2, $3, $4) RETURNING *', author.id, name, content, None)
        self.tags[tag_data['name']] = objects.Tag(data=dict(tag_data))

    async def create_tag_alias(self, *, author: discord.Member, alias: str, original: str) -> None:

        tag_data = await self.bot.db.fetchrow('INSERT INTO tags (owner_id, name, content, alias) VALUES ($1, $2, $3, $4) RETURNING *', author.id, alias, None, original)
        self.tags[tag_data['name']] = objects.Tag(data=dict(tag_data))

    async def edit_tag_content(self, *, name: str, new_content: str) -> None:

        await self.bot.db.execute('UPDATE tags SET content = $1 WHERE name = $2', new_content, name)
        self.tags[name].content = new_content

    async def edit_tag_owner(self, *, name: str, new_owner: discord.Member) -> None:

        await self.bot.db.execute('UPDATE tags SET owner_id = $1 WHERE name = $2', new_owner.id, name)
        self.tags[name].owner_id = new_owner.id

    async def delete_tag(self, *, name: str) -> None:

        await self.bot.db.execute('DELETE FROM tags WHERE name = $1', name)
        await self.bot.db.execute('DELETE FROM tags WHERE alias = $1', name)

        del self.tags[name]
