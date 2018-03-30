# coding:utf-8
from __future__ import unicode_literals

import operator
import sys

from backoff._jitter import full_jitter
from backoff import _sync


def on_predicate(wait_gen,
                 predicate=operator.not_,
                 max_tries=None,
                 max_time=None,
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
        **wait_gen_kwargs: Any additional keyword args specified will be
            passed to wait_gen when it is initialized.  Any callable
            args will first be evaluated and their return values passed.
            This is useful for runtime configuration.
    """
    def decorate(target):
        retry = None
        if sys.version_info[:2] >= (3, 4):  # pragma: python=3.4
            import asyncio

            if asyncio.iscoroutinefunction(target):
                import backoff._async
                retry = backoff._async.retry_predicate

            else:
                # Verify that sync version is not being run from coroutine
                # (that would lead to event loop hiccups).
                try:
                    asyncio.get_event_loop()
                except RuntimeError:
                    # Event loop not set for this thread.
                    pass
                else:
                    if asyncio.Task.current_task() is not None:
                        raise TypeError(
                            "backoff.on_predicate applied to a regular "
                            "function inside coroutine, this will lead "
                            "to event loop hiccups. "
                            "Use backoff.on_predicate on coroutines in "
                            "asynchronous code.")

        if retry is None:
            retry = _sync.retry_predicate

        return retry(target, wait_gen, predicate,
                     max_tries, max_time, jitter,
                     on_success, on_backoff, on_giveup,
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
        **wait_gen_kwargs: Any additional keyword args specified will be
            passed to wait_gen when it is initialized.  Any callable
            args will first be evaluated and their return values passed.
            This is useful for runtime configuration.
    """
    def decorate(target):
        retry = None
        if sys.version_info[:2] >= (3, 4):   # pragma: python=3.4
            import asyncio

            if asyncio.iscoroutinefunction(target):
                import backoff._async
                retry = backoff._async.retry_exception
            else:
                # Verify that sync version is not being run from coroutine
                # (that would lead to event loop hiccups).
                try:
                    asyncio.get_event_loop()
                except RuntimeError:
                    # Event loop not set for this thread.
                    pass
                else:
                    if asyncio.Task.current_task() is not None:
                        raise TypeError(
                            "backoff.on_exception applied to a regular "
                            "function inside coroutine, this will lead "
                            "to event loop hiccups. "
                            "Use backoff.on_exception on coroutines in "
                            "asynchronous code.")

        if retry is None:
            retry = _sync.retry_exception

        return retry(target, wait_gen, exception,
                     max_tries, max_time, jitter, giveup,
                     on_success, on_backoff, on_giveup,
                     wait_gen_kwargs)

    # Return a function which decorates a target with a retry loop.
    return decorate
