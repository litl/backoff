# backoff

[![Build Status](https://travis-ci.org/litl/backoff.svg?branch=master)](https://travis-ci.org/litl/backoff?branch=master) [![Coverage Status](https://coveralls.io/repos/litl/backoff/badge.svg?branch=master)](https://coveralls.io/r/litl/backoff?branch=master)

Function decoration for backoff and retry

This module provides function decorators which can be used to wrap a
function such that it will be retried until some condition is met. It
is meant to be of use when accessing unreliable resources with the
potential for intermittent failures i.e. network resources and external
APIs. Somewhat more generally, it may also be of use for dynamically
polling resources for externally generated content.

## Examples

*Since Kenneth Reitz's [requests](http://python-requests.org) module
has become a defacto standard for HTTP clients in python, networking
examples below are written using it, but it is in no way required by
the backoff module.*

### @backoff.on_exception

The on_exception decorator is used to retry when a specified exception
is raised. Here's an example using exponential backoff when any
requests exception is raised:

    @backoff.on_exception(backoff.expo,
                          requests.exceptions.RequestException,
                          max_tries=8)
    def get_url(url):
        return requests.get(url)

### @backoff.on_predicate

The on_predicate decorator is used to retry when a particular condition
is true of the return value of the target function.  This may be useful
when polling a resource for externally generated content.

Here's an example which uses a fibonacci sequence backoff when the
return value of the target function is the empty list:

    @backoff.on_predicate(backoff.fibo, lambda x: x == [], max_value=13)
    def poll_for_messages(queue):
        return queue.get()

Extra keyword arguments are passed when initializing the
wait_generator, so the max_value param above is used to initialize the
fibo generator.

When not specified, the predicate param defaults to the falsey test,
so the above can more concisely be written:

    @backoff.on_predicate(backoff.fibo, max_value=13)
    def poll_for_message(queue)
        return queue.get()

More simply, a function which continues polling every second until it
gets a non falsey result could be defined like like this:

    @backoff.on_predicate(backoff.constant, interval=1)
    def poll_for_message(queue)
        return queue.get()

### Using multiple decorators

It can also be useful to combine backoff decorators to define
different backoff behavior for different cases:

    @backoff.on_predicate(backoff.fibo, max_value=13)
    @backoff.on_exception(backoff.expo,
                          requests.exceptions.HTTPError,
                          max_tries=4)
    @backoff.on_exception(backoff.expo,
                          requests.exceptions.TimeoutError,
                          max_tries=8)
    def poll_for_message(queue):
        return queue.get()

### Event handlers

Both backoff decorators optionally accept event handler functions as the
keyword arguments: on_success, on_backoff, and on_giveup. This may be
useful in reporting statistics or other custom logging. Here's an
example of using event handler to log statsd statistics for each event
type:

    import statsd

    def success_stat(invoc, tries):
        f, args, kwargs = invoc
        statsd.statsd.histogram("backoff.success.%s" % f.name, tries)

    def backoff_stat(invoc, wait, exception):
        f, args, kwargs = invoc
        statsd.statsd.histogram("backoff.retry.%s" % f.name, wait)

    def giveup_stat(invoc, tries, exception):
        f, args, kwargs = invoc
        statsd.statsd.histogram("backoff.giveup.%s" % f.name, tries)

    @backoff.on_exception(backoff.expo,
                          requests.exceptions.RequestException,
                          max_tries=8,
                          on_success=success_stat,
                          on_backoff=backoff_stat,
                          on_giveup=giveup_stat)
    def get_url(url):
        return requests.get(url)

The first parameter to all three handler types is a tuple consisting of
the consisting of the function being invoked, the args lists and the
kwargs dict. The remainder of the parameters are defined as keyword
arguments appropriate to the handler type.

Iterables of handler functions are also accepted.

### Logging configuration

Errors and backoff/retry attempts are logged to the 'backoff' logger.
By default, this logger is configured with a NullHandler, so there will
be nothing output unless you configure a handler. Programmatically,
this might be accomplished with something as simple as:

    logging.getLogger('backoff').addHandler(logging.StreamHandler())

The default logging level is ERROR, which correponds to logging anytime
max_tries is exceeded as well as any time a retryable exception is
raised. If you would instead like to log any type of retry, you can
instead set the logger level to INFO:

    logging.getLogger('backoff').setLevel(logging.INFO)

