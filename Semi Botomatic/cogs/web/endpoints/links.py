import aiohttp.web


# noinspection PyUnusedLocal
async def links_discord_redirect(request: aiohttp.web.Request):
    return aiohttp.web.HTTPFound('https://discord.gg/3x3ZZpP')


def setup(app: aiohttp.web.Application) -> None:

    app.add_routes([
        aiohttp.web.get(r'/links/discord', links_discord_redirect),
    ])
