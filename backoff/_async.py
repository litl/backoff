# coding:utf-8
import datetime
import functools
# Python 3.4 code and syntax is allowed in this module!
import asyncio

from backoff._common import (_handlers, _init_wait_gen,
                             _log_backoff, _log_giveup, _maybe_call,
                             _next_wait, _total_seconds)


def _ensure_coroutine(coro_or_func):
    if asyncio.iscoroutinefunction(coro_or_func):
        return coro_or_func
    else:
        return asyncio.coroutine(coro_or_func)


def _ensure_coroutines(coros_or_funcs):
    return [_ensure_coroutine(f) for f in coros_or_funcs]


@asyncio.coroutine
def _call_handlers(hdlrs, target, args, kwargs, tries, elapsed, **extra):
    details = {
        'target': target,
        'args': args,
        'kwargs': kwargs,
        'tries': tries,
        'elapsed': elapsed,
    }
    details.update(extra)
    for hdlr in hdlrs:
        yield from hdlr(details)


def retry_predicate(target, wait_gen, predicate,
                    max_tries, max_time, jitter,
                    on_success, on_backoff, on_giveup,
                    wait_gen_kwargs):
    success_hdlrs = _ensure_coroutines(_handlers(on_success))
    backoff_hdlrs = _ensure_coroutines(_handlers(on_backoff, _log_backoff))
    giveup_hdlrs = _ensure_coroutines(_handlers(on_giveup, _log_giveup))

    # Easy to implement, please report if you need this.
    assert not asyncio.iscoroutinefunction(max_tries)
    assert not asyncio.iscoroutinefunction(jitter)

    assert asyncio.iscoroutinefunction(target)

    @functools.wraps(target)
    @asyncio.coroutine
    def retry(*args, **kwargs):

        # change names because python 2.x doesn't have nonlocal
        max_tries_ = _maybe_call(max_tries)
        max_time_ = _maybe_call(max_time)

        tries = 0
        start = datetime.datetime.now()
        wait = _init_wait_gen(wait_gen, wait_gen_kwargs)
        while True:
            tries += 1
            elapsed = _total_seconds(datetime.datetime.now() - start)
            details = (target, args, kwargs, tries, elapsed)

            ret = yield from target(*args, **kwargs)
            if predicate(ret):
                max_tries_exceeded = (tries == max_tries_)
                max_time_exceeded = (max_time_ is not None and
                                     elapsed >= max_time_)

                if max_tries_exceeded or max_time_exceeded:
                    yield from _call_handlers(
                        giveup_hdlrs, *details, value=ret)
                    break

                seconds = _next_wait(wait, jitter, elapsed, max_time_)

                yield from _call_handlers(
                    backoff_hdlrs, *details, value=ret, wait=seconds)

                # Note: there is no convenient way to pass explicit event
                # loop to decorator, so here we assume that either default
                # thread event loop is set and correct (it mostly is
                # by default), or Python >= 3.5.3 or Python >= 3.6 is used
                # where loop.get_event_loop() in coroutine guaranteed to
                # return correct value.
                # See for details:
                #   <https://groups.google.com/forum/#!topic/python-tulip/yF9C-rFpiKk>
                #   <https://bugs.python.org/issue28613>
                yield from asyncio.sleep(seconds)
                continue
            else:
                yield from _call_handlers(success_hdlrs, *details, value=ret)
                break

        return ret

    return retry


def retry_exception(target, wait_gen, exception,
                    max_tries, max_time, jitter, giveup,
                    on_success, on_backoff, on_giveup,
                    wait_gen_kwargs):
    success_hdlrs = _ensure_coroutines(_handlers(on_success))
    backoff_hdlrs = _ensure_coroutines(_handlers(on_backoff, _log_backoff))
    giveup_hdlrs = _ensure_coroutines(_handlers(on_giveup, _log_giveup))
    giveup = _ensure_coroutine(giveup)

    # Easy to implement, please report if you need this.
    assert not asyncio.iscoroutinefunction(max_tries)
    assert not asyncio.iscoroutinefunction(jitter)

    @functools.wraps(target)
    @asyncio.coroutine
    def retry(*args, **kwargs):
        # change names because python 2.x doesn't have nonlocal
        max_tries_ = _maybe_call(max_tries)
        max_time_ = _maybe_call(max_time)

        tries = 0
        start = datetime.datetime.now()
        wait = _init_wait_gen(wait_gen, wait_gen_kwargs)
        while True:
            tries += 1
            elapsed = _total_seconds(datetime.datetime.now() - start)
            details = (target, args, kwargs, tries, elapsed)

            try:
                ret = yield from target(*args, **kwargs)
            except exception as e:
                giveup_result = yield from giveup(e)
                max_tries_exceeded = (tries == max_tries_)
                max_time_exceeded = (max_time_ is not None and
                                     elapsed >= max_time_)

                if giveup_result or max_tries_exceeded or max_time_exceeded:
                    yield from _call_handlers(giveup_hdlrs, *details)
                    raise

                seconds = _next_wait(wait, jitter, elapsed, max_time_)

                yield from _call_handlers(
                    backoff_hdlrs, *details, wait=seconds)

                # Note: there is no convenient way to pass explicit event
                # loop to decorator, so here we assume that either default
                # thread event loop is set and correct (it mostly is
                # by default), or Python >= 3.5.3 or Python >= 3.6 is used
                # where loop.get_event_loop() in coroutine guaranteed to
                # return correct value.
                # See for details:
                #   <https://groups.google.com/forum/#!topic/python-tulip/yF9C-rFpiKk>
                #   <https://bugs.python.org/issue28613>
                yield from asyncio.sleep(seconds)
            else:
                yield from _call_handlers(success_hdlrs, *details)

                return ret
    return retry
