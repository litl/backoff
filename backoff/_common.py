# coding:utf-8

import logging
import sys
import traceback


# Use module-specific logger with a default null handler.
logger = logging.getLogger('backoff')

if sys.version_info < (2, 7, 0):  # pragma: no cover
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass
    logger.addHandler(NullHandler())
else:
    logger.addHandler(logging.NullHandler())  # pragma: no cover

logger.setLevel(logging.INFO)


# Evaluate arg that can be either a fixed value or a callable.
def _maybe_call(f, *args, **kwargs):
    return f(*args, **kwargs) if callable(f) else f


def _init_wait_gen(wait_gen, wait_gen_kwargs):
    # there are no dictionary comprehensions in python 2.6
    kwargs = dict((k, _maybe_call(v))
                  for k, v in wait_gen_kwargs.items())
    return wait_gen(**kwargs)


def _next_wait(wait, jitter, elapsed, max_time):
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

    # don't sleep longer than remaining alloted max_time
    if max_time is not None:
        seconds = min(seconds, max_time - elapsed)

    return seconds


# Create default handler list from keyword argument
def _handlers(hdlr, default=None):
    defaults = [default] if default is not None else []

    if hdlr is None:
        return defaults

    if hasattr(hdlr, '__iter__'):
        return defaults + list(hdlr)

    return defaults + [hdlr]


# Default backoff handler
def _log_backoff(details):
    fmt = "Backing off {0}(...) for {1:.1f}s"
    msg = fmt.format(details['target'].__name__, details['wait'])

    exc_typ, exc, _ = sys.exc_info()
    if exc is not None:
        exc_fmt = traceback.format_exception_only(exc_typ, exc)[-1]
        msg = "{0} ({1})".format(msg, exc_fmt.rstrip("\n"))
    else:
        msg = "{0} ({1})".format(msg, details['value'])
    logger.info(msg)


# Default giveup handler
def _log_giveup(details):
    fmt = "Giving up {0}(...) after {1} tries"
    msg = fmt.format(details['target'].__name__, details['tries'])

    exc_typ, exc, _ = sys.exc_info()
    if exc is not None:
        exc_fmt = traceback.format_exception_only(exc_typ, exc)[-1]
        msg = "{0} ({1})".format(msg, exc_fmt.rstrip("\n"))
    else:
        msg = "{0} ({1})".format(msg, details['value'])

    logger.error(msg)


# Python 2.6 datetime.timedelta does not have total_seconds()
# so we do our own implementation here.
def _total_seconds(timedelta):
    return (
        (timedelta.microseconds + 0.0 +
         (timedelta.seconds + timedelta.days * 24 * 3600) * 10**6) / 10**6)
