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
        pass
try:
    _ = TypedDict
except NameError:
    DetailsException = DetailsPredicate = Dict[str, Any]  # type: ignore
else:
    class _Details(TypedDict):
        """Shared keys available for all invocation details."""
        target: Callable[..., Any]
        args: Tuple[Any, ...]
        kwargs: Dict[str, Any]
        tries: int
        elapsed: float

    class DetailsException(_Details):
        """Invocation details for on_exception backoff handlers.

        Availble keys:

            `target` : reference to the function or method being invoked
            `args`   : positional arguments to func
            `kwargs` : keyword arguments to func
            `tries`  : number of invocation tries so far
            `elapsed`: elapsed time in seconds so far
            `wait`   : seconds to wait
        """
        wait: float

    class DetailsPredicate(_Details):
        """Invocation details for on_predicate backoff handlers.

        Availble keys:

            `target` : reference to the function or method being invoked
            `args`   : positional arguments to func
            `kwargs` : keyword arguments to func
            `tries`  : number of invocation tries so far
            `elapsed`: elapsed time in seconds so far
            `value`  : value triggering backoff
        """
        value: Any

_CallableT = TypeVar('_CallableT', bound=Callable[..., Any])
_HandlerPredicate = Callable[[DetailsPredicate], None]
_HandlerDetails = Callable[[DetailsException], None]
_Jitterer = Callable[[float], float]
_MaybeCallable = Union[T, Callable[[], T]]
_MaybeLogger = Union[str, logging.Logger]
_MaybeSequence = Union[T, Sequence[T]]
_Predicate = Callable[[T], bool]
_WaitGenerator = Callable[..., Generator[float, None, None]]
