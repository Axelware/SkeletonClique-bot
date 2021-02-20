import logging
from typing import Union

from utilities import enums, objects

__log__ = logging.getLogger(__name__)


class GuildManager:

    def __init__(self, bot) -> None:
        self.bot = bot

        self.default_config = objects.DefaultGuildConfig()
        self.configs = {}

    async def load(self) -> None:

        configs = await self.bot.db.fetch('SELECT * FROM guilds')
        for config in configs:
            self.configs[config['id']] = objects.GuildConfig(data=config)

        __log__.info(f'[GUILD MANAGER] Loaded guild configs. [{len(configs)} guilds]')
        print(f'[GUILD MANAGER] Loaded guild configs. [{len(configs)} guilds]')

        await self.bot.tag_manager.load()

    #

    async def create_config(self, *, guild_id: int) -> objects.GuildConfig:

        data = await self.bot.db.fetchrow('INSERT INTO guilds (id) values ($1) ON CONFLICT (id) DO UPDATE SET id = excluded.id RETURNING *', guild_id)
        self.configs[guild_id] = objects.GuildConfig(data=data)

        __log__.info(f'[GUILD MANAGER] Created config for guild with id \'{guild_id}\'')
        return self.configs[guild_id]

    async def get_or_create_config(self, *, guild_id: int) -> objects.GuildConfig:

        if isinstance(guild_config := self.get_config(guild_id=guild_id), objects.DefaultGuildConfig):
            guild_config = await self.create_config(guild_id=guild_id)

        return guild_config

    def get_config(self, *, guild_id: int) -> Union[objects.DefaultGuildConfig, objects.GuildConfig]:
        return self.configs.get(guild_id, self.default_config)

    #

    async def set_embed_size(self, *, guild_id: int, embed_size: enums.EmbedSize = enums.EmbedSize.LARGE) -> None:

        guild_config = await self.get_or_create_config(guild_id=guild_id)

        data = await self.bot.db.fetchrow('UPDATE guilds SET embed_size = $1 WHERE id = $2 RETURNING embed_size', embed_size.value, guild_id)
        # noinspection PyArgumentList
        guild_config.embed_size = enums.EmbedSize(data['embed_size'])
