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
