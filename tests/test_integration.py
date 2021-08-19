"""Integration tests

Higher-level tests integrating with 3rd party modules using iodiomatic
backoff patterns.
"""

import backoff


import requests
from requests import HTTPError
import responses


@responses.activate
def test_on_predicate_runtime(monkeypatch):

    log = []

    def sleep(seconds):
        log.append(seconds)

    monkeypatch.setattr("time.sleep", sleep)

    url = "http://example.com"

    responses.add(responses.GET, url, status=429, headers={"Retry-After": "1"})
    responses.add(responses.GET, url, status=429, headers={"Retry-After": "3"})
    responses.add(responses.GET, url, status=429, headers={"Retry-After": "7"})
    responses.add(responses.GET, url, status=200)

    @backoff.on_predicate(
        backoff.runtime,
        predicate=lambda r: r.status_code == 429,
        value=lambda r: int(r.headers.get("Retry-After")),
        jitter=None,
    )
    def get_url():
        return requests.get(url)

    resp = get_url()
    assert resp.status_code == 200

    assert log == [1, 3, 7]


@responses.activate
def test_on_exception_runtime(monkeypatch):

    log = []

    def sleep(seconds):
        log.append(seconds)

    monkeypatch.setattr("time.sleep", sleep)

    url = "http://example.com"

    responses.add(responses.GET, url, status=429, headers={"Retry-After": "1"})
    responses.add(responses.GET, url, status=429, headers={"Retry-After": "3"})
    responses.add(responses.GET, url, status=429, headers={"Retry-After": "7"})
    responses.add(responses.GET, url, status=200)

    @backoff.on_exception(
        backoff.runtime,
        HTTPError,
        value=lambda e: int(e.response.headers.get("Retry-After")),
        jitter=None,
    )
    def get_url():
        resp = requests.get(url)
        resp.raise_for_status()
        return resp

    resp = get_url()
    assert resp.status_code == 200

    assert log == [1, 3, 7]
