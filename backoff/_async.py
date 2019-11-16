# coding:utf-8
import datetime
import functools
import asyncio  # Python 3.5 code and syntax is allowed in this file
from datetime import timedelta

from backoff._common import (_init_wait_gen, _maybe_call, _next_wait)


def _ensure_coroutine(coro_or_func):
    if asyncio.iscoroutinefunction(coro_or_func):
        return coro_or_func
    else:
        @functools.wraps(coro_or_func)
        async def f(*args, **kwargs):
            return coro_or_func(*args, **kwargs)
        return f


def _ensure_coroutines(coros_or_funcs):
    return [_ensure_coroutine(f) for f in coros_or_funcs]


async def _call_handlers(hdlrs, target, args, kwargs, tries, elapsed, **extra):
    details = {
        'target': target,
        'args': args,
        'kwargs': kwargs,
        'tries': tries,
        'elapsed': elapsed,
    }
    details.update(extra)
    for hdlr in hdlrs:
        await hdlr(details)


def retry_predicate(target, wait_gen, predicate,
                    max_tries, max_time, jitter,
                    on_success, on_backoff, on_giveup,
                    wait_gen_kwargs):
    on_success = _ensure_coroutines(on_success)
    on_backoff = _ensure_coroutines(on_backoff)
    on_giveup = _ensure_coroutines(on_giveup)

    # Easy to implement, please report if you need this.
    assert not asyncio.iscoroutinefunction(max_tries)
    assert not asyncio.iscoroutinefunction(jitter)

    assert asyncio.iscoroutinefunction(target)

    @functools.wraps(target)
    async def retry(*args, **kwargs):

        # change names because python 2.x doesn't have nonlocal
        max_tries_ = _maybe_call(max_tries)
        max_time_ = _maybe_call(max_time)

        tries = 0
        start = datetime.datetime.now()
        wait = _init_wait_gen(wait_gen, wait_gen_kwargs)
        while True:
            tries += 1
            elapsed = timedelta.total_seconds(datetime.datetime.now() - start)
            details = (target, args, kwargs, tries, elapsed)

            ret = await target(*args, **kwargs)
            if predicate(ret):
                max_tries_exceeded = (tries == max_tries_)
                max_time_exceeded = (max_time_ is not None and
                                     elapsed >= max_time_)

                if max_tries_exceeded or max_time_exceeded:
                    await _call_handlers(on_giveup, *details, value=ret)
                    break

                try:
                    seconds = _next_wait(wait, jitter, elapsed, max_time_)
                except StopIteration:
                    await _call_handlers(on_giveup, *details, value=ret)
                    break

                await _call_handlers(on_backoff, *details, value=ret,
                                     wait=seconds)

                # Note: there is no convenient way to pass explicit event
                # loop to decorator, so here we assume that either default
                # thread event loop is set and correct (it mostly is
                # by default), or Python >= 3.5.3 or Python >= 3.6 is used
                # where loop.get_event_loop() in coroutine guaranteed to
                # return correct value.
                # See for details:
                #   <https://groups.google.com/forum/#!topic/python-tulip/yF9C-rFpiKk>
                #   <https://bugs.python.org/issue28613>
                await asyncio.sleep(seconds)
                continue
            else:
                await _call_handlers(on_success, *details, value=ret)
                break

        return ret

    return retry


def retry_exception(target, wait_gen, exception,
                    max_tries, max_time, jitter, giveup,
                    on_success, on_backoff, on_giveup,
                    wait_gen_kwargs):
    on_success = _ensure_coroutines(on_success)
    on_backoff = _ensure_coroutines(on_backoff)
    on_giveup = _ensure_coroutines(on_giveup)
    giveup = _ensure_coroutine(giveup)

    # Easy to implement, please report if you need this.
    assert not asyncio.iscoroutinefunction(max_tries)
    assert not asyncio.iscoroutinefunction(jitter)

    @functools.wraps(target)
    async def retry(*args, **kwargs):
        # change names because python 2.x doesn't have nonlocal
        max_tries_ = _maybe_call(max_tries)
        max_time_ = _maybe_call(max_time)

        tries = 0
        start = datetime.datetime.now()
        wait = _init_wait_gen(wait_gen, wait_gen_kwargs)
        while True:
            tries += 1
            elapsed = timedelta.total_seconds(datetime.datetime.now() - start)
            details = (target, args, kwargs, tries, elapsed)

            try:
                ret = await target(*args, **kwargs)
            except exception as e:
                giveup_result = await giveup(e)
                max_tries_exceeded = (tries == max_tries_)
                max_time_exceeded = (max_time_ is not None and
                                     elapsed >= max_time_)

                if giveup_result or max_tries_exceeded or max_time_exceeded:
                    await _call_handlers(on_giveup, *details)
                    raise

                try:
                    seconds = _next_wait(wait, jitter, elapsed, max_time_)
                except StopIteration:
                    await _call_handlers(on_giveup, *details)
                    raise e

                await _call_handlers(on_backoff, *details, wait=seconds)

                # Note: there is no convenient way to pass explicit event
                # loop to decorator, so here we assume that either default
                # thread event loop is set and correct (it mostly is
                # by default), or Python >= 3.5.3 or Python >= 3.6 is used
                # where loop.get_event_loop() in coroutine guaranteed to
                # return correct value.
                # See for details:
                #   <https://groups.google.com/forum/#!topic/python-tulip/yF9C-rFpiKk>
                #   <https://bugs.python.org/issue28613>
                await asyncio.sleep(seconds)
            else:
                await _call_handlers(on_success, *details)

                return ret
    return retry
