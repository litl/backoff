# coding:utf-8
import backoff
import math


def test_decay():
    gen = backoff.decay()
    gen.send(None)
    for i in range(10):
        assert math.e ** -i == next(gen)


def test_decay_init100():
    gen = backoff.decay(initial_value=100)
    gen.send(None)
    for i in range(10):
        assert 100 * math.e ** -i == next(gen)


def test_decay_init100_decay3():
    gen = backoff.decay(initial_value=100, decay_factor=3)
    gen.send(None)
    for i in range(10):
        assert 100 * math.e ** (-i * 3) == next(gen)


def test_decay_init100_decay3_min5():
    gen = backoff.decay(initial_value=100, decay_factor=3, min_value=5)
    gen.send(None)
    for i in range(10):
        assert max(100 * math.e ** (-i * 3), 5) == next(gen)


def test_expo():
    gen = backoff.expo()
    gen.send(None)
    for i in range(9):
        assert 2 ** i == next(gen)


def test_expo_base3():
    gen = backoff.expo(base=3)
    gen.send(None)
    for i in range(9):
        assert 3 ** i == next(gen)


def test_expo_factor3():
    gen = backoff.expo(factor=3)
    gen.send(None)
    for i in range(9):
        assert 3 * 2 ** i == next(gen)


def test_expo_base3_factor5():
    gen = backoff.expo(base=3, factor=5)
    gen.send(None)
    for i in range(9):
        assert 5 * 3 ** i == next(gen)


def test_expo_max_value():
    gen = backoff.expo(max_value=2 ** 4)
    gen.send(None)
    expected = [1, 2, 4, 8, 16, 16, 16]
    for expect in expected:
        assert expect == next(gen)


def test_fibo():
    gen = backoff.fibo()
    gen.send(None)
    expected = [1, 1, 2, 3, 5, 8, 13]
    for expect in expected:
        assert expect == next(gen)


def test_fibo_max_value():
    gen = backoff.fibo(max_value=8)
    gen.send(None)
    expected = [1, 1, 2, 3, 5, 8, 8, 8]
    for expect in expected:
        assert expect == next(gen)


def test_constant():
    gen = backoff.constant(interval=3)
    gen.send(None)
    for i in range(9):
        assert 3 == next(gen)


def test_runtime():
    gen = backoff.runtime(value=lambda x: x)
    gen.send(None)
    for i in range(20):
        assert i == gen.send(i)
