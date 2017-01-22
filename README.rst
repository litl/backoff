backoff
=======

.. image:: https://travis-ci.org/litl/backoff.svg?branch=master
    :target: https://travis-ci.org/litl/backoff?branch=master
.. image:: https://coveralls.io/repos/litl/backoff/badge.svg?branch=master
    :target: https://coveralls.io/r/litl/backoff?branch=master

**Function decoration for backoff and retry**

This module provides function decorators which can be used to wrap a
function such that it will be retried until some condition is met. It
is meant to be of use when accessing unreliable resources with the
potential for intermittent failures i.e. network resources and external
APIs. Somewhat more generally, it may also be of use for dynamically
polling resources for externally generated content.

Examples
========

Since Kenneth Reitz's `requests <http://python-requests.org>`_ module
has become a defacto standard for HTTP clients in python, networking
examples below are written using it, but it is in no way required by
the backoff module.

@backoff.on_exception
---------------------

The ``on_exception`` decorator is used to retry when a specified exception
is raised. Here's an example using exponential backoff when any
``requests`` exception is raised:

.. code-block:: python

    @backoff.on_exception(backoff.expo,
                          requests.exceptions.RequestException,
                          max_tries=8)
    def get_url(url):
        return requests.get(url)

The decorator will also accept a tuple of exceptions for cases where
you want the same backoff behavior for more than one exception type:

.. code-block:: python

    @backoff.on_exception(backoff.expo,
                          (requests.exceptions.Timeout,
                           requests.exceptions.ConnectionError),
                          max_tries=8)
    def get_url(url):
        return requests.get(url)

In some cases the raised exception instance itself may need to be
inspected in order to determine if it is a retryable condition. The
``giveup`` keyword arg can be used to specify a function which accepts
the exception and returns a truthy value if the exception should not
be retried:

.. code-block:: python

    def fatal_code(e):
        return 400 <= e.response.status_code < 500

    @backoff.on_exception(backoff.expo,
                          requests.exceptions.RequestException,
                          max_tries=8,
                          giveup=fatal_code)
    def get_url(url):
        return requests.get(url)


@backoff.on_predicate
---------------------

The ``on_predicate`` decorator is used to retry when a particular
condition is true of the return value of the target function.  This may
be useful when polling a resource for externally generated content.

Here's an example which uses a fibonacci sequence backoff when the
return value of the target function is the empty list:

.. code-block:: python

    @backoff.on_predicate(backoff.fibo, lambda x: x == [], max_value=13)
    def poll_for_messages(queue):
        return queue.get()

Extra keyword arguments are passed when initializing the
wait generator, so the ``max_value`` param above is passed as a keyword
arg when initializing the fibo generator.

When not specified, the predicate param defaults to the falsey test,
so the above can more concisely be written:

.. code-block:: python

    @backoff.on_predicate(backoff.fibo, max_value=13)
    def poll_for_message(queue)
        return queue.get()

More simply, a function which continues polling every second until it
gets a non-falsey result could be defined like like this:

.. code-block:: python

    @backoff.on_predicate(backoff.constant, interval=1)
    def poll_for_message(queue)
        return queue.get()


@backoff.factor
---------------

The ``factor`` decorator is used to ajust other wait generator. 

    @backoff.on_predicate(backoff.factor(backoff.constant, 60), interval=1)
    def poll_for_message(queue)
        return queue.get()

Here `backoff.factor(backoff.constant, 60)` make backoff to sleep 60 times 
longer than original wait generator.


Jitter
------

A jitter algorithm can be supplied with the ``jitter`` keyword arg to
either of the backoff decorators. This argument should be a function
accepting the original unadulterated backoff value and returning it's
jittered counterpart.

As of version 1.2, the default jitter function ``backoff.full_jitter``
implements the 'Full Jitter' algorithm as defined in the AWS
Architecture Blog's `Exponential Backoff And Jitter
<https://www.awsarchitectureblog.com/2015/03/backoff.html>`_ post.

Previous versions of backoff defaulted to adding some random number of
milliseconds (up to 1s) to the raw sleep value. If desired, this
behavior is now available as ``backoff.random_jitter``.

Using multiple decorators
-------------------------

The backoff decorators may also be combined to specify different
backoff behavior for different cases:

.. code-block:: python

    @backoff.on_predicate(backoff.fibo, max_value=13)
    @backoff.on_exception(backoff.expo,
                          requests.exceptions.HTTPError,
                          max_tries=4)
    @backoff.on_exception(backoff.expo,
                          requests.exceptions.TimeoutError,
                          max_tries=8)
    def poll_for_message(queue):
        return queue.get()

Runtime Configuration
---------------------

The decorator functions ``on_exception`` and ``on_predicate`` are
generally evaluated at import time. This is fine when the keyword args
are passed as constant values, but suppose we want to consult a
dictionary with configuration options that only become available at
runtime. The relevant values are not available at import time. Instead,
decorator functions can be passed callables which are evaluated at
runtime to obtain the value:

.. code-block:: python

    def lookup_max_tries():
        # pretend we have a global reference to 'app' here
        # and that it has a dictionary-like 'config' property
        return app.config["BACKOFF_MAX_TRIES"]

    @backoff.on_exception(backoff.expo,
                          ValueError,
                          max_tries=lookup_max_tries)

More cleverly, you might define a function which returns a lookup
function for a specified variable:

.. code-block:: python

    def config(app, name):
        return functools.partial(app.config.get, name)

    @backoff.on_exception(backoff.expo,
                          ValueError,
                          max_value=config(app, "BACKOFF_MAX_VALUE")
                          max_tries=config(app, "BACKOFF_MAX_TRIES"))

Event handlers
--------------

Both backoff decorators optionally accept event handler functions
using the keyword arguments ``on_success``, ``on_backoff``, and ``on_giveup``.
This may be useful in reporting statistics or performing other custom
logging.

Handlers must be callables with a unary signature accepting a dict
argument. This dict contains the details of the invocation. Valid keys
include:

* *target*: reference to the function or method being invoked
* *args*: positional arguments to func
* *kwargs*: keyword arguments to func
* *tries*: number of invocation tries so far
* *wait*: seconds to wait (``on_backoff`` handler only)
* *value*: value triggering backoff (``on_predicate`` decorator only)

A handler which prints the details of the backoff event could be
implemented like so:

.. code-block:: python

    def backoff_hdlr(details):
        print ("Backing off {wait:0.1f} seconds afters {tries} tries "
               "calling function {func} with args {args} and kwargs "
               "{kwargs}".format(**details))

    @backoff.on_exception(backoff.expo,
                          requests.exceptions.RequestException,
                          on_backoff=backoff_hdlr)
    def get_url(url):
        return requests.get(url)

**Multiple handlers per event type**

In all cases, iterables of handler functions are also accepted, which
are called in turn. For example, you might provide a simple list of
handler functions as the value of the ``on_backoff`` keyword arg:

.. code-block:: python

    @backoff.on_exception(backoff.expo,
                          requests.exceptions.RequestException,
                          on_backoff=[backoff_hdlr1, backoff_hdlr2])
    def get_url(url):
        return requests.get(url)

**Getting exception info**

In the case of the ``on_exception`` decorator, all ``on_backoff`` and
``on_giveup`` handlers are called from within the except block for the
exception being handled. Therefore exception info is available to the
handler functions via the python standard library, specifically
``sys.exc_info()`` or the ``traceback`` module.

Logging configuration
---------------------

Errors and backoff and retry attempts are logged to the 'backoff'
logger. By default, this logger is configured with a NullHandler, so
there will be nothing output unless you configure a handler.
Programmatically, this might be accomplished with something as simple
as:

.. code-block:: python

    logging.getLogger('backoff').addHandler(logging.StreamHandler())

The default logging level is ERROR, which corresponds to logging anytime
``max_tries`` is exceeded as well as any time a retryable exception is
raised. If you would instead like to log any type of retry, you can
set the logger level to INFO:

.. code-block:: python

    logging.getLogger('backoff').setLevel(logging.INFO)
