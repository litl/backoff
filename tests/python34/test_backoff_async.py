# coding:utf-8

import asyncio
import backoff
import pytest
import random

from tests.common import _log_hdlrs, _save_target


def test_expo():
    gen = backoff.expo()
    for i in range(9):
        assert 2 ** i == next(gen)


def test_expo_base3():
    gen = backoff.expo(base=3)
    for i in range(9):
        assert 3 ** i == next(gen)


def test_expo_factor3():
    gen = backoff.expo(factor=3)
    for i in range(9):
        assert 3 * 2 ** i == next(gen)


def test_expo_base3_factor5():
    gen = backoff.expo(base=3, factor=5)
    for i in range(9):
        assert 5 * 3 ** i == next(gen)


def test_expo_max_value():
    gen = backoff.expo(max_value=2 ** 4)
    expected = [1, 2, 4, 8, 16, 16, 16]
    for expect in expected:
        assert expect == next(gen)


def test_fibo():
    gen = backoff.fibo()
    expected = [1, 1, 2, 3, 5, 8, 13]
    for expect in expected:
        assert expect == next(gen)


def test_fibo_max_value():
    gen = backoff.fibo(max_value=8)
    expected = [1, 1, 2, 3, 5, 8, 8, 8]
    for expect in expected:
        assert expect == next(gen)


def test_constant():
    gen = backoff.constant(interval=3)
    for i in range(9):
        assert 3 == next(gen)


@pytest.mark.asyncio
def test_on_predicate(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', asyncio.coroutine(lambda x: None))

    @backoff.on_predicate(backoff.expo)
    @asyncio.coroutine
    def return_true(log, n):
        val = (len(log) == n - 1)
        log.append(val)
        return val

    log = []
    ret = yield from return_true(log, 3)
    assert ret is True
    assert 3 == len(log)


@pytest.mark.asyncio
def test_on_predicate_max_tries(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', asyncio.coroutine(lambda x: None))

    @backoff.on_predicate(backoff.expo, jitter=None, max_tries=3)
    @asyncio.coroutine
    def return_true(log, n):
        val = (len(log) == n)
        log.append(val)
        return val

    log = []
    ret = yield from return_true(log, 10)
    assert ret is False
    assert 3 == len(log)


@pytest.mark.asyncio
def test_on_exception(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', asyncio.coroutine(lambda x: None))

    @backoff.on_exception(backoff.expo, KeyError)
    @asyncio.coroutine
    def keyerror_then_true(log, n):
        if len(log) == n:
            return True
        e = KeyError()
        log.append(e)
        raise e

    log = []
    assert (yield from keyerror_then_true(log, 3)) is True
    assert 3 == len(log)


@pytest.mark.asyncio
def test_on_exception_tuple(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', asyncio.coroutine(lambda x: None))

    @backoff.on_exception(backoff.expo, (KeyError, ValueError))
    @asyncio.coroutine
    def keyerror_valueerror_then_true(log):
        if len(log) == 2:
            return True
        if len(log) == 0:
            e = KeyError()
        if len(log) == 1:
            e = ValueError()
        log.append(e)
        raise e

    log = []
    assert (yield from keyerror_valueerror_then_true(log)) is True
    assert 2 == len(log)
    assert isinstance(log[0], KeyError)
    assert isinstance(log[1], ValueError)


@pytest.mark.asyncio
def test_on_exception_max_tries(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', asyncio.coroutine(lambda x: None))

    @backoff.on_exception(backoff.expo, KeyError, jitter=None, max_tries=3)
    @asyncio.coroutine
    def keyerror_then_true(log, n, foo=None):
        if len(log) == n:
            return True
        e = KeyError()
        log.append(e)
        raise e

    log = []
    with pytest.raises(KeyError):
        yield from keyerror_then_true(log, 10, foo="bar")

    assert 3 == len(log)


@pytest.mark.asyncio
def test_on_exception_success_random_jitter(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', asyncio.coroutine(lambda x: None))

    log, log_success, log_backoff, log_giveup = _log_hdlrs()

    @backoff.on_exception(backoff.expo,
                          Exception,
                          on_success=log_success,
                          on_backoff=log_backoff,
                          on_giveup=log_giveup,
                          jitter=backoff.random_jitter,
                          factor=0.5)
    @_save_target
    @asyncio.coroutine
    def succeeder(*args, **kwargs):
        # succeed after we've backed off twice
        if len(log['backoff']) < 2:
            raise ValueError("catch me")

    yield from succeeder(1, 2, 3, foo=1, bar=2)

    # we try 3 times, backing off twice before succeeding
    assert len(log['success']) == 1
    assert len(log['backoff']) == 2
    assert len(log['giveup']) == 0

    for i in range(2):
        details = log['backoff'][i]
        assert details['wait'] >= 0.5 * 2 ** i


@pytest.mark.asyncio
def test_on_exception_success_full_jitter(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', asyncio.coroutine(lambda x: None))

    log, log_success, log_backoff, log_giveup = _log_hdlrs()

    @backoff.on_exception(backoff.expo,
                          Exception,
                          on_success=log_success,
                          on_backoff=log_backoff,
                          on_giveup=log_giveup,
                          jitter=backoff.full_jitter,
                          factor=0.5)
    @_save_target
    @asyncio.coroutine
    def succeeder(*args, **kwargs):
        # succeed after we've backed off twice
        if len(log['backoff']) < 2:
            raise ValueError("catch me")

    yield from succeeder(1, 2, 3, foo=1, bar=2)

    # we try 3 times, backing off twice before succeeding
    assert len(log['success']) == 1
    assert len(log['backoff']) == 2
    assert len(log['giveup']) == 0

    for i in range(2):
        details = log['backoff'][i]
        assert details['wait'] <= 0.5 * 2 ** i


@pytest.mark.asyncio
def test_on_exception_success():
    log, log_success, log_backoff, log_giveup = _log_hdlrs()

    @backoff.on_exception(backoff.constant,
                          Exception,
                          on_success=log_success,
                          on_backoff=log_backoff,
                          on_giveup=log_giveup,
                          jitter=lambda: 0,
                          interval=0)
    @_save_target
    @asyncio.coroutine
    def succeeder(*args, **kwargs):
        # succeed after we've backed off twice
        if len(log['backoff']) < 2:
            raise ValueError("catch me")

    yield from succeeder(1, 2, 3, foo=1, bar=2)

    # we try 3 times, backing off twice before succeeding
    assert len(log['success']) == 1
    assert len(log['backoff']) == 2
    assert len(log['giveup']) == 0

    for i in range(2):
        details = log['backoff'][i]
        assert details == {'args': (1, 2, 3),
                           'kwargs': {'foo': 1, 'bar': 2},
                           'target': succeeder._target,
                           'tries': i + 1,
                           'wait': 0}

    details = log['success'][0]
    assert details == {'args': (1, 2, 3),
                       'kwargs': {'foo': 1, 'bar': 2},
                       'target': succeeder._target,
                       'tries': 3}


@pytest.mark.asyncio
def test_on_exception_giveup():
    log, log_success, log_backoff, log_giveup = _log_hdlrs()

    @backoff.on_exception(backoff.constant,
                          ValueError,
                          on_success=log_success,
                          on_backoff=log_backoff,
                          on_giveup=log_giveup,
                          max_tries=3,
                          jitter=lambda: 0,
                          interval=0)
    @_save_target
    @asyncio.coroutine
    def exceptor(*args, **kwargs):
        raise ValueError("catch me")

    with pytest.raises(ValueError):
        yield from exceptor(1, 2, 3, foo=1, bar=2)

    # we try 3 times, backing off twice and giving up once
    assert len(log['success']) == 0
    assert len(log['backoff']) == 2
    assert len(log['giveup']) == 1

    details = log['giveup'][0]
    assert details == {'args': (1, 2, 3),
                       'kwargs': {'foo': 1, 'bar': 2},
                       'target': exceptor._target,
                       'tries': 3}


@pytest.mark.asyncio
def test_on_exception_giveup_predicate(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', asyncio.coroutine(lambda x: None))

    def on_baz(e):
        return str(e) == "baz"

    vals = ["baz", "bar", "foo"]

    @backoff.on_exception(backoff.constant,
                          ValueError,
                          giveup=on_baz)
    @asyncio.coroutine
    def foo_bar_baz():
        raise ValueError(vals.pop())

    with pytest.raises(ValueError):
        yield from foo_bar_baz()

    assert not vals


@pytest.mark.asyncio
def test_on_exception_giveup_coro(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', asyncio.coroutine(lambda x: None))

    @asyncio.coroutine
    def on_baz(e):
        return str(e) == "baz"

    vals = ["baz", "bar", "foo"]

    @backoff.on_exception(backoff.constant,
                          ValueError,
                          giveup=on_baz)
    @asyncio.coroutine
    def foo_bar_baz():
        raise ValueError(vals.pop())

    with pytest.raises(ValueError):
        yield from foo_bar_baz()

    assert not vals


@pytest.mark.asyncio
def test_on_predicate_success():
    log, log_success, log_backoff, log_giveup = _log_hdlrs()

    @backoff.on_predicate(backoff.constant,
                          on_success=log_success,
                          on_backoff=log_backoff,
                          on_giveup=log_giveup,
                          jitter=lambda: 0,
                          interval=0)
    @_save_target
    @asyncio.coroutine
    def success(*args, **kwargs):
        # succeed after we've backed off twice
        return len(log['backoff']) == 2

    yield from success(1, 2, 3, foo=1, bar=2)

    # we try 3 times, backing off twice before succeeding
    assert len(log['success']) == 1
    assert len(log['backoff']) == 2
    assert len(log['giveup']) == 0

    for i in range(2):
        details = log['backoff'][i]
        assert details == {'args': (1, 2, 3),
                           'kwargs': {'foo': 1, 'bar': 2},
                           'target': success._target,
                           'tries': i + 1,
                           'value': False,
                           'wait': 0}

    details = log['success'][0]
    assert details == {'args': (1, 2, 3),
                       'kwargs': {'foo': 1, 'bar': 2},
                       'target': success._target,
                       'tries': 3,
                       'value': True}


@pytest.mark.asyncio
def test_on_predicate_giveup():
    log, log_success, log_backoff, log_giveup = _log_hdlrs()

    @backoff.on_predicate(backoff.constant,
                          on_success=log_success,
                          on_backoff=log_backoff,
                          on_giveup=log_giveup,
                          max_tries=3,
                          jitter=lambda: 0,
                          interval=0)
    @_save_target
    @asyncio.coroutine
    def emptiness(*args, **kwargs):
        pass

    yield from emptiness(1, 2, 3, foo=1, bar=2)

    # we try 3 times, backing off twice and giving up once
    assert len(log['success']) == 0
    assert len(log['backoff']) == 2
    assert len(log['giveup']) == 1

    details = log['giveup'][0]
    assert details == {'args': (1, 2, 3),
                       'kwargs': {'foo': 1, 'bar': 2},
                       'target': emptiness._target,
                       'tries': 3,
                       'value': None}


@pytest.mark.asyncio
def test_on_predicate_iterable_handlers():
    hdlrs = [_log_hdlrs() for _ in range(3)]

    @backoff.on_predicate(backoff.constant,
                          on_success=(h[1] for h in hdlrs),
                          on_backoff=(h[2] for h in hdlrs),
                          on_giveup=(h[3] for h in hdlrs),
                          max_tries=3,
                          jitter=lambda: 0,
                          interval=0)
    @_save_target
    @asyncio.coroutine
    def emptiness(*args, **kwargs):
        pass

    yield from emptiness(1, 2, 3, foo=1, bar=2)

    for i in range(3):
        assert len(hdlrs[i][0]['success']) == 0
        assert len(hdlrs[i][0]['backoff']) == 2
        assert len(hdlrs[i][0]['giveup']) == 1

        details = hdlrs[i][0]['giveup'][0]
        assert details == {'args': (1, 2, 3),
                           'kwargs': {'foo': 1, 'bar': 2},
                           'target': emptiness._target,
                           'tries': 3,
                           'value': None}


# To maintain backward compatibility,
# on_predicate should support 0-argument jitter function.
@pytest.mark.asyncio
def test_on_exception_success_0_arg_jitter(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', asyncio.coroutine(lambda x: None))
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
    @asyncio.coroutine
    def succeeder(*args, **kwargs):
        # succeed after we've backed off twice
        if len(log['backoff']) < 2:
            raise ValueError("catch me")

    yield from succeeder(1, 2, 3, foo=1, bar=2)

    # we try 3 times, backing off twice before succeeding
    assert len(log['success']) == 1
    assert len(log['backoff']) == 2
    assert len(log['giveup']) == 0

    for i in range(2):
        details = log['backoff'][i]
        assert details == {'args': (1, 2, 3),
                           'kwargs': {'foo': 1, 'bar': 2},
                           'target': succeeder._target,
                           'tries': i + 1,
                           'wait': 0}

    details = log['success'][0]
    assert details == {'args': (1, 2, 3),
                       'kwargs': {'foo': 1, 'bar': 2},
                       'target': succeeder._target,
                       'tries': 3}


# To maintain backward compatibility,
# on_predicate should support 0-argument jitter function.
@pytest.mark.asyncio
def test_on_predicate_success_0_arg_jitter(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', asyncio.coroutine(lambda x: None))
    monkeypatch.setattr('random.random', lambda: 0)

    log, log_success, log_backoff, log_giveup = _log_hdlrs()

    @backoff.on_predicate(backoff.constant,
                          on_success=log_success,
                          on_backoff=log_backoff,
                          on_giveup=log_giveup,
                          jitter=random.random,
                          interval=0)
    @_save_target
    @asyncio.coroutine
    def success(*args, **kwargs):
        # succeed after we've backed off twice
        return len(log['backoff']) == 2

    yield from success(1, 2, 3, foo=1, bar=2)

    # we try 3 times, backing off twice before succeeding
    assert len(log['success']) == 1
    assert len(log['backoff']) == 2
    assert len(log['giveup']) == 0

    for i in range(2):
        details = log['backoff'][i]
        assert details == {'args': (1, 2, 3),
                           'kwargs': {'foo': 1, 'bar': 2},
                           'target': success._target,
                           'tries': i + 1,
                           'value': False,
                           'wait': 0}

    details = log['success'][0]
    assert details == {'args': (1, 2, 3),
                       'kwargs': {'foo': 1, 'bar': 2},
                       'target': success._target,
                       'tries': 3,
                       'value': True}


@pytest.mark.asyncio
def test_on_exception_callable_max_tries(monkeypatch):
    monkeypatch.setattr('asyncio.sleep', asyncio.coroutine(lambda x: None))

    def lookup_max_tries():
        return 3

    log = []

    @backoff.on_exception(backoff.constant,
                          ValueError,
                          max_tries=lookup_max_tries)
    @asyncio.coroutine
    def exceptor():
        log.append(True)
        raise ValueError()

    with pytest.raises(ValueError):
        yield from exceptor()

    assert len(log) == 3


@pytest.mark.asyncio
def test_on_exception_callable_gen_kwargs():

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
    @asyncio.coroutine
    def exceptor():
        raise ValueError("aah")

    with pytest.raises(ValueError):
        yield from exceptor()


@pytest.mark.asyncio
def test_on_exception_coro_cancelling(event_loop):
    sleep_started_event = asyncio.Event()

    @backoff.on_predicate(backoff.expo)
    @asyncio.coroutine
    def coro():
        sleep_started_event.set()

        try:
            yield from asyncio.sleep(10)
        except asyncio.CancelledError:
            return True

        return False

    task = event_loop.create_task(coro())

    yield from sleep_started_event.wait()

    task.cancel()

    assert (yield from task)


@pytest.mark.asyncio
def test_on_exception_on_regular_function():
    # Force this function to be a running coroutine.
    yield from asyncio.sleep(0)

    with pytest.raises(TypeError) as excinfo:
        @backoff.on_exception(backoff.expo, ValueError)
        def regular_func():
            pass
    assert "applied to a regular function" in str(excinfo.value)


@pytest.mark.asyncio
def test_on_predicate_on_regular_function():
    # Force this function to be a running coroutine.
    yield from asyncio.sleep(0)

    with pytest.raises(TypeError) as excinfo:
        @backoff.on_predicate(backoff.expo)
        def regular_func():
            pass

    assert "applied to a regular function" in str(excinfo.value)
