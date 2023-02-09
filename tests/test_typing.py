import backoff


# No pyunit tests are defined here yet, but the following decorator calls will
# be analyzed by mypy which would have caught a bug the last release.

@backoff.on_exception(
    backoff.expo,
    ValueError,
    jitter=None,
    max_tries=3,
)
def foo():
    raise ValueError()


@backoff.on_exception(
    backoff.constant,
    ValueError,
    interval=1,
    max_tries=3
)
def bar():
    raise ValueError()


@backoff.on_predicate(
    backoff.runtime,
    predicate=lambda r: r.status_code == 429,
    value=lambda r: int(r.headers.get("Retry-After")),
    jitter=None,
)
def baz():
    pass


# Type Successes
for exception in OSError, tuple([OSError]), (OSError, ValueError):
    backoff.on_exception(backoff.expo, exception)


# Type Failures
for exception in OSError(), [OSError], (OSError, ValueError()), "hi", (2, 3):
    try:
        backoff.on_exception(backoff.expo, exception)
        raise AssertionError(f"Expected TypeError for {exception}")
    except TypeError:
        pass
