# coding:utf-8

import functools
import logging
import sys
import traceback
import warnings


# python 2.7 -> 3.x compatibility for str and unicode
try:
    basestring
except NameError:  # pragma: python=3.5
    basestring = str


# Use module-specific logger with a default null handler.
_logger = logging.getLogger('backoff')
_logger.addHandler(logging.NullHandler())  # pragma: no cover
_logger.setLevel(logging.INFO)


# Evaluate arg that can be either a fixed value or a callable.
def _maybe_call(f, *args, **kwargs):
    return f(*args, **kwargs) if callable(f) else f

def _init_wait_gen(wait_gen, wait_gen_kwargs):
    prepared_kwargs = _prepare_kwargs(wait_gen_kwargs)
    return wait_gen(**prepared_kwargs)

def _prepare_kwargs(kwargs):
    return {k: _maybe_call(v) for k, v in kwargs.items()}

def _next_wait(wait_gen, jitter, elapsed, max_time):
    wait_seconds = next(wait_gen)
    return _get_wait_seconds(wait_seconds, jitter, elapsed, max_time)

def _get_wait_seconds(wait_seconds, jitter, elapsed, max_time):
    try:
        if jitter is not None:
            seconds = jitter(wait_seconds)
        else:
            seconds = wait_seconds
    except TypeError:
        warnings.warn(
            "Nullary jitter function signature is deprecated. Use "
            "unary signature accepting a wait value in seconds and "
            "returning a jittered version of it.",
            DeprecationWarning,
            stacklevel=2,
        )

        seconds = wait_seconds + jitter()

    # don't sleep longer than remaining allotted max_time
    if max_time is not None:
        seconds = min(seconds, max_time - elapsed)

    return seconds


def _prepare_logger(logger):
    if isinstance(logger, basestring):
        logger = logging.getLogger(logger)
    return logger


# Configure handler list with user specified handler and optionally
# with a default handler bound to the specified logger.
def _config_handlers(
    user_handlers, default_handler=None, logger=None, log_level=None
):
    handlers = []
    if logger is not None:
        assert log_level is not None, "Log level is not specified"
        # bind the specified logger to the default log handler
        log_handler = functools.partial(
            default_handler, logger=logger, log_level=log_level
        )
        handlers.append(log_handler)

    if user_handlers is None:
        return handlers

    # user specified handlers can either be an iterable of handlers
    # or a single handler. either way append them to the list.
    if hasattr(user_handlers, '__iter__'):
        # add all handlers in the iterable
        handlers += list(user_handlers)
    else:
        # append a single handler
        handlers.append(user_handlers)

    return handlers


# Default backoff handler
def _log_backoff(details, logger, log_level):
    msg = "Backing off %s(...) for %.1fs (%s)"
    log_args = [details['target'].__name__, details['wait']]

    exc_typ, exc, _ = sys.exc_info()
    if exc is not None:
        exc_fmt = traceback.format_exception_only(exc_typ, exc)[-1]
        log_args.append(exc_fmt.rstrip("\n"))
    else:
        log_args.append(details['value'])
    logger.log(log_level, msg, *log_args)


# Default giveup handler
def _log_giveup(details, logger, log_level):
    msg = "Giving up %s(...) after %d tries (%s)"
    log_args = [details['target'].__name__, details['tries']]

    exc_typ, exc, _ = sys.exc_info()
    if exc is not None:
        exc_fmt = traceback.format_exception_only(exc_typ, exc)[-1]
        log_args.append(exc_fmt.rstrip("\n"))
    else:
        log_args.append(details['value'])

    logger.log(log_level, msg, *log_args)
