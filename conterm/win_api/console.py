from collections.abc import Hashable
from ctypes.wintypes import DWORD
from enum import Enum
from typing import cast

from . import Cols, Rows, Rect
from .structs import CONSOLE_SCREEN_BUFFER_INFO, HANDLE
from .signatures import _GetStdHandle, _GetConsoleScreenBufferInfo, _GetConsoleMode, _SetConsoleMode

from ctypes import byref

__all__ = [
    "ConsoleInfo",
    "GetConsoleInfo",
    "GetConsoleSize",
    "GetCursorPos",
]

class StdDevice(Enum):
    """The available standard devices for windows."""
    IN = -10
    OUT = -11
    ERR = -12

def GetStdHandle(handle: StdDevice = StdDevice.OUT) -> HANDLE:
    """Retrieves a handle to the specified standard device (stdin, stdout, stderr)

    Args:
        handle (int): Indentifier for the standard device. Defaults to -11 (stdout).

    Returns:
        wintypes.HANDLE: Handle to the standard device
    """
    return cast(HANDLE, _GetStdHandle(handle.value))

stdout = GetStdHandle(StdDevice.OUT)
stdin = GetStdHandle(StdDevice.IN)
stderr = GetStdHandle(StdDevice.ERR)

def GetConsoleMode(std: HANDLE) -> DWORD:
    mode = DWORD()
    _GetConsoleMode(std, byref(mode))
    return mode

def SetConsoleMode(std: HANDLE, mode: int) -> bool:
    return _SetConsoleMode(std, mode) != 0

class ConsoleInfo:
    __slots__ = ("size", "cursor", "rect", "max_size")
    def __init__(self, info: CONSOLE_SCREEN_BUFFER_INFO) -> None:
        self.rect = Rect(info.srWindow)
        self.cursor = (info.dwCursorPosition.X, info.dwCursorPosition.Y)

    def __repr__(self) -> str:
        return f"""ConsoleInfo(rect={self.rect!r}, cursor={self.cursor})"""

def GetConsoleInfo(std: HANDLE) -> ConsoleInfo:
    """Retrieves information about the console.

    Returns:
        ConsoleInfo: A struct containint information about
            console size and cursor position"""
    console_screen_buffer_info = CONSOLE_SCREEN_BUFFER_INFO()

    _GetConsoleScreenBufferInfo(std, byref(console_screen_buffer_info))
    return ConsoleInfo(console_screen_buffer_info)

def GetConsoleSize(std: HANDLE) -> tuple[Cols, Rows]:
    """Get the console size in cols and rows."""
    return GetConsoleInfo(std).rect.size()

def GetCursorPos(std: HANDLE) -> tuple[int, int]:
    """Get the cursors position in the console. Not Mouse Position.

    Returns:
        tuple[int, int]: The (x, y) coordinate of the cursor.
    """
    return GetConsoleInfo(std).cursor

