import aiohttp.web
import aiohttp_jinja2
import pendulum


# noinspection PyUnusedLocal
@aiohttp_jinja2.template('timezones.html')
async def timezones_get(request: aiohttp.web.Request):
    return {'timezones': pendulum.timezones}


def setup(app: aiohttp.web.Application) -> None:

    app.add_routes([
        aiohttp.web.get(r'/timezones', timezones_get),
    ])
