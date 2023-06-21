from contextlib import contextmanager
from typing import Generator
import sys

from .event import Record, Mouse, Key, eprint
from .keys import KEY

if sys.platform == "win32":
    from .win import terminal_setup, terminal_reset, read, read_ready
elif sys.platform == "linux":
    from .linux import terminal_setup, terminal_reset, read, read_ready
else:
    raise ImportError(f"Unsupported platform: {sys.platform}")



@contextmanager
def terminal_input():
    """Enable virtual terminal sequence processing for windows."""
    data = terminal_setup()
    try:
        yield
    except Exception as error:
        raise error
    finally:
        terminal_reset(data)


class InputManager:
    """Manager that handles getting characters from stdin."""

    def __init__(self):
        self.data = terminal_setup()

    def _read_buff_(self) -> Generator:
        """Read characters from the buffer until none are left."""
        try:
            yield read(1)

            while read_ready(sys.stdin):
                yield read(1)
        finally:
            pass

    def getch(self, interupt: bool = True) -> str:
        """Get the next character. Blank if no next character.

        Args:
            interupt: Whether to allow for default keyboard interrupts. Defaults to True
        """

        char = "".join(self._read_buff_())
        try:
            if char == chr(3):
                raise KeyboardInterrupt
        except:
            if interupt:
                raise KeyboardInterrupt("Unhandled Interupt")
        return char

    def __del__(self):
        if self.data is not None:
            terminal_reset(self.data)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        if self.data is not None:
            terminal_reset(self.data)
            self.data = None

    def watch(self, interupt: bool = True, surpress: bool = False) -> Generator:
        """Get characters until keyboard interupt. Blocks until next char is available.

        Args:
            interupt: Whether to allow for default keyboard interrupts. Defaults to True
            surpress: Whether to supress input warnings. Defaults to False
        """

        if not surpress and not interupt:
            print(
                "\x1b[1m[\x1b[33mWARN\x1b[39m]\x1b[22m:",
                "Exit/Interupt case is not being handled. Make sure to handle exiting the input loop"
            )

        while True:
            char = self.getch(interupt)
            if char != "":
                yield Record(char)
