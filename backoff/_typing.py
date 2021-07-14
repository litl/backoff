# coding:utf-8
import logging
import sys
from typing import (Any, Callable, Dict, Generator, Sequence, Tuple, Union,
                    TYPE_CHECKING, TypeVar)

T = TypeVar("T")

if sys.version_info >= (3, 8):
    from typing import TypedDict
elif TYPE_CHECKING:
    try:
        from typing_extensions import TypedDict
    except ImportError:
        TypedDict = object
else:
    TypedDict = object


class Details(TypedDict):
    """Invocation details for a handler.

    The following keys are valid for the `on_exception` decorator,
    except for the `on_backoff` handler, which uses the
    `DetailsBackoff` type instead.

    Available keys:

        `target` : reference to the function or method being invoked
        `args`   : positional arguments to func
        `kwargs` : keyword arguments to func
        `tries`  : number of invocation tries so far
        `elapsed`: elapsed time in seconds so far
        `wait`   : seconds to wait
    """

    target: Callable[..., Any]
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    tries: int
    elapsed: float


class _DetailsBackoffMixin(TypedDict):
    """Extra keys specific to `on_backoff` handlers."""

    wait: float


class DetailsBackoff(Details, _DetailsBackoffMixin):
    """Invocation details for a backoff handler.

    The following keys are valid for the `on_exception` decorator,
    and only for the `on_backoff` handler. Other handlers use the
    `Details` type instead.

    Available keys:

        `target` : reference to the function or method being invoked
        `args`   : positional arguments to func
        `kwargs` : keyword arguments to func
        `tries`  : number of invocation tries so far
        `elapsed`: elapsed time in seconds so far
        `wait`   : seconds to wait
    """


class DetailsPredicate(Details):
    """Invocation details for a predicate handlers.

    The following keys are valid for the `on_predicate` decorator,
    except for the `on_backoff` handler, which uses the
    `DetailsPredicateBackoff` type instead.

    Available keys:

        `target` : reference to the function or method being invoked
        `args`   : positional arguments to func
        `kwargs` : keyword arguments to func
        `tries`  : number of invocation tries so far
        `elapsed`: elapsed time in seconds so far
        `value`  : value triggering backoff
    """

    value: Any


class DetailsPredicateBackoff(DetailsPredicate, _DetailsBackoffMixin):
    """Invocation details for a predicate backoff handlers.

    The following keys are valid for the `on_predicate` decorator,
    and only for the `on_backoff` handler. Other handlers use the
    `DetailsPredicate` type instead.

    Available keys:

        `target` : reference to the function or method being invoked
        `args`   : positional arguments to func
        `kwargs` : keyword arguments to func
        `tries`  : number of invocation tries so far
        `elapsed`: elapsed time in seconds so far
        `wait`   : seconds to wait
        `value`  : value triggering backoff
    """


_HandlerT = Callable[[T], None]
_CallableT = TypeVar('_CallableT', bound=Callable[..., Any])
_HandlerPredicate = _HandlerT[DetailsPredicate]
_HandlerPredicateBackoff = _HandlerT[DetailsPredicateBackoff]
_Handler = _HandlerT[Details]
_HandlerBackoff = _HandlerT[DetailsBackoff]
_Jitterer = Callable[[float], float]
_MaybeCallable = Union[T, Callable[[], T]]
_MaybeLogger = Union[str, logging.Logger]
_MaybeSequence = Union[T, Sequence[T]]
_Predicate = Callable[[T], bool]
_WaitGenerator = Callable[..., Generator[float, None, None]]
