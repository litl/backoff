import pytest

import backoff

aiohttp = pytest.importorskip("aiohttp")
aiohttp.web = pytest.importorskip("aiohttp.web")
aiohttp.web_exceptions = pytest.importorskip("aiohttp.web_exceptions")


async def test_backoff_on_all_session_requests(aiohttp_client):
    call_count = 0

    async def handler(request):
        nonlocal call_count
        call_count += 1
        raise aiohttp.web_exceptions.HTTPUnauthorized

    app = aiohttp.web.Application()
    app.router.add_get('/', handler)
    client = await aiohttp_client(
        app,
        connector=aiohttp.TCPConnector(limit=1),
        raise_for_status=True,
    )

    # retry every session request
    client._session._request = backoff.on_exception(
        wait_gen=backoff.expo,
        exception=aiohttp.client_exceptions.ClientResponseError,
        max_tries=2,
    )(client._session._request)

    with pytest.raises(aiohttp.client_exceptions.ClientResponseError) as exc:
        await client.get('/')

    assert exc.value.code == 401
    assert call_count == 2
