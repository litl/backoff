# coding:utf-8


def expo(base=2, factor=1, max_value=None):
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
    """Generator for constant intervals.

    Args:
        interval: The constant value in seconds to yield.
    """
    while True:
        yield interval
