# Future
from __future__ import annotations

# Standard Library
from typing import TYPE_CHECKING, Any

# My stuff
from utilities import enums, objects, utils


if TYPE_CHECKING:
    # My stuff
    from core.bot import SkeletonClique


class MemberConfig:

    def __init__(self, bot: SkeletonClique, user_config: objects.UserConfig, data: dict[str, Any]) -> None:
        self._bot = bot
        self._user_config = user_config

        self._id: int = data["id"]
        self._user_id: int = data["user_id"]
        self._guild_id: int = data["guild_id"]

        self._xp: int = data["xp"]
        self._coins: int = data["coins"]

    def __repr__(self) -> str:
        return "<UserEconomy>"

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
    def guild_id(self) -> int:
        return self._guild_id

    @property
    def xp(self) -> int:
        return self._xp

    @property
    def coins(self) -> int:
        return self._coins

    #

    @property
    def level(self) -> int:
        return utils.level(self.xp)

    @property
    def needed_xp(self) -> int:
        return utils.needed_xp(self.level, self.xp)

    # Config

    async def change_coins(self, coins: int, *, operation: enums.Operation) -> None:

        if operation == enums.Operation.SET:
            self._coins = coins
        elif operation == enums.Operation.ADD:
            self._coins += coins
        elif operation == enums.Operation.MINUS:
            self._coins -= coins
        else:
            raise ValueError(f"'change_coins' expected one of {enums.Operation.SET, enums.Operation.ADD, enums.Operation.MINUS}, got '{operation!r}'.")

        await self.bot.db.execute("UPDATE members SET coins = $1 WHERE user_id = $2 AND guild_id = $3", self.coins, self.user_id, self.guild_id)

    async def change_xp(self, xp: int, *, operation: enums.Operation) -> None:

        if operation == enums.Operation.SET:
            self._xp = xp
        elif operation == enums.Operation.ADD:
            self._xp += xp
        elif operation == enums.Operation.MINUS:
            self._xp -= xp
        else:
            raise ValueError(f"'change_xp' expected one of {enums.Operation.SET, enums.Operation.ADD, enums.Operation.MINUS}, got '{operation!r}'.")

        await self.bot.db.execute("UPDATE members SET xp = $1 WHERE user_id = $2 AND guild_id = $3", self.xp, self.user_id, self.guild_id)
