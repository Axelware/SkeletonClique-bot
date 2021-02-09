import aiohttp.web
import aiohttp_jinja2


class Index:

    @aiohttp_jinja2.template('index.html')
    async def get(self, request: aiohttp.web.Request):
        return None


def setup(app: aiohttp.web.Application) -> None:

    index = Index()

    app.add_routes([
        aiohttp.web.get(r'/', index.get),
    ])
