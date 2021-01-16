from __future__ import annotations

from typing import Any, List, TYPE_CHECKING, Union

import slate

if TYPE_CHECKING:
    from cogs.voice.custom.player import Player


class Queue(slate.Queue):

    def __init__(self, player: Player) -> None:
        super().__init__()

        self.player: Player = player

    def put(self, *, items: Union[List[Any], Any], position: int = None) -> None:
        super().put(items=items, position=position)

        self.player.queue_add_event.set()
        self.player.queue_add_event.clear()
