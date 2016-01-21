# coding:utf-8
"""
Function decoration for backoff and retry

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

The `on_exception` decorator is used to retry when a specified exception
is raised. Here's an example using exponential backoff when any
`requests` exception is raised:

    @backoff.on_exception(backoff.expo,
                          requests.exceptions.RequestException,
                          max_tries=8)
    def get_url(url):
        return requests.get(url)

The decorator will also accept a tuple of exceptions for cases where
you want the same backoff behavior for more than one exception type:

    @backoff.on_exception(backoff.expo,
                          (requests.exceptions.Timeout,
                           requests.exceptions.ConnectionError),
                          max_tries=8)
    def get_url(url):
        return requests.get(url)

### @backoff.on_predicate

The `on_predicate` decorator is used to retry when a particular
condition is true of the return value of the target function.  This may
be useful when polling a resource for externally generated content.

Here's an example which uses a fibonacci sequence backoff when the
return value of the target function is the empty list:

    @backoff.on_predicate(backoff.fibo, lambda x: x == [], max_value=13)
    def poll_for_messages(queue):
        return queue.get()

Extra keyword arguments are passed when initializing the
wait generator, so the `max_value` param above is passed as a keyword
arg when initializing the fibo generator.

When not specified, the predicate param defaults to the falsey test,
so the above can more concisely be written:

    @backoff.on_predicate(backoff.fibo, max_value=13)
    def poll_for_message(queue)
        return queue.get()

More simply, a function which continues polling every second until it
gets a non-falsey result could be defined like like this:

    @backoff.on_predicate(backoff.constant, interval=1)
    def poll_for_message(queue)
        return queue.get()

### Using multiple decorators

The backoff decorators may also be combined to specify different
backoff behavior for different cases:

    @backoff.on_predicate(backoff.fibo, max_value=13)
    @backoff.on_exception(backoff.expo,
                          requests.exceptions.HTTPError,
                          max_tries=4)
    @backoff.on_exception(backoff.expo,
                          requests.exceptions.TimeoutError,
                          max_tries=8)
    def poll_for_message(queue):
        return queue.get()

### Event handlers

Both backoff decorators optionally accept event handler functions
using the keyword arguments `on_success`, `on_backoff`, and `on_giveup`.
This may be useful in reporting statistics or performing other custom
logging.

Handlers must be callables with a unary signature accepting a dict
argument. This dict contains the details of the invocation. Valid keys
include:

  * 'target' - reference to the function or method being invoked
  * 'args' - positional arguments to func
  * 'kwargs' - keyword arguments to func
  * 'tries' - number of invocation tries so far
  * 'wait' - seconds to wait (`on_backoff` handler only)
  * 'value' - value triggering backoff (`on_predicate` decorator only)

A handler which prints the details of the backoff event could be
implemented like so:

    def backoff_hdlr(details):
        print ("Backing off {wait:0.1f} seconds afters {tries} tries "
               "calling function {func} with args {args} and kwargs "
               "{kwargs}".format(**details))

    @backoff.on_exception(backoff.expo,
                          requests.exceptions.RequestException,
                          on_backoff=backoff_hdlr)
    def get_url(url):
        return requests.get(url)

#### Multiple handlers per event type

In all cases, iterables of handler functions are also accepted, which
are called in turn.

#### Getting exception info

In the case of the `on_exception` decorator, all `on_backoff` and
`on_giveup` handlers are called from within the except block for the
exception being handled. Therefore exception info is available to the
handler functions via the python standard library, specifically
`sys.exc_info()` or the `traceback` module.

### Logging configuration

Errors and backoff and retry attempts are logged to the 'backoff'
logger. By default, this logger is configured with a NullHandler, so
there will be nothing output unless you configure a handler.
Programmatically, this might be accomplished with something as simple
as:

    logging.getLogger('backoff').addHandler(logging.StreamHandler())

The default logging level is ERROR, which corresponds to logging anytime
`max_tries` is exceeded as well as any time a retryable exception is
raised. If you would instead like to log any type of retry, you can
set the logger level to INFO:

    logging.getLogger('backoff').setLevel(logging.INFO)
"""
from __future__ import unicode_literals

import functools
import operator
import logging
import random
import time
import traceback
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


def expo(init_value=1, base=2, max_value=None):
    """Generator for exponential decay.

    Args:
        base: The mathematical base of the exponentiation operation
        max_value: The maximum value to yield. Once the value in the
             true exponential sequence exceeds this, the value
             of max_value will forever after be yielded.
    """
    n = 0
    while True:
        a = init_value * base ** n
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


def random_jitter(value):
    return value+random.random()


def full_jitter(value):
    return random.uniform(0, value)


def equal_jitter(value):
    return (value/2.0) + (random.uniform(0, value/2.0))


def on_predicate(wait_gen,
                 predicate=operator.not_,
                 max_tries=None,
                 jitter=full_jitter,
                 on_success=None,
                 on_backoff=None,
                 on_giveup=None,
                 **wait_gen_kwargs):
    """Returns decorator for backoff and retry triggered by predicate.

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
        jitter: Callable returning an offset to the value yielded by wait_gen.
            This staggers wait times a random number of milliseconds to help
            spread out load in the case that there are multiple simultaneous
            retries occuring.
        on_success: Callable (or iterable of callables) with a unary
            signature to be called in the event of success. The
            parameter is a dict containing details about the invocation.
        on_backoff: Callable (or iterable of callables) with a unary
            signature to be called in the event of a backoff. The
            parameter is a dict containing details about the invocation.
        on_giveup: Callable (or iterable of callables) wutg a unary
            signature to be called in the event that max_tries
            is exceeded.  The parameter is a dict containing details
            about the invocation.
        **wait_gen_kwargs: Any additional keyword args specified will be
            passed to wait_gen when it is initialized.
    """
    success_hdlrs = _handlers(on_success)
    backoff_hdlrs = _handlers(on_backoff, _log_backoff)
    giveup_hdlrs = _handlers(on_giveup, _log_giveup)

    def decorate(target):

        @functools.wraps(target)
        def retry(*args, **kwargs):
            tries = 0

            wait = wait_gen(**wait_gen_kwargs)
            while True:
                tries += 1
                ret = target(*args, **kwargs)
                if predicate(ret):
                    if max_tries is not None and tries == max_tries:
                        for hdlr in giveup_hdlrs:
                            hdlr({'target': target,
                                  'args': args,
                                  'kwargs': kwargs,
                                  'tries': tries,
                                  'value': ret})
                        break

                    value = next(wait)
                    try:
                        if jitter is not None:
                            seconds = jitter(value)
                        else:
                            seconds = value
                    except TypeError:
                        # support deprecated nullary jitter function signature
                        # which returns a delta rather than a jittered value
                        seconds = value + jitter()

                    for hdlr in backoff_hdlrs:
                        hdlr({'target': target,
                              'args': args,
                              'kwargs': kwargs,
                              'tries': tries,
                              'value': ret,
                              'wait': seconds})

                    time.sleep(seconds)
                    continue
                else:
                    for hdlr in success_hdlrs:
                        hdlr({'target': target,
                              'args': args,
                              'kwargs': kwargs,
                              'tries': tries,
                              'value': ret})
                    break

            return ret

        return retry

    # Return a function which decorates a target with a retry loop.
    return decorate


def on_exception(wait_gen,
                 exception,
                 max_tries=None,
                 jitter=full_jitter,
                 on_success=None,
                 on_backoff=None,
                 on_giveup=None,
                 **wait_gen_kwargs):
    """Returns decorator for backoff and retry triggered by exception.

    Args:
        wait_gen: A generator yielding successive wait times in
            seconds.
        exception: An exception type (or tuple of types) which triggers
            backoff.
        max_tries: The maximum number of attempts to make before giving
            up. Once exhausted, the exception will be allowed to escape.
            The default value of None means their is no limit to the
            number of tries.
        jitter: Callable returning an offset to the value yielded by wait_gen.
            This staggers wait times a random number of milliseconds to help
            spread out load in the case that there are multiple simultaneous
            retries occuring.
        on_success: Callable (or iterable of callables) with a unary
            signature to be called in the event of success. The
            parameter is a dict containing details about the invocation.
        on_backoff: Callable (or iterable of callables) with a unary
            signature to be called in the event of a backoff. The
            parameter is a dict containing details about the invocation.
        on_giveup: Callable (or iterable of callables) wutg a unary
            signature to be called in the event that max_tries
            is exceeded.  The parameter is a dict containing details
            about the invocation.
        **wait_gen_kwargs: Any additional keyword args specified will be
            passed to wait_gen when it is initialized.

    """
    success_hdlrs = _handlers(on_success)
    backoff_hdlrs = _handlers(on_backoff, _log_backoff)
    giveup_hdlrs = _handlers(on_giveup, _log_giveup)

    def decorate(target):

        @functools.wraps(target)
        def retry(*args, **kwargs):
            tries = 0
            wait = wait_gen(**wait_gen_kwargs)
            while True:
                try:
                    tries += 1
                    ret = target(*args, **kwargs)
                except exception:
                    if max_tries is not None and tries == max_tries:
                        for hdlr in giveup_hdlrs:
                            hdlr({'target': target,
                                  'args': args,
                                  'kwargs': kwargs,
                                  'tries': tries})
                        raise

                    value = next(wait)
                    try:
                        if jitter is not None:
                            seconds = jitter(value)
                        else:
                            seconds = value
                    except TypeError:
                        # support deprecated nullary jitter function signature
                        # which returns a delta rather than a jittered value
                        seconds = value + jitter()

                    for hdlr in backoff_hdlrs:
                        hdlr({'target': target,
                              'args': args,
                              'kwargs': kwargs,
                              'tries': tries,
                              'wait': seconds})

                    time.sleep(seconds)
                else:
                    for hdlr in success_hdlrs:
                        hdlr({'target': target,
                              'args': args,
                              'kwargs': kwargs,
                              'tries': tries})

                    return ret

        return retry

    # Return a function which decorates a target with a retry loop.
    return decorate


# Create default handler list from keyword argument
def _handlers(hdlr, default=None):
    defaults = [default] if default is not None else []

    if hdlr is None:
        return defaults

    if hasattr(hdlr, '__iter__'):
        return defaults + list(hdlr)

    return defaults + [hdlr]


# Formats a function invocation as a unicode string for logging.
def _invoc_repr(details):
    f, args, kwargs = details['target'], details['args'], details['kwargs']
    args_out = ", ".join("{0}".format(a) for a in args)
    if args and kwargs:
        args_out += ", "
    if kwargs:
        args_out += ", ".join("{0}={1}".format(k, v)
                              for k, v in kwargs.items())

    return "{0}({1})".format(f.__name__, args_out)


# Default backoff handler
def _log_backoff(details):
    msg = "Backing off {0} {1:.1f}s".format(_invoc_repr(details),
                                            details['wait'])

    exc_typ, exc, _ = sys.exc_info()
    if exc is not None:
        exc_fmt = traceback.format_exception_only(exc_typ, exc)[-1]
        msg = "{0} ({1})".format(msg, exc_fmt.rstrip("\n"))
        logger.error(msg)
    else:
        msg = "{0} ({1})".format(msg, details['value'])
        logger.info(msg)


# Default giveup handler
def _log_giveup(details):
    msg = "Giving up {0} after {1} tries".format(_invoc_repr(details),
                                                 details['tries'])

    exc_typ, exc, _ = sys.exc_info()
    if exc is not None:
        exc_fmt = traceback.format_exception_only(exc_typ, exc)[-1]
        msg = "{0} ({1})".format(msg, exc_fmt.rstrip("\n"))
    else:
        msg = "{0} ({1})".format(msg, details['value'])

    logger.error(msg)
