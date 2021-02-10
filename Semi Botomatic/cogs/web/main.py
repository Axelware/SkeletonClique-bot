from __future__ import annotations

import importlib
import logging
import os
from typing import TYPE_CHECKING

import aiohttp.web
import aiohttp_jinja2
import jinja2

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

    endpoints = ['api.spotify', 'index', 'timezones', 'links']
    for endpoint in [importlib.import_module(f'cogs.web.endpoints.{endpoint}') for endpoint in endpoints]:
        endpoint.setup(app=app)

    app.add_routes([aiohttp.web.static('/static', os.path.abspath(os.path.join(os.path.dirname(__file__), 'static')), show_index=True, follow_symlinks=True)])
    app['static_root_url'] = '/static'

    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))))

    runner = aiohttp.web.AppRunner(app=app)
    await runner.setup()

    site = aiohttp.web.TCPSite(runner, config.WEB_ADDRESS, config.WEB_PORT)
    await site.start()

    return app
