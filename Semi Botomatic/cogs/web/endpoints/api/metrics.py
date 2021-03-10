from __future__ import annotations

import aiohttp.web
import prometheus_client


# noinspection PyUnusedLocal
async def api_metrics_get(request: aiohttp.web.Request) -> aiohttp.web.Response:
    return aiohttp.web.Response(body=prometheus_client.generate_latest(prometheus_client.REGISTRY), headers={'Content-Type': prometheus_client.CONTENT_TYPE_LATEST})


def setup(app: aiohttp.web.Application) -> None:

    app.add_routes([
        aiohttp.web.get(r'/api/metrics', api_metrics_get),
    ])
