# coding:utf-8
import logging
from typing import Callable, Generator, Sequence, Union, TypeVar


T = TypeVar("T")

_Handler = Callable[[dict], None]
_Jitterer = Callable[[float], float]
_MaybeCallable = Union[T, Callable[[], T]]
_MaybeLogger = Union[str, logging.Logger]
_MaybeSequence = Union[T, Sequence[T]]
_Predicate = Callable[[T], bool]
_WaitGenerator = Callable[..., Generator[float, None, None]]
