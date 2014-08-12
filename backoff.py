# coding:utf-8
from __future__ import unicode_literals

"""
Function decoration for pluggable backoff and retry

This module provides function decorators which can be used to wrap a
function such that it will be retried until some condition is met. It
is meant to be of use when accessing unreliable resources with the
potential for intermittent failures i.e. network resources and external
APIs. Somewhat more generally, it may also be of use for dynamically
polling resources for externally generated content.

## Examples

*Since Kenneth Reitz's [requests](http://python-requests.org) module
has become a defacto standard for HTTP clients in python, networking
examples below are written using it, but it is in no way required by
the backoff module.*

### @backoff.on_exception

The on_exception decorator is used to retry when a specified exception
is raised. Here's an example using exponential backoff when any
requests exception is raised:

    @backoff.on_exception(backoff.expo,
                          requests.exceptions.RequestException,
                          max_tries=8)
    def get_url(url):
        return requests.get(url)

### @backoff.on_predicate

The on_predicate decorator is used to retry when a particular condition
is true of the return value of the target function.  This may be useful
when polling a resource for externally generated content.

Here's an example which uses a fibonacci sequence backoff when the
return value of the target function is the empty list:

    @backoff.on_predicate(backoff.fibo, lambda x: x == [], max_value=13)
    def poll_for_messages(queue):
        return queue.get()

Extra keyword arguments are passed when initializing the
wait_generator, so the max_value param above is used to initialize the
fibo generator.

When not specified, the predicate param defaults to the falsey test,
so the above can more concisely be written:

    @backoff.on_predicate(backoff.fibo, max_value=13)
    def poll_for_message(queue)
        return queue.get()

More simply, function which continues polling every second until it
gets a non falsey result could be defined like like this:

    @backoff.on_predicate(backoff.constant, interval=1)
    def poll_for_message(queue)
        return queue.get()

### Using multiple decorators

It can also be useful to combine backoff decorators to define
different backoff behavior for different cases:

    @backoff.on_predicate(backoff.fibo, max_value=13)
    @backoff.on_exception(backoff.expo,
                          requests.exceptions.HTTPError,
                          max_tries=4)
    @backoff.on_exception(backoff.expo,
                          requests.exceptions.TimeoutError,
                          max_tries=8)
    def poll_for_message(queue):
        return queue.get()

### Logging configuration

Errors and backoff/retry attempts are logged to the 'backoff' logger.
By default, this logger is configured with a NullHandler, so there will
be nothing output unless you configure a handler. Programmatically,
this might be accomplished with something as simple as:

    logging.getLogger('backoff').addHandler(logging.StreamHandler())

The default logging level is ERROR, which correponds to logging anytime
max_tries is exceeded as well as any time a retryable exception is
raised. If you would instead like to log any type of retry, you can
instead set the logger level to INFO:

    logging.getLogger('backoff').setLevel(logging.INFO)
"""

import functools
import operator
import logging
import random
import time
import sys


# Use module-specific logger with a default null handler.
logger = logging.getLogger(__name__)

if sys.version_info < (2, 7, 0):  # pragma: no cover
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass
    logger.addHandler(NullHandler())
else:
    logger.addHandler(logging.NullHandler())  # pragma: no cover

logger.setLevel(logging.ERROR)


def expo(base=2, max_value=None):
    """Generator for exponential decay.

    Args:
        base: The mathematical base of the exponentiation operation
        max_value: The maximum value to yield. Once the value in the
             true exponential sequence exceeds this, the value
             of max_value will forever after be yielded.
    """
    n = 0
    while True:
        a = base ** n
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


def constant(interval):
    """Generator for constant intervals.

    Args:
        interval: The constant value in seconds to yield.
    """
    while True:
        yield interval


# Formats a function invocation as a unicode string for logging.
def _invoc_repr(f, args, kwargs):
    args_out = ", ".join("%s" % a for a in args)
    if args and kwargs:
        args_out += ", "
    if kwargs:
        args_out += ", ".join("%s=%s" % i for i in kwargs.items())

    return "%s(%s)" % (f.__name__, args_out)


def on_predicate(wait_gen,
                 predicate=operator.not_,
                 max_tries=None,
                 jitter=random.random,
                 **wait_gen_kwargs):
    """Returns decorator for pluggable backoff triggered by predicate.

    Args:
        wait_gen: A generator yielding successive wait times in
            seconds.
        predicate: A function which when called on the return value of
            the target function will trigger backoff when considered
            truthily. If not specified, the default behavior is to
            backoff on falsey return values.
        max_tries: The maximum number of attempts to make before giving
            up. In the case of failure, the result of the last attempt
            will be returned.  The default value of None means their
            is no limit to the number of tries.
        jitter: Callable returning an offset in seconds to add to the
            value yielded by wait_gen. When used with the default
            random function, this staggers wait times a random number
            of milliseconds to help spread out load in the case that
            there are multiple simultaneous retries occuring.
        **wait_gen_kwargs: Any additional keyword args specified will be passed
            to the wait_gen when it is initialized.
    """
    def decorate(target):

        @functools.wraps(target)
        def retry(*args, **kwargs):
            # format function invocation to be made for logging
            invoc = _invoc_repr(target, args, kwargs)

            tries = 0
            wait = wait_gen(**wait_gen_kwargs)
            while max_tries is None or tries < max_tries:
                ret = target(*args, **kwargs)
                if predicate(ret):
                    tries += 1
                    if tries == max_tries:
                        logger.error("Giving up %s after %s tries" %
                                     (invoc, tries))

                    seconds = next(wait) + jitter()
                    logger.info("Backing off %s: %.1fs" %
                                (invoc, round(seconds, 1)))
                    time.sleep(seconds)
                    continue
                else:
                    break

            return ret

        return retry

    # Return a function which decorates a target with a retry loop.
    return decorate


def on_exception(wait_gen,
                 exception,
                 max_tries=None,
                 jitter=random.random,
                 **wait_gen_kwargs):
    """Returns decorator for pluggable backoff triggered by exception.

    Args:
        wait_gen: A generator yielding successive wait times in
            seconds.
        exception: An exception type which triggers backoff.
        max_tries: The maximum number of attempts to make before giving
            up. Once exhausted, the exception will be allowed to escape.
            The default value of None means their is no limit to the
            number of tries.
        jitter: Callable returning an offset in seconds to add to the
            value yielded by wait_gen. When used with the default
            random function, this staggers wait times a random number
            of milliseconds to help spread out load in the case that
            there are multiple simultaneous retries occuring.
        **wait_gen_kwargs: Any additional keyword args specified will be
            passed to the wait_generator when it is initialized.

    """
    def decorate(target):

        @functools.wraps(target)
        def retry(*args, **kwargs):
            # format function invocation to be made for logging
            invoc = _invoc_repr(target, args, kwargs)

            tries = 0
            wait = wait_gen(**wait_gen_kwargs)
            while max_tries is None or tries < max_tries:
                try:
                    ret = target(*args, **kwargs)
                except exception as e:
                    tries += 1
                    if tries == max_tries:
                        logger.error("Giving up %s after %s tries: %s" %
                                     (invoc, tries, e))
                        raise

                    seconds = next(wait) + jitter()
                    logger.error("Backing off %s %.1fs for exception: %s" %
                                 (invoc, round(seconds, 1), e))
                    time.sleep(seconds)
                else:
                    return ret

        return retry

    # Return a function which decorates a target with a retry loop.
    return decorate
