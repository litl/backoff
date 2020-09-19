# coding:utf-8

import itertools

try:
    from typing import Iterable, Iterator, Optional, Union
except ImportError:
    # This import is not used at runtime and may fail since the typing module
    # is optional on Python v2.7. This is fine as it is only required for
    # external static type checkers.
    pass


def expo(base=2, factor=1, max_value=None):
    # type: (int, float, Optional[float]) -> Iterator[float]
    """Generator for exponential decay.

    Args:
        base: The mathematical base of the exponentiation operation
        factor: Factor to multiply the exponentation by.
        max_value: The maximum value to yield. Once the value in the
             true exponential sequence exceeds this, the value
             of max_value will forever after be yielded.
    """
    n = 0
    while True:
        a = factor * base ** n
        if max_value is None or a < max_value:
            yield a
            n += 1
        else:
            yield max_value


def fibo(max_value=None):
    # type: (Optional[int]) -> Iterator[int]
    """Generator for fibonaccial decay.

    Args:
        max_value: The maximum value to yield. Once the value in the
             true fibonacci sequence exceeds this, the value
             of max_value will forever after be yielded.
    """
    a = 1
    b = 1
    while True:
        if max_value is None or a < max_value:
            yield a
            a, b = b, a + b
        else:
            yield max_value


def constant(interval=1):
    # type: (Union[float, Iterable[float]]) -> Iterator[float]
    """Generator for constant intervals.

    Args:
        interval: A constant value to yield or an iterable of such values.
    """
    try:
        itr = iter(interval)
    except TypeError:
        itr = itertools.repeat(interval)

    for val in itr:
        yield val
