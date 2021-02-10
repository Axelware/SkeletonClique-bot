import aiohttp.web
import aiohttp_jinja2


@aiohttp_jinja2.template('index.html')
async def index_get(request: aiohttp.web.Request):
    return None


def setup(app: aiohttp.web.Application) -> None:

    app.add_routes([
        aiohttp.web.get(r'/', index_get),
    ])
