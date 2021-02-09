import pendulum
import aiohttp.web
import aiohttp_jinja2


class Timezones:

    @aiohttp_jinja2.template('timezones.html')
    async def get(self, request: aiohttp.web.Request):
        return {'timezones': pendulum.timezones}


def setup(app: aiohttp.web.Application) -> None:

    timezones = Timezones()

    app.add_routes([
        aiohttp.web.get(r'/timezones', timezones.get),
    ])
