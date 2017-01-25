# Python 3.4 code and syntax is allowed in this module!


# FIXME remove this pragma when async support is implemented
def retry_predicate(target, wait_gen, predicate,
                    max_tries, jitter,
                    on_success, on_backoff, on_giveup,
                    wait_gen_kwargs):  # pragma: no cover
    raise NotImplementedError('no async support yet')


# FIXME remove this pragma when async support is implemented
def retry_exception(target, wait_gen, exception,
                    max_tries, jitter, giveup,
                    on_success, on_backoff, on_giveup,
                    wait_gen_kwargs):   # pragma: no cover
    raise NotImplementedError('no async support yet')
