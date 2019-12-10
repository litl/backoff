# coding:utf-8
import collections
import functools


def _logging_handlers():
    """
    Setup up some handlers which log events for testing.

    Returns:
       log - a log mapping events to details
       kwargs - handler kwargs suitable to passing to the decorators
    """
    log = collections.defaultdict(list)

    def handler(event, details):
        log[event].append(details)

    handlers = {
        "on_" + event: functools.partial(handler, event)
        for event in ["try", "backoff", "giveup", "success"]
    }

    return log, handlers


# decorator that that saves the target as
# an attribute of the decorated function
def _save_target(f):
    f._target = f
    return f
