# coding:utf-8

import itertools


def from_value(parser):
    """ Generator that is based on parsing the return value or thrown exception of the decorated method

    Args:
        parser: a callable which takes as input the decorated
            function's return value or thrown exception and
            determines how long to wait
    """
    value = yield
    while True:
        value = yield parser(value)


def expo(base=2, factor=1, max_value=None):
    """Generator for exponential decay.

    Args:
        base: The mathematical base of the exponentiation operation
        factor: Factor to multiply the exponentiation by.
        max_value: The maximum value to yield. Once the value in the
             true exponential sequence exceeds this, the value
             of max_value will forever after be yielded.
    """
    yield  # Advance past initial .send() call
    n = 0
    while True:
        a = factor * base ** n
        if max_value is None or a < max_value:
            yield a
            n += 1
        else:
            yield max_value


def fibo(max_value=None):
    """Generator for fibonaccial decay.

    Args:
        max_value: The maximum value to yield. Once the value in the
             true fibonacci sequence exceeds this, the value
             of max_value will forever after be yielded.
    """
    yield  # Advance past initial .send() call
    a = 1
    b = 1
    while True:
        if max_value is None or a < max_value:
            yield a
            a, b = b, a + b
        else:
            yield max_value


def constant(interval=1):
    """Generator for constant intervals.

    Args:
        interval: A constant value to yield or an iterable of such values.
    """
    yield  # Advance past initial .send() call
    try:
        itr = iter(interval)
    except TypeError:
        itr = itertools.repeat(interval)

    for val in itr:
        yield val
