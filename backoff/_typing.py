# coding:utf-8
import logging
import sys
from typing import (Any, Callable, Dict, Generator, Sequence, Tuple, Union,
                    TypeVar)

T = TypeVar("T")

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    try:
        from typing_extensions import TypedDict
    except ImportError:
        TypedDict = object


class _Details(TypedDict):
    target: Callable[..., Any]
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    tries: int
    elapsed: float


class Details(_Details, total=False):
    wait: float  # this key will be present in the on_backoff handler case for either decorator
    value: Any  # this key will be present in the on_predicate decorator case


_CallableT = TypeVar('_CallableT', bound=Callable[..., Any])
_Handler = Callable[[Details], None]
_Jitterer = Callable[[float], float]
_MaybeCallable = Union[T, Callable[[], T]]
_MaybeLogger = Union[str, logging.Logger]
_MaybeSequence = Union[T, Sequence[T]]
_Predicate = Callable[[T], bool]
_WaitGenerator = Callable[..., Generator[float, None, None]]
