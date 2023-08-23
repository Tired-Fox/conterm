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

import re
import sys
from collections.abc import Callable
from contextlib import contextmanager
from threading import Thread
import threading
from typing import Generator

from .event import Button, Event, Key, Mouse, Record, eprint
from .keys import keys

if sys.platform == "win32":
    from .win import read, read_ready, terminal_reset, terminal_setup
elif sys.platform in ["linux", "darwin"]:
    from .unix import read, read_ready, terminal_reset, terminal_setup
else:
    raise ImportError(f"Unsupported platform: {sys.platform}")

__all__ = [
    "Key",
    "Mouse",
    "Event",
    "Button",
    "eprint",
    "keys",
    "Listener",
    "InputManager",
    "terminal_input",
    "supports_ansi",
]

ARROW = re.compile(r"\x1b\[(?:\d;\d)?[ABCD]")


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

    def __exit__(self, etype, evalue, etb):
        if self.data is not None:
            terminal_reset(self.data)
            self.data = None

    @staticmethod
    def watch(interupt: bool = True, surpress: bool = False) -> Generator[Record, None, None]:
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
                try:
                    char = input.getch(interupt)
                    if char != "":
                        arrows = list(ARROW.finditer(char))
                        if len(arrows) > 1:
                            start = arrows[0].start()
                            start = char[:start]
                            for arrow in arrows:
                                yield Record(start + arrow.group(0))
                        else:
                            yield Record(char)
                except KeyboardInterrupt as error:
                    raise error
                except Exception:
                    continue

def _void_(*_):
    pass


class Listener(Thread):
    """Input event listener"""

    def __init__(
        self,
        on_key: Callable[[Key, dict], bool | None] = _void_,
        on_mouse: Callable[[Mouse, dict], bool | None] = _void_,
        on_event: Callable[[Record, dict], bool | None] = _void_,
        on_interrupt: Callable = _void_,
        interupt: bool = True,
        *,
        state: dict | None = None,
        surpress: bool = False,
    ):
        self._on_key_ = on_key
        self._on_mouse_ = on_mouse
        self._on_event_ = on_event
        self._on_interrupt_ = on_interrupt

        self._interupt_ = interupt
        self._surpress_ = surpress
        self._state_ = state or {}
        self._stop_ = threading.Event()
        self.exc = None
        # If the program exits in a odd manner then the thread will
        # also exit
        super().__init__(name="python_input_listner", daemon=True)

    def __enter__(self) -> Listener:
        self.start()
        return self

    def __exit__(self, _etype, evalue, _etb):
        if evalue is not None:
            raise evalue

    def run(self):
        try:
            for record in InputManager.watch(self._interupt_, self._surpress_):
                if self._stop_.is_set():
                    raise KeyboardInterrupt

                result = self._on_event_(record, self._state_)
                if result is False:
                    return

                if record == "KEY":
                    result = self._on_key_(record.key, self._state_)
                    if result is False:
                        return

                elif record == "MOUSE":
                    result = self._on_mouse_(record.mouse, self._state_)
                    if result is False:
                        return
        except KeyboardInterrupt as error:
            self._on_interrupt_()
            self.exc = error

    def stop(self):
        self._stop_.set()

    def join(self):
        """Force exceptions to be thrown in main thread"""
        Thread.join(self)
        # If exception occurs raise it again here. This will raise
        # the exception in the caller thread.
        if self.exc is not None:
            raise self.exc


def supports_ansi() -> bool:
    """Check if the current terminal supports ansi sequences."""

    sys.stdout.write("\x1b[6n")
    sys.stdout.flush()

    # Collect input which could be blank meaning no ansi input
    char = ""
    try:
        char += read(1)
        while read_ready(sys.stdin):
            char += read(1)
    finally:
        pass

    return char != "" and char.startswith("\x1b[") and char.endswith("R")

