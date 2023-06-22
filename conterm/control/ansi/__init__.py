"""Terminal ansi input module

This module focuses around setting up the terminal for full ansi input.
it also focuses around ease of use and comparison between key, or mouse, events and
handling them.

Supported Platforms:
    - Windows (win32)
    - Linux   (linux)
    - MacOS   (darwin)
"""

from __future__ import annotations
from collections.abc import Callable
from contextlib import contextmanager
from typing import Generator
from threading import Thread
import sys

from .event import Record, Mouse, Key, eprint, Event, Button
from .keys import keys

if sys.platform == "win32":
    from .win import terminal_setup, terminal_reset, read, read_ready
elif sys.platform in ["linux", "darwin"]:
    from .unix import terminal_setup, terminal_reset, read, read_ready
else:
    raise ImportError(f"Unsupported platform: {sys.platform}")

__all__= [
    "Key",
    "Mouse",
    "Event",
    "Button",
    "eprint",
    "keys",
    "Listener",
    "InputManager",
    "terminal_input",
]

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
                raise KeyboardInterrupt("Unhandled Interupt")
        except KeyboardInterrupt as error:
            if interupt:
                raise error
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

    @staticmethod
    def watch(interupt: bool = True, surpress: bool = False) -> Generator:
        """Get characters until keyboard interupt. Blocks until next char is available.

        Args:
            interupt: Whether to allow for default keyboard interrupts. Defaults to True
            surpress: Whether to supress input warnings. Defaults to False
        """

        if not surpress and not interupt:
            print(
                "\x1b[1m[\x1b[33mWARN\x1b[39m]\x1b[22m:",
                "Exit/Interupt case is not being handled. Make sure to handle exiting the input loop",
            )

        with InputManager() as input:
            while True:
                char = input.getch(interupt)
                if char != "":
                    yield Record(char)


def _void_(*_):
    pass


class Listener(Thread):
    """Input event listener"""

    def __init__(
        self,
        on_key: Callable[[Key],bool|None] =_void_,
        on_mouse: Callable[[Mouse],bool|None]=_void_,
        interupt: bool = True,
        *,
        surpress: bool = False,
    ):
        self._on_key_ = on_key
        self._on_mouse_ = on_mouse
        self._interupt_ = interupt
        self._surpress_ = surpress
        # If the program exits in a odd manner then the thread will
        # also exit
        super().__init__(name="python_input_listner", daemon=True)

    def __enter__(self) -> Listener:
        self.start()
        return self

    def __exit__(self, *_):
        pass

    def run(self):
        for record in InputManager.watch(self._interupt_, self._surpress_):
            if record == "KEY":
                result = self._on_key_(record.key)
                if result is False:
                    return
            elif record == "MOUSE":
                result = self._on_mouse_(record.mouse)
                if result is False:
                    return
