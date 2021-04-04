import aiohttp
from typing import Union


async def _json_or_text(request: aiohttp.ClientResponse) -> Union[dict, str]:

    if request.headers['Content-Type'] == 'application/json; charset=utf-8':
        return await request.json()
    return await request.text()

