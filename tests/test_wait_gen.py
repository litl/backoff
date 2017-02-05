# coding:utf-8
import backoff


def test_expo():
    gen = backoff.expo()
    for i in range(9):
        assert 2**i == next(gen)


def test_expo_base3():
    gen = backoff.expo(base=3)
    for i in range(9):
        assert 3**i == next(gen)


def test_expo_factor3():
    gen = backoff.expo(factor=3)
    for i in range(9):
        assert 3 * 2**i == next(gen)


def test_expo_base3_factor5():
    gen = backoff.expo(base=3, factor=5)
    for i in range(9):
        assert 5 * 3**i == next(gen)


def test_expo_max_value():
    gen = backoff.expo(max_value=2**4)
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
