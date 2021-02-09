import aiohttp
from typing import Dict, Union


async def _json_or_text(request: aiohttp.ClientResponse) -> Union[Dict, str]:

    if request.headers['Content-Type'] == 'application/json; charset=utf-8':
        return await request.json()
    return await request.text()

