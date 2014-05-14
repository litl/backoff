# coding:utf-8

import backoff
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

    assert "func(a, b, c=c)" == backoff._invoc_repr(func,
                                                    ["a", "b"],
                                                    {"c": "c"})
    assert "func(c=c)" == backoff._invoc_repr(func, [], {"c": "c"})
    assert "func(a, b)" == backoff._invoc_repr(func, ["a", "b"], {})
