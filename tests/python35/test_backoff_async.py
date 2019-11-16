# coding:utf-8

import asyncio  # Python 3.5 code and syntax is allowed in this file
import backoff
import pytest
import random

from tests.common import _log_hdlrs, _save_target


async def _await_none(x):
    return None


@pytest.mark.asyncio
async def test_on_predicate(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', _await_none)

    @backoff.on_predicate(backoff.expo)
    async def return_true(log, n):
        val = (len(log) == n - 1)
        log.append(val)
        return val

    log = []
    ret = await return_true(log, 3)
    assert ret is True
    assert 3 == len(log)


@pytest.mark.asyncio
async def test_on_predicate_max_tries(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', _await_none)

    @backoff.on_predicate(backoff.expo, jitter=None, max_tries=3)
    async def return_true(log, n):
        val = (len(log) == n)
        log.append(val)
        return val

    log = []
    ret = await return_true(log, 10)
    assert ret is False
    assert 3 == len(log)


@pytest.mark.asyncio
async def test_on_exception(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', _await_none)

    @backoff.on_exception(backoff.expo, KeyError)
    async def keyerror_then_true(log, n):
        if len(log) == n:
            return True
        e = KeyError()
        log.append(e)
        raise e

    log = []
    assert (await keyerror_then_true(log, 3)) is True
    assert 3 == len(log)


@pytest.mark.asyncio
async def test_on_exception_tuple(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', _await_none)

    @backoff.on_exception(backoff.expo, (KeyError, ValueError))
    async def keyerror_valueerror_then_true(log):
        if len(log) == 2:
            return True
        if len(log) == 0:
            e = KeyError()
        if len(log) == 1:
            e = ValueError()
        log.append(e)
        raise e

    log = []
    assert (await keyerror_valueerror_then_true(log)) is True
    assert 2 == len(log)
    assert isinstance(log[0], KeyError)
    assert isinstance(log[1], ValueError)


@pytest.mark.asyncio
async def test_on_exception_max_tries(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', _await_none)

    @backoff.on_exception(backoff.expo, KeyError, jitter=None, max_tries=3)
    async def keyerror_then_true(log, n, foo=None):
        if len(log) == n:
            return True
        e = KeyError()
        log.append(e)
        raise e

    log = []
    with pytest.raises(KeyError):
        await keyerror_then_true(log, 10, foo="bar")

    assert 3 == len(log)


@pytest.mark.asyncio
async def test_on_exception_constant_iterable(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', _await_none)

    backoffs = []
    giveups = []
    successes = []

    @backoff.on_exception(
        backoff.constant,
        KeyError,
        interval=(1, 2, 3),
        on_backoff=backoffs.append,
        on_giveup=giveups.append,
        on_success=successes.append,
    )
    async def endless_exceptions():
        raise KeyError('foo')

    with pytest.raises(KeyError):
        await endless_exceptions()

    assert len(backoffs) == 3
    assert len(giveups) == 1
    assert len(successes) == 0


@pytest.mark.asyncio
async def test_on_exception_success_random_jitter(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', _await_none)

    log, log_success, log_backoff, log_giveup = _log_hdlrs()

    @backoff.on_exception(backoff.expo,
                          Exception,
                          on_success=log_success,
                          on_backoff=log_backoff,
                          on_giveup=log_giveup,
                          jitter=backoff.random_jitter,
                          factor=0.5)
    @_save_target
    async def succeeder(*args, **kwargs):
        # succeed after we've backed off twice
        if len(log['backoff']) < 2:
            raise ValueError("catch me")

    await succeeder(1, 2, 3, foo=1, bar=2)

    # we try 3 times, backing off twice before succeeding
    assert len(log['success']) == 1
    assert len(log['backoff']) == 2
    assert len(log['giveup']) == 0

    for i in range(2):
        details = log['backoff'][i]
        assert details['wait'] >= 0.5 * 2 ** i


@pytest.mark.asyncio
async def test_on_exception_success_full_jitter(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', _await_none)

    log, log_success, log_backoff, log_giveup = _log_hdlrs()

    @backoff.on_exception(backoff.expo,
                          Exception,
                          on_success=log_success,
                          on_backoff=log_backoff,
                          on_giveup=log_giveup,
                          jitter=backoff.full_jitter,
                          factor=0.5)
    @_save_target
    async def succeeder(*args, **kwargs):
        # succeed after we've backed off twice
        if len(log['backoff']) < 2:
            raise ValueError("catch me")

    await succeeder(1, 2, 3, foo=1, bar=2)

    # we try 3 times, backing off twice before succeeding
    assert len(log['success']) == 1
    assert len(log['backoff']) == 2
    assert len(log['giveup']) == 0

    for i in range(2):
        details = log['backoff'][i]
        assert details['wait'] <= 0.5 * 2 ** i


@pytest.mark.asyncio
async def test_on_exception_success():
    log, log_success, log_backoff, log_giveup = _log_hdlrs()

    @backoff.on_exception(backoff.constant,
                          Exception,
                          on_success=log_success,
                          on_backoff=log_backoff,
                          on_giveup=log_giveup,
                          jitter=None,
                          interval=0)
    @_save_target
    async def succeeder(*args, **kwargs):
        # succeed after we've backed off twice
        if len(log['backoff']) < 2:
            raise ValueError("catch me")

    await succeeder(1, 2, 3, foo=1, bar=2)

    # we try 3 times, backing off twice before succeeding
    assert len(log['success']) == 1
    assert len(log['backoff']) == 2
    assert len(log['giveup']) == 0

    for i in range(2):
        details = log['backoff'][i]
        elapsed = details.pop('elapsed')
        assert isinstance(elapsed, float)
        assert details == {'args': (1, 2, 3),
                           'kwargs': {'foo': 1, 'bar': 2},
                           'target': succeeder._target,
                           'tries': i + 1,
                           'wait': 0}

    details = log['success'][0]
    elapsed = details.pop('elapsed')
    assert isinstance(elapsed, float)
    assert details == {'args': (1, 2, 3),
                       'kwargs': {'foo': 1, 'bar': 2},
                       'target': succeeder._target,
                       'tries': 3}


@pytest.mark.asyncio
async def test_on_exception_giveup():
    log, log_success, log_backoff, log_giveup = _log_hdlrs()

    @backoff.on_exception(backoff.constant,
                          ValueError,
                          on_success=log_success,
                          on_backoff=log_backoff,
                          on_giveup=log_giveup,
                          max_tries=3,
                          jitter=None,
                          interval=0)
    @_save_target
    async def exceptor(*args, **kwargs):
        raise ValueError("catch me")

    with pytest.raises(ValueError):
        await exceptor(1, 2, 3, foo=1, bar=2)

    # we try 3 times, backing off twice and giving up once
    assert len(log['success']) == 0
    assert len(log['backoff']) == 2
    assert len(log['giveup']) == 1

    details = log['giveup'][0]
    elapsed = details.pop('elapsed')
    assert isinstance(elapsed, float)
    assert details == {'args': (1, 2, 3),
                       'kwargs': {'foo': 1, 'bar': 2},
                       'target': exceptor._target,
                       'tries': 3}


@pytest.mark.asyncio
async def test_on_exception_giveup_predicate(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', _await_none)

    def on_baz(e):
        return str(e) == "baz"

    vals = ["baz", "bar", "foo"]

    @backoff.on_exception(backoff.constant,
                          ValueError,
                          giveup=on_baz)
    async def foo_bar_baz():
        raise ValueError(vals.pop())

    with pytest.raises(ValueError):
        await foo_bar_baz()

    assert not vals


@pytest.mark.asyncio
async def test_on_exception_giveup_coro(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', _await_none)

    async def on_baz(e):
        return str(e) == "baz"

    vals = ["baz", "bar", "foo"]

    @backoff.on_exception(backoff.constant,
                          ValueError,
                          giveup=on_baz)
    async def foo_bar_baz():
        raise ValueError(vals.pop())

    with pytest.raises(ValueError):
        await foo_bar_baz()

    assert not vals


@pytest.mark.asyncio
async def test_on_predicate_success():
    log, log_success, log_backoff, log_giveup = _log_hdlrs()

    @backoff.on_predicate(backoff.constant,
                          on_success=log_success,
                          on_backoff=log_backoff,
                          on_giveup=log_giveup,
                          jitter=None,
                          interval=0)
    @_save_target
    async def success(*args, **kwargs):
        # succeed after we've backed off twice
        return len(log['backoff']) == 2

    await success(1, 2, 3, foo=1, bar=2)

    # we try 3 times, backing off twice before succeeding
    assert len(log['success']) == 1
    assert len(log['backoff']) == 2
    assert len(log['giveup']) == 0

    for i in range(2):
        details = log['backoff'][i]
        elapsed = details.pop('elapsed')
        assert isinstance(elapsed, float)
        assert details == {'args': (1, 2, 3),
                           'kwargs': {'foo': 1, 'bar': 2},
                           'target': success._target,
                           'tries': i + 1,
                           'value': False,
                           'wait': 0}

    details = log['success'][0]
    elapsed = details.pop('elapsed')
    assert isinstance(elapsed, float)
    assert details == {'args': (1, 2, 3),
                       'kwargs': {'foo': 1, 'bar': 2},
                       'target': success._target,
                       'tries': 3,
                       'value': True}


@pytest.mark.asyncio
async def test_on_predicate_giveup():
    log, log_success, log_backoff, log_giveup = _log_hdlrs()

    @backoff.on_predicate(backoff.constant,
                          on_success=log_success,
                          on_backoff=log_backoff,
                          on_giveup=log_giveup,
                          max_tries=3,
                          jitter=None,
                          interval=0)
    @_save_target
    async def emptiness(*args, **kwargs):
        pass

    await emptiness(1, 2, 3, foo=1, bar=2)

    # we try 3 times, backing off twice and giving up once
    assert len(log['success']) == 0
    assert len(log['backoff']) == 2
    assert len(log['giveup']) == 1

    details = log['giveup'][0]
    elapsed = details.pop('elapsed')
    assert isinstance(elapsed, float)
    assert details == {'args': (1, 2, 3),
                       'kwargs': {'foo': 1, 'bar': 2},
                       'target': emptiness._target,
                       'tries': 3,
                       'value': None}


@pytest.mark.asyncio
async def test_on_predicate_iterable_handlers():
    hdlrs = [_log_hdlrs() for _ in range(3)]

    @backoff.on_predicate(backoff.constant,
                          on_success=(h[1] for h in hdlrs),
                          on_backoff=(h[2] for h in hdlrs),
                          on_giveup=(h[3] for h in hdlrs),
                          max_tries=3,
                          jitter=None,
                          interval=0)
    @_save_target
    async def emptiness(*args, **kwargs):
        pass

    await emptiness(1, 2, 3, foo=1, bar=2)

    for i in range(3):
        assert len(hdlrs[i][0]['success']) == 0
        assert len(hdlrs[i][0]['backoff']) == 2
        assert len(hdlrs[i][0]['giveup']) == 1

        details = dict(hdlrs[i][0]['giveup'][0])
        elapsed = details.pop('elapsed')
        assert isinstance(elapsed, float)
        assert details == {'args': (1, 2, 3),
                           'kwargs': {'foo': 1, 'bar': 2},
                           'target': emptiness._target,
                           'tries': 3,
                           'value': None}


@pytest.mark.asyncio
async def test_on_predicate_constant_iterable(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', _await_none)

    waits = [1, 2, 3, 6, 9]
    backoffs = []
    giveups = []
    successes = []

    @backoff.on_predicate(
        backoff.constant,
        interval=waits,
        on_backoff=backoffs.append,
        on_giveup=giveups.append,
        on_success=successes.append,
        jitter=None,
    )
    async def falsey():
        return False

    assert not await falsey()

    assert len(backoffs) == len(waits)
    for i, wait in enumerate(waits):
        assert backoffs[i]['wait'] == wait

    assert len(giveups) == 1
    assert len(successes) == 0


# To maintain backward compatibility,
# on_predicate should support 0-argument jitter function.
@pytest.mark.asyncio
async def test_on_exception_success_0_arg_jitter(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', _await_none)
    monkeypatch.setattr('random.random', lambda: 0)

    log, log_success, log_backoff, log_giveup = _log_hdlrs()

    @backoff.on_exception(backoff.constant,
                          Exception,
                          on_success=log_success,
                          on_backoff=log_backoff,
                          on_giveup=log_giveup,
                          jitter=random.random,
                          interval=0)
    @_save_target
    async def succeeder(*args, **kwargs):
        # succeed after we've backed off twice
        if len(log['backoff']) < 2:
            raise ValueError("catch me")

    with pytest.deprecated_call():
        await succeeder(1, 2, 3, foo=1, bar=2)

    # we try 3 times, backing off twice before succeeding
    assert len(log['success']) == 1
    assert len(log['backoff']) == 2
    assert len(log['giveup']) == 0

    for i in range(2):
        details = log['backoff'][i]
        elapsed = details.pop('elapsed')
        assert isinstance(elapsed, float)
        assert details == {'args': (1, 2, 3),
                           'kwargs': {'foo': 1, 'bar': 2},
                           'target': succeeder._target,
                           'tries': i + 1,
                           'wait': 0}

    details = log['success'][0]
    elapsed = details.pop('elapsed')
    assert isinstance(elapsed, float)
    assert details == {'args': (1, 2, 3),
                       'kwargs': {'foo': 1, 'bar': 2},
                       'target': succeeder._target,
                       'tries': 3}


# To maintain backward compatibility,
# on_predicate should support 0-argument jitter function.
@pytest.mark.asyncio
async def test_on_predicate_success_0_arg_jitter(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', _await_none)
    monkeypatch.setattr('random.random', lambda: 0)

    log, log_success, log_backoff, log_giveup = _log_hdlrs()

    @backoff.on_predicate(backoff.constant,
                          on_success=log_success,
                          on_backoff=log_backoff,
                          on_giveup=log_giveup,
                          jitter=random.random,
                          interval=0)
    @_save_target
    async def success(*args, **kwargs):
        # succeed after we've backed off twice
        return len(log['backoff']) == 2

    with pytest.deprecated_call():
        await success(1, 2, 3, foo=1, bar=2)

    # we try 3 times, backing off twice before succeeding
    assert len(log['success']) == 1
    assert len(log['backoff']) == 2
    assert len(log['giveup']) == 0

    for i in range(2):
        details = log['backoff'][i]
        elapsed = details.pop('elapsed')
        assert isinstance(elapsed, float)
        assert details == {'args': (1, 2, 3),
                           'kwargs': {'foo': 1, 'bar': 2},
                           'target': success._target,
                           'tries': i + 1,
                           'value': False,
                           'wait': 0}

    details = log['success'][0]
    elapsed = details.pop('elapsed')
    assert isinstance(elapsed, float)
    assert details == {'args': (1, 2, 3),
                       'kwargs': {'foo': 1, 'bar': 2},
                       'target': success._target,
                       'tries': 3,
                       'value': True}


@pytest.mark.asyncio
async def test_on_exception_callable_max_tries(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', _await_none)

    def lookup_max_tries():
        return 3

    log = []

    @backoff.on_exception(backoff.constant,
                          ValueError,
                          max_tries=lookup_max_tries)
    async def exceptor():
        log.append(True)
        raise ValueError()

    with pytest.raises(ValueError):
        await exceptor()

    assert len(log) == 3


@pytest.mark.asyncio
async def test_on_exception_callable_gen_kwargs():

    def lookup_foo():
        return "foo"

    def wait_gen(foo=None, bar=None):
        assert foo == "foo"
        assert bar == "bar"

        while True:
            yield 0

    @backoff.on_exception(wait_gen,
                          ValueError,
                          max_tries=2,
                          foo=lookup_foo,
                          bar="bar")
    async def exceptor():
        raise ValueError("aah")

    with pytest.raises(ValueError):
        await exceptor()


@pytest.mark.asyncio
async def test_on_exception_coro_cancelling(event_loop):
    sleep_started_event = asyncio.Event()

    @backoff.on_predicate(backoff.expo)
    async def coro():
        sleep_started_event.set()

        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            return True

        return False

    task = event_loop.create_task(coro())

    await sleep_started_event.wait()

    task.cancel()

    assert (await task)


@pytest.mark.asyncio
async def test_on_exception_on_regular_function():
    # Force this function to be a running coroutine.
    await asyncio.sleep(0)

    with pytest.raises(TypeError) as excinfo:
        @backoff.on_exception(backoff.expo, ValueError)
        def regular_func():
            pass
    assert "applied to a regular function" in str(excinfo.value)


@pytest.mark.asyncio
async def test_on_predicate_on_regular_function():
    # Force this function to be a running coroutine.
    await asyncio.sleep(0)

    with pytest.raises(TypeError) as excinfo:
        @backoff.on_predicate(backoff.expo)
        def regular_func():
            pass

    assert "applied to a regular function" in str(excinfo.value)


def test_on_predicate_on_regular_function_without_event_loop(monkeypatch):
    monkeypatch.setattr('time.sleep', lambda x: None)

    # Set default event loop to None.
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(None)

    try:
        @backoff.on_predicate(backoff.expo)
        def return_true(log, n):
            val = (len(log) == n - 1)
            log.append(val)
            return val

        log = []
        ret = return_true(log, 3)
        assert ret is True
        assert 3 == len(log)

    finally:
        # Restore event loop.
        asyncio.set_event_loop(loop)


def test_on_exception_on_regular_function_without_event_loop(monkeypatch):
    monkeypatch.setattr('time.sleep', lambda x: None)

    # Set default event loop to None.
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(None)

    try:
        @backoff.on_exception(backoff.expo, KeyError)
        def keyerror_then_true(log, n):
            if len(log) == n:
                return True
            e = KeyError()
            log.append(e)
            raise e

        log = []
        assert keyerror_then_true(log, 3) is True
        assert 3 == len(log)

    finally:
        # Restore event loop.
        asyncio.set_event_loop(loop)
