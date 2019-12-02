# coding:utf-8
from __future__ import unicode_literals

import logging
import operator
import sys

from backoff._common import (_config_handlers, _log_backoff, _log_giveup)
from backoff._jitter import full_jitter
from backoff import _sync


# python 2.7 -> 3.x compatibility for str and unicode
try:
    basestring
except NameError:  # pragma: python=3.5
    basestring = str


def on_predicate(wait_gen,
                 predicate=operator.not_,
                 max_tries=None,
                 max_time=None,
                 jitter=full_jitter,
                 on_success=None,
                 on_backoff=None,
                 on_giveup=None,
                 logger='backoff',
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
            will be returned. The default value of None means there
            is no limit to the number of tries. If a callable is passed,
            it will be evaluated at runtime and its return value used.
        max_time: The maximum total amount of time to try for before
            giving up. If this time expires, the result of the last
            attempt will be returned. If a callable is passed, it will
            be evaluated at runtime and its return value used.
        jitter: A function of the value yielded by wait_gen returning
            the actual time to wait. This distributes wait times
            stochastically in order to avoid timing collisions across
            concurrent clients. Wait times are jittered by default
            using the full_jitter function. Jittering may be disabled
            altogether by passing jitter=None.
        on_success: Callable (or iterable of callables) with a unary
            signature to be called in the event of success. The
            parameter is a dict containing details about the invocation.
        on_backoff: Callable (or iterable of callables) with a unary
            signature to be called in the event of a backoff. The
            parameter is a dict containing details about the invocation.
        on_giveup: Callable (or iterable of callables) with a unary
            signature to be called in the event that max_tries
            is exceeded.  The parameter is a dict containing details
            about the invocation.
        logger: Name of logger or Logger object to log to. Defaults to
            'backoff'.
        **wait_gen_kwargs: Any additional keyword args specified will be
            passed to wait_gen when it is initialized.  Any callable
            args will first be evaluated and their return values passed.
            This is useful for runtime configuration.
    """
    def decorate(target):
        # change names because python 2.x doesn't have nonlocal
        logger_ = logger
        if isinstance(logger_, basestring):
            logger_ = logging.getLogger(logger_)
        on_success_ = _config_handlers(on_success)
        on_backoff_ = _config_handlers(on_backoff, _log_backoff, logger_)
        on_giveup_ = _config_handlers(on_giveup, _log_giveup, logger_)

        retry = None
        if sys.version_info >= (3, 5):  # pragma: python=3.5
            import asyncio

            if asyncio.iscoroutinefunction(target):
                import backoff._async
                retry = backoff._async.retry_predicate

        if retry is None:
            retry = _sync.retry_predicate

        return retry(target, wait_gen, predicate,
                     max_tries, max_time, jitter,
                     on_success_, on_backoff_, on_giveup_,
                     wait_gen_kwargs)

    # Return a function which decorates a target with a retry loop.
    return decorate


def on_exception(wait_gen,
                 exception,
                 max_tries=None,
                 max_time=None,
                 jitter=full_jitter,
                 giveup=lambda e: False,
                 on_success=None,
                 on_backoff=None,
                 on_giveup=None,
                 logger='backoff',
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
            number of tries. If a callable is passed, it will be
            evaluated at runtime and its return value used.
        max_time: The maximum total amount of time to try for before
            giving up. Once expired, the exception will be allowed to
            escape. If a callable is passed, it will be
            evaluated at runtime and its return value used.
        jitter: A function of the value yielded by wait_gen returning
            the actual time to wait. This distributes wait times
            stochastically in order to avoid timing collisions across
            concurrent clients. Wait times are jittered by default
            using the full_jitter function. Jittering may be disabled
            altogether by passing jitter=None.
        giveup: Function accepting an exception instance and
            returning whether or not to give up. Optional. The default
            is to always continue.
        on_success: Callable (or iterable of callables) with a unary
            signature to be called in the event of success. The
            parameter is a dict containing details about the invocation.
        on_backoff: Callable (or iterable of callables) with a unary
            signature to be called in the event of a backoff. The
            parameter is a dict containing details about the invocation.
        on_giveup: Callable (or iterable of callables) with a unary
            signature to be called in the event that max_tries
            is exceeded.  The parameter is a dict containing details
            about the invocation.
        logger: Name or Logger object to log to. Defaults to 'backoff'.
        **wait_gen_kwargs: Any additional keyword args specified will be
            passed to wait_gen when it is initialized.  Any callable
            args will first be evaluated and their return values passed.
            This is useful for runtime configuration.
    """
    def decorate(target):
        # change names because python 2.x doesn't have nonlocal
        logger_ = logger
        if isinstance(logger_, basestring):
            logger_ = logging.getLogger(logger_)
        on_success_ = _config_handlers(on_success)
        on_backoff_ = _config_handlers(on_backoff, _log_backoff, logger_)
        on_giveup_ = _config_handlers(on_giveup, _log_giveup, logger_)

        retry = None
        if sys.version_info[:2] >= (3, 5):   # pragma: python=3.5
            import asyncio

            if asyncio.iscoroutinefunction(target):
                import backoff._async
                retry = backoff._async.retry_exception

        if retry is None:
            retry = _sync.retry_exception

        return retry(target, wait_gen, exception,
                     max_tries, max_time, jitter, giveup,
                     on_success_, on_backoff_, on_giveup_,
                     wait_gen_kwargs)

    # Return a function which decorates a target with a retry loop.
    return decorate
