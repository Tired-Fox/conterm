import msvcrt
from typing import Any, AnyStr

# These are wrappers around Win32 API methods that I wrote.
from conterm.win import enable_virtual_processing

# These methods are directly copied from `pytermgui` getch logic
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

def get_chars() -> str:
    """Reads characters from sys.stdin.

    Returns:
        All read characters.
    """
    if not msvcrt.kbhit():
        return ""

    char = msvcrt.getch()  # type: ignore
    if char == b"\xe0":
        char = "\x1b"

    buff = _ensure_str(char)  # type: ignore

    while msvcrt.kbhit():
        char = msvcrt.getch()  # type: ignore
        buff += _ensure_str(char)

    return buff

def getch() -> Any:
    key = get_chars()
    if key == chr(3):
        raise KeyboardInterrupt
    return key

if __name__ == "__main__":
    with enable_virtual_processing():
        # While no interupt, read key and mouse events
        while True:
            if (key := getch()) != "":
                print(repr(key))

