"""Terminal unix specific ansi input logic."""
from codecs import getincrementaldecoder
import os
from select import select
from typing import IO, AnyStr
import sys
import termios
import tty

if sys.stdin.encoding is not None:
    decode = getincrementaldecoder(sys.stdin.encoding)().decode
else:
    decode = lambda item: item

KEYS = {
    # "F1": "\x1b[11~",
    # "F2": "\x1b[12~",
    # "F3": "\x1b[13~",
    # "F4": "\x1b[14~",
    # "F5": "\x1b[15~",
    # "F6": "\x1b[17~",
    # "F7": "\x1b[18~",
    # "F8": "\x1b[19~",
    # "F9": "\x1b[20~",
    # "F10": "\x1b[21~",
    # "F11": "\x1b[23~",
    # "F12": "\x1b[24~",
}

def read_ready(file: IO[AnyStr]) -> bool:
    """Determines if IO object is reading to read.

    Args:
        file: An IO object of any type.

    Returns:
        A boolean describing whether the object has unread
        content.
    """

    result = select([file], [], [], 0.0)
    return len(result[0]) > 0


def read(num: int) -> str:
    """Reads characters from sys.stdin.

    Args:
        num: How many characters should be read.

    Returns:
        The characters read.
    """

    buff = ""
    while len(buff) < num:
        char = os.read(sys.stdin.fileno(), 1)

        try:
            buff += decode(char)
        except UnicodeDecodeError:
            buff += str(char)

    return buff

def terminal_setup() -> tuple[int, list]:
    """Enable terminal cbreak mode.

    Returns:
        tuple of the stdin descriptor and list of original flags for stdin respectively.
    """
    descriptor = sys.stdin.fileno()
    old_settings = termios.tcgetattr(descriptor)
    tty.setcbreak(descriptor)
    return descriptor, old_settings

def terminal_reset(data: tuple[int, list]):
    """Reset the terminal to it's original state given the state of stdin and stdout.

    Args:
        data (tuple[int, list]): Tuple of stdin descriptor and original flags respectively.
    """
    termios.tcsetattr(data[0], termios.TCSADRAIN, data[1])
