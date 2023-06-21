import msvcrt
from typing import IO, Any, AnyStr, cast
from enum import Enum
import sys

from ctypes import WinError, byref, LibraryLoader, WinDLL
from ctypes.wintypes import BOOL, DWORD, HANDLE, LPDWORD

windll: Any = None
if sys.platform == "win32":
    windll = LibraryLoader(WinDLL)
else:
    raise ImportError(f"{__name__} can only be imported on Windows systems")

# SIGNATURES

_GetStdHandle = windll.kernel32.GetStdHandle
_GetStdHandle.argtypes = [DWORD]
_GetStdHandle.restype = HANDLE

_GetConsoleMode = windll.kernel32.GetConsoleMode
_GetConsoleMode.argtypes = [HANDLE, LPDWORD]
_GetConsoleMode.restype = BOOL

_SetConsoleMode = windll.kernel32.SetConsoleMode
_SetConsoleMode.argtypes = [HANDLE, DWORD]
_SetConsoleMode.restype = BOOL

# CONSTANTS

# All input events are redirected to stdin as ansii codes
ENABLE_VIRTUAL_TERMINAL_INPUT = 0x0200
# Enable mouse input events
ENABLE_MOUSE_INPUT = 0x0010
# Need to be able to enable mouse events
ENABLE_EXTENDED_FLAGS = 0x0080

# stdin processes events as ansii codes
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
# Needed for virtual terminal ansii code processing
ENABLE_PROCESSED_OUTPUT = 0x0001

# IMPLEMENTATION


class StdDevice(Enum):
    """The available standard devices for windows."""

    IN = -10
    OUT = -11
    ERR = -12


def get_std_handle(handle: StdDevice = StdDevice.OUT) -> HANDLE:
    """Retrieves a handle to the specified standard device (stdin, stdout, stderr)

    Args:
        handle (int): Indentifier for the standard device. Defaults to -11 (stdout).

    Returns:
        wintypes.HANDLE: Handle to the standard device
    """
    return cast(HANDLE, _GetStdHandle(handle.value))


stdout = get_std_handle(StdDevice.OUT)
stdin = get_std_handle(StdDevice.IN)
stderr = get_std_handle(StdDevice.ERR)


def get_console_mode(std: HANDLE) -> DWORD:
    """Get the console mode for the given standard device.

    Args:
        std (HANDLE): The handle to the standard device to get
            the settings from

    Returns:
        False: when setting the mode fails
    """
    mode = DWORD()
    _GetConsoleMode(std, byref(mode))
    return mode


def set_console_mode(std: HANDLE, mode: int) -> bool:
    """Set the console mode for the given standard device.

    Args:
        std (HANDLE): The handle to the standard device.
        mode (int): The mode / setting flags to set to the device.

    Returns:
        False when setting the mode fails.
    """
    return _SetConsoleMode(std, mode) != 0

KEYS = {
    "ESC": "\x1b",
    "ENTER": "\r",
    "CTRL_ENTER": "\n",
    "F1": "\x1bOP",
    "F2": "\x1bOQ",
    "F3": "\x1bOR",
    "F4": "\x1bOS",
    "F5": "\x1b[15~",
    "F6": "\x1b[17~",
    "F7": "\x1b[18~",
    "F8": "\x1b[19~",
    "F9": "\x1b[20~",
    "F10": "\x1b[21~",
    "F11": "\x1b[23~",
    "F12": "\x1b[24~",
}

def read_ready(_: IO[AnyStr]) -> bool:
    """Determines if IO object is reading to read.

    Args:
        file: An IO object of any type.

    Returns:
        A boolean describing whether the object has unread
        content.
    """
    return msvcrt.kbhit()

def _ensure_str(string: AnyStr) -> str:
    """Ensures return value is always a `str` and not `bytes`.

    Args:
        string: Any string or bytes object.

    Returns:
        The string argument, converted to `str`.
    """

    if isinstance(string, bytes):
        return string.decode("utf-8", "ignore")

    return string

def read(_: int) -> str:
    """Reads characters from sys.stdin.

    Args:
        num: How many characters should be read.

    Returns:
        The characters read.
    """

    if not msvcrt.kbhit():  # type: ignore
        return ""

    return _ensure_str(msvcrt.getch()) # type: ignore

def terminal_setup() -> tuple[DWORD, DWORD]:
    """Enable virtual sequence processing for the windows terminal.

    Returns:
        tuple of the stdin and stdout original modes respectively.
    """
    # Get current console settings for stdin and stdout so they can
    # be reset when the input is done being read
    _old_input_ = get_console_mode(stdin)
    _old_output_ = get_console_mode(stdout)

    # Set the appropriate settings for input to be converted to ansii
    # and for mouse events to be captured
    if not set_console_mode(
        stdin,
        ENABLE_EXTENDED_FLAGS | ENABLE_VIRTUAL_TERMINAL_INPUT | ENABLE_MOUSE_INPUT,
    ):
        raise WinError(descr="Failed to set Terminal Input for stdin")

    # Set the appropriate settings for output to capture input events as ansii
    if not set_console_mode(
        stdout, ENABLE_PROCESSED_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING
    ):
        set_console_mode(stdin, _old_input_.value)
        raise WinError(descr="Failed to set Terminal Input for stdin")

    return _old_input_, _old_output_


def terminal_reset(data: tuple[DWORD, DWORD]):
    """Reset the terminal to it's original state given the state of stdin and stdout.

    Args:
        data (tuple[DWORD, DWORD]): Tuple of stdin and stdout original modes respectively.
    """

    # Done reading input so reset console settings
    if not set_console_mode(stdin, data[0].value):
        raise WinError(descr="Failed to set Terminal Input for stdin")

    if not set_console_mode(stdout, data[1].value):
        raise WinError(descr="Failed to set Terminal Input for stdin")
