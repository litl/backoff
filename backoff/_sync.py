# coding:utf-8
import functools
import time

from backoff._common import (_handlers, _init_wait_gen, _log_backoff,
                             _log_giveup, _maybe_call, _next_wait)


def _call_handlers(hdlrs, target, args, kwargs, tries, **extra):
    details = {
        'target': target,
        'args': args,
        'kwargs': kwargs,
        'tries': tries,
    }
    details.update(extra)
    for hdlr in hdlrs:
        hdlr(details)


def retry_predicate(target, wait_gen, predicate,
                    max_tries, jitter,
                    on_success, on_backoff, on_giveup,
                    wait_gen_kwargs):

    success_hdlrs = _handlers(on_success)
    backoff_hdlrs = _handlers(on_backoff, _log_backoff)
    giveup_hdlrs = _handlers(on_giveup, _log_giveup)

    @functools.wraps(target)
    def retry(*args, **kwargs):

        # change names because python 2.x doesn't have nonlocal
        max_tries_ = _maybe_call(max_tries)

        tries = 0
        wait = _init_wait_gen(wait_gen, wait_gen_kwargs)
        while True:
            tries += 1
            details = (target, args, kwargs, tries)

            ret = target(*args, **kwargs)
            if predicate(ret):
                if tries == max_tries_:
                    _call_handlers(giveup_hdlrs, *details, value=ret)
                    break

                seconds = _next_wait(wait, jitter)

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
                    max_tries, jitter, giveup,
                    on_success, on_backoff, on_giveup,
                    wait_gen_kwargs):

    success_hdlrs = _handlers(on_success)
    backoff_hdlrs = _handlers(on_backoff, _log_backoff)
    giveup_hdlrs = _handlers(on_giveup, _log_giveup)

    @functools.wraps(target)
    def retry(*args, **kwargs):
        # change names because python 2.x doesn't have nonlocal
        max_tries_ = _maybe_call(max_tries)

        tries = 0
        wait = _init_wait_gen(wait_gen, wait_gen_kwargs)
        while True:
            tries += 1
            details = (target, args, kwargs, tries)

            try:
                ret = target(*args, **kwargs)
            except exception as e:
                if giveup(e) or tries == max_tries_:
                    _call_handlers(giveup_hdlrs, *details)
                    raise

                seconds = _next_wait(wait, jitter)

                _call_handlers(backoff_hdlrs, *details, wait=seconds)

                time.sleep(seconds)
            else:
                _call_handlers(success_hdlrs, *details)

                return ret
    return retry
