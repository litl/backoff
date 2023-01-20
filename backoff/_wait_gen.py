# coding:utf-8

import itertools
import math
from typing import Any, Callable, Generator, Iterable, Optional, Union


def expo(
    base: float = 2,
    factor: float = 1,
    max_value: Optional[float] = None
) -> Generator[float, Any, None]:

    """Generator for exponential decay.

    Args:
        base: The mathematical base of the exponentiation operation
        factor: Factor to multiply the exponentiation by.
        max_value: The maximum value to yield. Once the value in the
             true exponential sequence exceeds this, the value
             of max_value will forever after be yielded.
    """
    # Advance past initial .send() call
    yield  # type: ignore[misc]
    n = 0
    while True:
        a = factor * base ** n
        if max_value is None or a < max_value:
            yield a
            n += 1
        else:
            yield max_value


def decay(
    initial_value: float = 1,
    decay_factor: float = 1,
    min_value: Optional[float] = None
) -> Generator[float, Any, None]:

    """Generator for exponential decay[1]:

    Args:
        initial_value: initial quantity
        decay_factor: exponential decay constant.
        min_value: The minimum value to yield. Once the value in the
             true exponential sequence is lower than this, the value
             of min_value will forever after be yielded.

    [1] https://en.wikipedia.org/wiki/Exponential_decay
    """
    # Advance past initial .send() call
    yield  # type: ignore[misc]
    t = 0
    while True:
        a = initial_value * math.e ** (-t * decay_factor)
        if min_value is None or a > min_value:
            yield a
            t += 1
        else:
            yield min_value


def fibo(max_value: Optional[int] = None) -> Generator[int, None, None]:
    """Generator for fibonaccial decay.

    Args:
        max_value: The maximum value to yield. Once the value in the
             true fibonacci sequence exceeds this, the value
             of max_value will forever after be yielded.
    """
    # Advance past initial .send() call
    yield  # type: ignore[misc]

    a = 1
    b = 1
    while True:
        if max_value is None or a < max_value:
            yield a
            a, b = b, a + b
        else:
            yield max_value


def constant(
    interval: Union[int, Iterable[float]] = 1
) -> Generator[float, None, None]:
    """Generator for constant intervals.

    Args:
        interval: A constant value to yield or an iterable of such values.
    """
    # Advance past initial .send() call
    yield  # type: ignore[misc]

    try:
        itr = iter(interval)  # type: ignore
    except TypeError:
        itr = itertools.repeat(interval)  # type: ignore

    for val in itr:
        yield val


def runtime(
    *,
    value: Callable[[Any], float]
) -> Generator[float, None, None]:
    """Generator that is based on parsing the return value or thrown
        exception of the decorated method

    Args:
        value: a callable which takes as input the decorated
            function's return value or thrown exception and
            determines how long to wait
    """
    ret_or_exc = yield  # type: ignore[misc]
    while True:
        ret_or_exc = yield value(ret_or_exc)
