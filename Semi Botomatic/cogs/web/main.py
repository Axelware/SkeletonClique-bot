from __future__ import annotations

import importlib
import logging
from typing import TYPE_CHECKING

import aiohttp.web

import config

if TYPE_CHECKING:
    from bot import SemiBotomatic

__log__ = logging.getLogger(__name__)


class SemiBotomaticWeb(aiohttp.web.Application):

    def __init__(self, bot: SemiBotomatic) -> None:
        super().__init__()

        self.bot = bot
        self.session = aiohttp.ClientSession()


async def load(bot: SemiBotomatic) -> SemiBotomaticWeb:

    app = SemiBotomaticWeb(bot=bot)
    endpoints = ['api.spotify']

    for endpoint in [importlib.import_module(f'cogs.web.endpoints.{endpoint}') for endpoint in endpoints]:
        endpoint.setup(app=app)

    runner = aiohttp.web.AppRunner(app=app)
    await runner.setup()

    site = aiohttp.web.TCPSite(runner, config.WEB_ADDRESS, config.WEB_PORT)
    await site.start()

    return app
