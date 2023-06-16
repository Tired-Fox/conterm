from ctypes.wintypes import RECT, SMALL_RECT
from typing import Any
from ctypes import LibraryLoader, WinDLL
import sys

windll: Any = None
if sys.platform == "win32":
    windll = LibraryLoader(WinDLL)
else:
    raise ImportError(f"{__name__} can only be imported on Windows systems")

Cols = int
Rows = int

class Rect:
    __slots__ = ("_left", "_right", "_top", "_bottom")
    def __init__(self, rect: SMALL_RECT | RECT) -> None:
        if isinstance(rect, SMALL_RECT):
            self._left = int(rect.Left)
            self._right = int(rect.Right)
            self._top = int(rect.Top)
            self._bottom = int(rect.Bottom)
        elif isinstance(rect, RECT):
            self._left = int(rect.left)
            self._right = int(rect.right)
            self._top = int(rect.top)
            self._bottom = int(rect.bottom)

    @property
    def width(self) -> Cols:
        """Width of the rect. 1 indexed"""
        return self.right - self.left + 1

    @property
    def height(self) -> Rows:
        """Height of the rect. 1 indexed"""
        return self.bottom - self.top + 1

    @property
    def left(self) -> int:
        """Left of value of the rect. 0 indexed"""
        return self._left

    @property
    def right(self) -> int:
        """Right of value of the rect. 0 indexed"""
        return self._right

    @property
    def top(self) -> int:
        """Top of value of the rect. 0 indexed"""
        return self._top

    @property
    def bottom(self) -> int:
        """Bottom of value of the rect. 0 indexed"""
        return self._bottom

    def size(self) -> tuple[Cols, Rows]:
        """Get a tuple of the number of columns and number of rows."""
        return (self.width, self.height)

    def __repr__(self) -> str:
        return f"Rect({self._left}, {self._top}, {self._right}, {self._bottom})"
