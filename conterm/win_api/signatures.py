from ctypes import POINTER
from ctypes.wintypes import BOOL, DWORD, HANDLE, LPDWORD

from . import windll
from .structs import INPUT_RECORD, CONSOLE_SCREEN_BUFFER_INFO

_GetStdHandle = windll.kernel32.GetStdHandle
_GetStdHandle.argtypes = [DWORD]
_GetStdHandle.restype = HANDLE

_GetConsoleScreenBufferInfo = windll.kernel32.GetConsoleScreenBufferInfo
_GetConsoleScreenBufferInfo.argtypes = [
    HANDLE,
    POINTER(CONSOLE_SCREEN_BUFFER_INFO),
]
_GetConsoleScreenBufferInfo.restype = BOOL

_GetConsoleMode = windll.kernel32.GetConsoleMode
_GetConsoleMode.argtypes = [HANDLE, LPDWORD]
_GetConsoleMode.restype = BOOL

_SetConsoleMode = windll.kernel32.SetConsoleMode
_SetConsoleMode.argtypes = [HANDLE, DWORD]
_SetConsoleMode.restype = BOOL

_ReadConsoleInput = windll.kernel32.ReadConsoleInputW
_ReadConsoleInput.argtypes = [HANDLE, POINTER(INPUT_RECORD), DWORD, LPDWORD]
_ReadConsoleInput.restype = BOOL
