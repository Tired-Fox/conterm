"""Events

The logic in this module helps to indetify and compare events.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from functools import cache
from typing import Any, Literal, Protocol, runtime_checkable

from .keys import keys


@cache
def _build_chord_(modifiers: int, key: str) -> str:
    """Builds string chord from key event data. Caches results
    for prolonged keyboard event captures.
    """
    ctrl = "ctrl+" if modifiers & Modifiers.Ctrl else ""
    alt = "alt+" if modifiers & Modifiers.Alt else ""
    shift = "shift+" if modifiers & Modifiers.Shift and len(key) > 1 else ""
    if key in keys:
        return f"{ctrl}{alt}{shift}{keys.by_code(key)}"
    return f"{ctrl}{alt}{shift}{key if key.isascii() else 'unkown'}"


__ANSI__ = re.compile(
    r"(?P<sequence>\x1b\[(?P<data>(?:\d{1,3};?)*)(?P<event>[ACBDmMZFHPQRS~]{1,2})?)t?|(\x1b(?!O))|(?P<key>.{1,3}|[\n\r\t])"
)
"""Regex for key event sequences.

Produces (in order):
    - sequence
    - data
    - event
    - key
"""

__MOUSE__ = re.compile(r"\[<(.+)([ACBDFHMZmM~])")
"""Regex for mouse event sequences.

Produces (in order):
    - data
    - event
"""


@dataclass
class Modifiers:
    """Custom modifier flags for key events."""

    Ctrl = 0x0001
    Alt = 0x0002
    Shift = 0x0004


class Event(Enum):
    """Mouse event types."""

    CLICK = 0
    """Button click."""
    RELEASE = 1
    """Button release."""
    DRAG = 2
    """Click and drag."""
    MOVE = 35
    """Move mouse."""
    DRAG_RIGHT_CLICK = 34
    """Right click and drag."""
    DRAG_LEFT_CLICK = 32
    """Left click and drag."""
    DRAG_MIDDLE_CLICK = 33
    """Middle click and drag."""
    SCROLL_UP = 64
    """Scroll wheel up."""
    SCROLL_DOWN = 65
    """Scroll wheel down."""


class Button(Enum):
    """Mouse buttons."""

    EMPTY = -1
    """Not button pressed."""
    LEFT = 0
    """Left button pressed."""
    MIDDLE = 1
    """Middle button pressed."""
    RIGHT = 2
    """Right button pressed."""


class Mouse:
    """A Event. All information relating to an event of a mouse input."""

    __slots__ = ("modifiers", "events", "button", "code", "pos")

    def __init__(
        self,
        code: str = "",
    ) -> None:
        self.modifiers = 0
        # Can have multiple events. Ex: While dragging a user can click a different
        # mouse button. This results in a click event and a drag event.
        self.events: dict[str, Event] = {}
        self.button: Button = Button.EMPTY
        self.code = code
        self.pos = (-1, -1)

        events = filter(lambda x: x != "", code.split("\x1b"))
        # Iterate through the different mouse sequences
        for event in events:
            if (match := __MOUSE__.match(event)) is not None:
                # Parse the data and button event from the sequence
                data, event = match.groups()

                # Split data into tuple. First value is the type of mouse event
                # then the other values are information for that event.
                data = data.split(";")
                if (button := int(data[0])) in [0, 1, 2]:
                    if event == "M":
                        self.events[Event.CLICK.name] = Event.CLICK
                    elif event == "m":
                        self.events[Event.RELEASE.name] = Event.RELEASE
                    self.button = Button(button)
                elif (scroll := int(data[0])) in [65, 64]:
                    event = Event(scroll)
                    self.events[event.name] = event
                elif (move := int(data[0])) == 35:
                    event = Event(move)
                    self.events[event.name] = event
                    if len(data[1:]) < 2:
                        raise ValueError(f"Invalid mouse move sequence: {code}")
                    self.pos = (int(data[1]), int(data[2]))
                elif (drag := int(data[0])) in [32, 33, 34]:
                    event = Event(drag)
                    self.events.update({Event.DRAG.name: Event.DRAG, event.name: event})
                    if len(data[1:]) < 2:
                        raise ValueError(f"Invalid mouse move sequence: {code}")
                    self.pos = (int(data[1]), int(data[2]))

    def event_of(self, *events: Event) -> bool:
        """Check if the mouse event is one of the given mouse events."""
        return any(event.name in self.events for event in events)

    def __contains__(self, key: Event) -> bool:
        """Check if an event is in the list of mouse events."""
        if isinstance(key, Event):
            return key.name in self.events
        return False

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Mouse):
            return (
                __value.events == self.events
                and __value.pos == self.pos
                and __value.button == self.button
            )
        return False

    def __event_to_str__(self, event: Event) -> str:
        symbol = event.name
        # __contains__ treats a list of events as running any
        if self.event_of(Event.CLICK, Event.RELEASE):
            symbol = self.button.name

        if Event.CLICK in self.events:
            symbol = f"\x1b[32m{symbol}\x1b[39m"
        elif Event.RELEASE in self.events:
            symbol = f"\x1b[31m{symbol}\x1b[39m"

        return symbol

    def __eprint__(self) -> str:
        events = (
            f"{{{', '.join([self.__event_to_str__(e) for e in self.events.values()])}}}"
        )
        position = f" {self.pos}" if self.pos[0] > 0 else ""
        return f"{events}{position}"

    def __repr__(self) -> str:
        return f"<Mouse: {self.code!r}>"


class Key:
    "A Key Event. All information relating to an event of a keyboard input."
    __slots__ = ("modifiers", "key", "code")

    def __init__(
        self,
        code: str = "",
    ) -> None:
        self.modifiers = 0
        self.key = ""
        self.code = code

        parts = __ANSI__.findall(code)
        if len(parts) == 2:
            self.modifiers |= Modifiers.Alt

        # sequence, data, event, key
        sequence, data, _, esc, key = parts[-1]
        key = key or esc
        if key != "" or sequence != "":
            k = (k := keys.by_code(key)) or (k := keys.by_code(sequence))
            if k is not None:
                mods = k.split("_")
                if "CTRL" in mods:
                    self.modifiers |= Modifiers.Ctrl
                if "ALT" in mods:
                    self.modifiers |= Modifiers.Alt
                if "SHIFT" in mods:
                    self.modifiers |= Modifiers.Shift
                self.key = mods[-1].lower()
            else:
                self.key = key or sequence
        elif sequence != "" and data != "" and (key := keys.by_code(sequence)):
            mods = key.split("_")
            if "CTRL" in mods:
                self.modifiers |= Modifiers.Ctrl
            if "ALT" in mods:
                self.modifiers |= Modifiers.Alt
            if "SHIFT" in mods:
                self.modifiers |= Modifiers.Shift
            self.key = mods[-1].lower()
        else:
            self.key = f"{code!r}"
        # mod, ckey, esc, data, event

    def is_ascii(self) -> bool:
        return len(self.key) == 1 and self.key.isascii()

    def ctrl(self) -> bool:
        """Check if the key has a control modifier applied."""
        return self.modifiers & Modifiers.Ctrl != 0

    def alt(self) -> bool:
        """Check if the key has a alt modifier applied."""
        return self.modifiers & Modifiers.Alt != 0

    def shift(self) -> bool:
        """Check if the key has a shift modifier applied."""
        return self.modifiers & Modifiers.Shift != 0 or self.key.isupper()

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, str):
            return keys.by_chord(__value) == self.code
        if isinstance(__value, Key):
            return __value.code == self.code
        return False

    def __eprint__(self) -> str:
        return f"\x1b[33m{self}\x1b[39m"

    def __str__(self) -> str:
        return _build_chord_(self.modifiers, self.key)

    def __repr__(self) -> str:
        return f"KeyEvent({self.code!r}, key={self.key}, {self.modifiers})"


class Record:
    """Input event based on an ansi code.

    This class serves to help identify what input event was triggered.
    It has rich comparison with string literals of chords along with
    helper methods to help specify/identify the key.
    """

    __slots__ = ("type", "key", "mouse")

    def __init__(self, code: str) -> None:
        self.type: Literal["KEY", "MOUSE"] = "KEY"
        self.key = None
        self.mouse = None

        if code.startswith("\x1b[<"):
            self.type = "MOUSE"
            self.mouse = Mouse(code)
        else:
            self.key = Key(code)

    def __eq__(self, other) -> bool:
        if isinstance(other, Record):
            return other.type == self.type
        if isinstance(other, str):
            return other == self.type
        return False

    def __repr__(self) -> str:
        event = (self.key or self.mouse).__eprint__()
        return f"<{self.type}: {event}>"


@runtime_checkable
class EPrint(Protocol):
    """Rules for being able to be a printable event."""

    def __eprint__(self) -> str:
        ...


def eprint(event: EPrint) -> None:
    """Pretty print an input event to stdout."""
    if not isinstance(event, EPrint):
        raise TypeError(f"{event.__class__} does not implement __eprint__")
    print(event.__eprint__())
