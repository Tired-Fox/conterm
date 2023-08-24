from __future__ import annotations
from enum import Enum
from threading import Lock
from typing import Any, Callable, Generic, Literal, TypeVar


class State:
    def __init__(self):
        self._state_ = {}

    def get(self, key: str, default: Any | None = None):
        return self._state_.get(key, default)

    def set(self, key: str, value: Any):
        self._state_[key] = value

T = TypeVar("T")
class Locker(Generic[T]):
    """
    A thread safe container that will lock the data on access.
    Use the `with` keyword for a set scope or use the `inner` property to
    get a Object that contains the data. The thread is locked and the object
    has full access to the data. When the object is deleted by the GC or with the `del`
    keyword it will release the lock on the data allowing for the parent Locker to access
    the data again.
    """
    def __init__(self, data: T):
        self._data_ = data
        self.lock = Lock()

    @property
    def inner(self) -> Locker.Data:
        return Locker.Data(self._data_, self.lock)

    def __enter__(self) -> T:
        self.lock.acquire(blocking=True)
        return self._data_

    def __exit__(self, et, ev, etb):
        self.lock.release()
        if ev is not None:
            raise ev

    class Data:
        def __init__(self, data: T, lock: Lock):
            self._lock_ = lock
            lock.acquire(blocking=True)
            self.data: T = data

        def __del__(self):
            self._lock_.release()

class Rect:
    __slots__ = ("left", "right", "top", "bottom")

    def __init__(
        self,
        x: int | float | Callable[[int], int],
        y: int | float | Callable[[int], int],
        w: int | float | Callable[[int], int],
        h: int | float | Callable[[int], int],
        mw: int,
        mh: int
    ):
        self.left = min(calc_size(x, mw), mw - 1)
        self.right = min(self.left + calc_size(w, mw), mw)
        self.top = min(calc_size(y, mh), mh - 1)
        self.bottom = min(self.top + calc_size(h, mh), mh)

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    def points(self) -> tuple[int, int, int, int]:
        """Left, top, right, and bottom points respectively."""
        return (self.left, self.top, self.right, self.bottom)

    def dims(self) -> tuple[int, int]:
        """Width and height respectively."""
        return (self.width, self.height)

class Command(Enum):
    NOOP = -1
    """No Operation. Do nothing."""
    Quit = 0
    """Quit the application."""
    Deselect = 1
    """Deselect the node if posible."""
    Select = 2
    """Select the node or item if possible."""

def norm_sizing(
    sizing: SizeType 
) -> tuple[int, int, int, int]:
    """Sizing left, top, right, and bottom respectively.

    Args:
        sizing (int | tuple[int, int] | tuple[int, int, int, int]): tuple of left, top, right and bottom
            int values. Can also be a tuple of inline and block int values that spread to the four respective values. Can finally be a single int value that spreads to all four values.
    """
    if isinstance(sizing, tuple):
        if len(sizing) == 2:
            return (sizing[0], sizing[1], sizing[0], sizing[1])
        elif len(sizing) == 4:
            return sizing
        else:
            raise ValueError(
                f"Invalid tuple of sizing values. Expected 2 or 4 found {len(sizing)}"
            )
    elif isinstance(sizing, int):
        return tuple([sizing for _ in range(4)])
    else:
        raise ValueError(f"Invalid sizing type; was {type(sizing)}")

def calc_size(val: int | float | Callable[[int], int], total: int) -> int:
    if callable(val):
        val = val(total)
    elif isinstance(val, float):
        val = round(val * total)
    return val

def clamp(value: int, lower, upper) -> int:
    return max(lower, min(value, upper))

def align(collection: list, size: int, fill, alignment):
    if alignment == "center":
        remainder = size - len(collection)
        half = remainder // 2
        result = [fill for _ in range(half)]
        result.extend(collection)
        result.extend(fill for _ in range(remainder - half))
        return result
    elif alignment == "end":
        return [*[fill for _ in range(size - len(collection))], *collection]
    return collection

SingleDouble = Literal["single", "double"]
CornerType = Literal["single", "double", "rounded"]
EdgeType = Literal["single", "dashed", "dotted", "double"]
HOverflowType = Literal["wrap", "hidden", "scroll"]
VOverflowType = Literal["hidden", "scroll"]
AlignType = Literal['start', 'center', 'end']
SizeType = int | tuple[int, int] | tuple[int, int, int, int]
