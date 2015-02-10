# coding:utf-8

import backoff
import collections
import functools
import mock
import pytest


def test_expo():
    gen = backoff.expo()
    for i in range(9):
        assert 2 ** i == next(gen)


def test_expo_base3():
    gen = backoff.expo(base=3)
    for i in range(9):
        assert 3 ** i == next(gen)


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


@mock.patch('time.sleep', lambda x: None)
def test_on_predicate():
    @backoff.on_predicate(backoff.expo)
    def return_true(log, n):
        val = (len(log) == n - 1)
        log.append(val)
        return val

    log = []
    ret = return_true(log, 3)
    assert True == ret
    assert 3 == len(log)


@mock.patch('time.sleep', lambda x: None)
def test_on_predicate_max_tries():
    @backoff.on_predicate(backoff.expo, max_tries=3)
    def return_true(log, n):
        val = (len(log) == n)
        log.append(val)
        return val

    log = []
    ret = return_true(log, 10)
    assert False == ret
    assert 3 == len(log)


@mock.patch('time.sleep', lambda x: None)
def test_on_exception():
    @backoff.on_exception(backoff.expo, KeyError)
    def keyerror_then_true(log, n):
        if len(log) == n:
            return True
        e = KeyError()
        log.append(e)
        raise e

    log = []
    assert True == keyerror_then_true(log, 3)
    assert 3 == len(log)


@mock.patch('time.sleep', lambda x: None)
def test_on_exception_max_tries():
    @backoff.on_exception(backoff.expo, KeyError, max_tries=3)
    def keyerror_then_true(log, n, foo=None):
        if len(log) == n:
            return True
        e = KeyError()
        log.append(e)
        raise e

    log = []
    with pytest.raises(KeyError):
        keyerror_then_true(log, 10, foo="bar")

    assert 3 == len(log)


def test_invoc_repr():
    def func(a, b, c=None):
        pass

    assert "func(a, b, c=c)" == backoff._invoc_repr((func,
                                                     ["a", "b"],
                                                     {"c": "c"}))
    assert "func(c=c)" == backoff._invoc_repr((func, [], {"c": "c"}))
    assert "func(a, b)" == backoff._invoc_repr((func, ["a", "b"], {}))
    assert u"func(ユニコーン, ア=あ)" == \
        backoff._invoc_repr((func, [u"ユニコーン"], {u"ア": u"あ"}))

    # tuple args caused a string formatting exception
    assert "func((1, 2, 3))" == backoff._invoc_repr((func, [(1, 2, 3)], {}))


# create event handler which log their invocations to a dict
def _log_hdlrs():
    log = collections.defaultdict(int)

    def log_hdlr(event,
                 invoc,
                 wait=None, tries=None, exception=None, value=None):
        log[event] += 1

    log_success = functools.partial(log_hdlr, 'success')
    log_backoff = functools.partial(log_hdlr, 'backoff')
    log_giveup = functools.partial(log_hdlr, 'giveup')

    return log, log_success, log_backoff, log_giveup


def test_on_exception_success():
    log, log_success, log_backoff, log_giveup = _log_hdlrs()

    @backoff.on_exception(backoff.constant,
                          Exception,
                          on_success=log_success,
                          on_backoff=log_backoff,
                          on_giveup=log_giveup,
                          jitter=lambda: 0,
                          interval=0)
    def succeeder():
        # succeed after we've backed off twice
        if log['backoff'] < 2:
            raise ValueError("catch me")

    succeeder()

    # we try 3 times, backing off twice before succeeding
    assert log['success'] == 1
    assert log['backoff'] == 2
    assert log['giveup'] == 0


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
    def exceptor():
        raise ValueError("catch me")

    with pytest.raises(ValueError):
        exceptor()

    # we try 3 times, backing off twice and giving up once
    assert log['success'] == 0
    assert log['backoff'] == 2
    assert log['giveup'] == 1


def test_on_predicate_success():
    log, log_success, log_backoff, log_giveup = _log_hdlrs()

    @backoff.on_predicate(backoff.constant,
                          on_success=log_success,
                          on_backoff=log_backoff,
                          on_giveup=log_giveup,
                          jitter=lambda: 0,
                          interval=0)
    def success():
        # succeed after we've backed off twice
        return log['backoff'] == 2

    success()

    # we try 3 times, backing off twice before succeeding
    assert log['success'] == 1
    assert log['backoff'] == 2
    assert log['giveup'] == 0


def test_on_predicate_giveup():
    log, log_success, log_backoff, log_giveup = _log_hdlrs()

    @backoff.on_predicate(backoff.constant,
                          on_success=log_success,
                          on_backoff=log_backoff,
                          on_giveup=log_giveup,
                          max_tries=3,
                          jitter=lambda: 0,
                          interval=0)
    def emptiness():
        pass

    emptiness()

    # we try 3 times, backing off twice and giving up once
    assert log['success'] == 0
    assert log['backoff'] == 2
    assert log['giveup'] == 1


def test_on_predicate_iterable_handlers():
    hdlrs = [_log_hdlrs() for _ in range(3)]

    @backoff.on_predicate(backoff.constant,
                          on_success=(h[1] for h in hdlrs),
                          on_backoff=(h[2] for h in hdlrs),
                          on_giveup=(h[3] for h in hdlrs),
                          max_tries=3,
                          jitter=lambda: 0,
                          interval=0)
    def emptiness():
        pass

    emptiness()

    for i in range(3):
        assert hdlrs[i][0]['success'] == 0
        assert hdlrs[i][0]['backoff'] == 2
        assert hdlrs[i][0]['giveup'] == 1
