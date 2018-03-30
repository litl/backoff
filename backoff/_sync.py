# coding:utf-8
import datetime
import functools
import time

from backoff._common import (_handlers, _init_wait_gen, _log_backoff,
                             _log_giveup, _maybe_call, _next_wait,
                             _total_seconds)


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
                    max_tries, max_time, jitter,
                    on_success, on_backoff, on_giveup,
                    wait_gen_kwargs):

    success_hdlrs = _handlers(on_success)
    backoff_hdlrs = _handlers(on_backoff, _log_backoff)
    giveup_hdlrs = _handlers(on_giveup, _log_giveup)

    @functools.wraps(target)
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

            ret = target(*args, **kwargs)
            if predicate(ret):
                max_tries_exceeded = (tries == max_tries_)
                max_time_exceeded = (max_time_ is not None and
                                     elapsed >= max_time_)

                if max_tries_exceeded or max_time_exceeded:
                    _call_handlers(giveup_hdlrs, *details, value=ret)
                    break

                seconds = _next_wait(wait, jitter, elapsed, max_time_)

                _call_handlers(backoff_hdlrs, *details,
                               value=ret, wait=seconds)

                time.sleep(seconds)
                continue
            else:
                _call_handlers(success_hdlrs, *details, value=ret)
                break

        return ret

    return retry


def retry_exception(target, wait_gen, exception,
                    max_tries, max_time, jitter, giveup,
                    on_success, on_backoff, on_giveup,
                    wait_gen_kwargs):

    success_hdlrs = _handlers(on_success)
    backoff_hdlrs = _handlers(on_backoff, _log_backoff)
    giveup_hdlrs = _handlers(on_giveup, _log_giveup)

    @functools.wraps(target)
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
                ret = target(*args, **kwargs)
            except exception as e:
                max_tries_exceeded = (tries == max_tries_)
                max_time_exceeded = (max_time_ is not None and
                                     elapsed >= max_time_)

                if giveup(e) or max_tries_exceeded or max_time_exceeded:
                    _call_handlers(giveup_hdlrs, *details)
                    raise

                seconds = _next_wait(wait, jitter, elapsed, max_time_)

                _call_handlers(backoff_hdlrs, *details, wait=seconds)

                time.sleep(seconds)
            else:
                _call_handlers(success_hdlrs, *details)

                return ret
    return retry
