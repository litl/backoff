import backoff
import requests
import pytest


def test_client_response_errors():
    statuses = [418, 500, 501]

    backoffs = []
    giveups = []
    successes = []

    @backoff.on_exception(
        backoff.expo,
        requests.exceptions.RequestException,
        max_tries=3,
        on_backoff=backoffs.append,
        on_giveup=giveups.append,
        on_success=successes.append,
    )
    def httpbin_status():
        status = statuses.pop()
        url = "http://httpbin.org/status/{}".format(status)
        resp = requests.get(url)
        resp.raise_for_status()

    with pytest.raises(requests.exceptions.RequestException):
        httpbin_status()

    assert len(backoffs) == 2
    assert len(giveups) == 1
    assert len(successes) == 0


def test_get():

    backoffs = []
    giveups = []
    successes = []

    @backoff.on_exception(
        backoff.expo,
        requests.exceptions.RequestException,
        max_tries=3,
        on_success=successes.append,
        on_backoff=backoffs.append,
        on_giveup=giveups.append,
    )
    def httpbin_get():
        resp = requests.get("http://httpbin.org/get")
        resp.raise_for_status()
        return resp.json()

    data = httpbin_get()

    assert len(backoffs) == 0
    assert len(giveups) == 0
    assert len(successes) == 1
    assert data["headers"]["Host"] == "httpbin.org"
