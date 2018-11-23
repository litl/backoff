import asyncio

import aiohttp
import backoff
import pytest


@pytest.mark.asyncio
async def test_client_response_errors():
    statuses = [418, 500, 501]

    backoffs = []
    giveups = []
    successes = []

    @backoff.on_exception(
        backoff.expo,
        aiohttp.client_exceptions.ClientResponseError,
        max_tries=3,
        on_backoff=backoffs.append,
        on_giveup=giveups.append,
        on_success=successes.append,
    )
    async def httpbin_status():
        status = statuses.pop()
        url = "http://httpbin.org/status/{}".format(status)
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(url) as resp:
                await resp

    with pytest.raises(aiohttp.client_exceptions.ClientResponseError):
        await httpbin_status()

    assert len(backoffs) == 2
    assert len(giveups) == 1
    assert len(successes) == 0


@pytest.mark.asyncio
async def test_get():

    backoffs = []
    giveups = []
    successes = []

    @backoff.on_exception(
        backoff.expo,
        aiohttp.client_exceptions.ClientResponseError,
        max_tries=3,
        on_success=successes.append,
        on_backoff=backoffs.append,
        on_giveup=giveups.append,
    )
    async def httpbin_get():
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get("http://httpbin.org/get") as resp:
                data = await resp.json()
                return data

    data = await httpbin_get()

    assert len(backoffs) == 0
    assert len(giveups) == 0
    assert len(successes) == 1
    assert data["headers"]["Host"] == "httpbin.org"
