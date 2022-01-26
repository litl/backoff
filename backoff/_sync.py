# coding:utf-8
import functools
import time

from backoff._common import (_init_wait_gen, _maybe_call, _next_wait)


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
        hdlr(details)


def retry_predicate(target, wait_gen, predicate,
                    *,
                    max_tries, max_time, jitter,
                    on_success, on_backoff, on_giveup,
                    monotonic_time=None,
                    sleep=None,
                    wait_gen_kwargs):

    @functools.wraps(target)
    def retry(*args, **kwargs):

        # update variables from outer function args
        nonlocal max_tries, max_time
        max_tries = _maybe_call(max_tries)
        max_time = _maybe_call(max_time)

        tries = 0
        start = (monotonic_time or time.monotonic)()
        wait = _init_wait_gen(wait_gen, wait_gen_kwargs)
        while True:
            tries += 1
            elapsed = (monotonic_time or time.monotonic)() - start
            details = {
                "target": target,
                "args": args,
                "kwargs": kwargs,
                "tries": tries,
                "elapsed": elapsed,
            }

            ret = target(*args, **kwargs)
            if predicate(ret):
                max_tries_exceeded = (tries == max_tries)
                max_time_exceeded = (max_time is not None and
                                     elapsed >= max_time)

                if max_tries_exceeded or max_time_exceeded:
                    _call_handlers(on_giveup, **details, value=ret)
                    break

                try:
                    seconds = _next_wait(wait, ret, jitter, elapsed, max_time)
                except StopIteration:
                    _call_handlers(on_giveup, **details)
                    break

                _call_handlers(on_backoff, **details,
                               value=ret, wait=seconds)

                (sleep or time.sleep)(seconds)
                continue
            else:
                _call_handlers(on_success, **details, value=ret)
                break

        return ret

    return retry


def retry_exception(target, wait_gen, exception,
                    *,
                    max_tries, max_time, jitter, giveup,
                    on_success, on_backoff, on_giveup, raise_on_giveup,
                    monotonic_time=None,
                    sleep=None,
                    wait_gen_kwargs):

    @functools.wraps(target)
    def retry(*args, **kwargs):

        # update variables from outer function args
        nonlocal max_tries, max_time
        max_tries = _maybe_call(max_tries)
        max_time = _maybe_call(max_time)

        tries = 0
        start = (monotonic_time or time.monotonic)()
        wait = _init_wait_gen(wait_gen, wait_gen_kwargs)
        while True:
            tries += 1
            elapsed = (monotonic_time or time.monotonic)() - start
            details = {
                "target": target,
                "args": args,
                "kwargs": kwargs,
                "tries": tries,
                "elapsed": elapsed,
            }

            try:
                ret = target(*args, **kwargs)
            except exception as e:
                max_tries_exceeded = (tries == max_tries)
                max_time_exceeded = (max_time is not None and
                                     elapsed >= max_time)

                if giveup(e) or max_tries_exceeded or max_time_exceeded:
                    _call_handlers(on_giveup, **details)
                    if raise_on_giveup:
                        raise
                    return None

                try:
                    seconds = _next_wait(wait, e, jitter, elapsed, max_time)
                except StopIteration:
                    _call_handlers(on_giveup, **details)
                    raise e

                _call_handlers(on_backoff, **details, wait=seconds)

                (sleep or time.sleep)(seconds)
            else:
                _call_handlers(on_success, **details)

                return ret
    return retry
