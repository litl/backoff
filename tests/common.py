# coding:utf-8
import collections
import functools


# create event handler which log their invocations to a dict
def _log_hdlrs():
    log = collections.defaultdict(list)

    def log_hdlr(event, details):
        log[event].append(details)

    log_success = functools.partial(log_hdlr, 'success')
    log_backoff = functools.partial(log_hdlr, 'backoff')
    log_giveup = functools.partial(log_hdlr, 'giveup')

    return log, log_success, log_backoff, log_giveup


# decorator that that saves the target as
# an attribute of the decorated function
def _save_target(f):
    f._target = f
    return f
