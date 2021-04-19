# coding:utf-8

import itertools
from typing import Generator, Iterable, Optional, Union


def expo(
    base: int = 2,
    factor: int = 1,
    max_value: Optional[int] = None
) -> Generator[int, None, None]:

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


def fibo(max_value: Optional[int] = None) -> Generator[int, None, None]:
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


def constant(
    interval: Union[int, Iterable[int]] = 1
) -> Generator[int, None, None]:
    """Generator for constant intervals.

    Args:
        interval: A constant value to yield or an iterable of such values.
    """
    yield  # Advance past initial .send() call
    try:
        itr = iter(interval)  # type: ignore
    except TypeError:
        itr = itertools.repeat(interval)  # type: ignore

    for val in itr:
        yield val
