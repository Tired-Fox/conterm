"""Events

The logic in this module helps to indetify and compare events.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import re
from typing import Literal, Protocol, runtime_checkable

from conterm.input.keys import KEY

ANSI = re.compile(
    r"(?P<sequence>\x1b\[(?P<data>(?:\d{1,3};?)*)(?P<event>[ACBDmMZFHPQRS~]{1,2})?)|(\x1b(?!O))|(?P<key>.{1,3}|[\n\r\t])"
)
# sequence, data, event, key
MOUSE = re.compile(r"\[<(.+)([ACBDFHMZmM~])")
# data, event


@dataclass
class Modifiers:
    Ctrl = 0x0001
    Alt = 0x0002
    Shift = 0x0002


class Mouse:
    """A Mouse Event. All information relating to an event of a mouse input."""

    __slots__ = ("modifiers", "events", "button", "code", "pos")

    def __init__(
        self,
        code: str = "",
    ):
        self.modifiers = 0
        self.events: dict[str, Mouse.Event] = {}
        self.button: Mouse.Button = Mouse.Button.EMPTY
        self.code = code
        self.pos = (-1, -1)

        events = filter(lambda x: x != "", code.split("\x1b"))
        for event in events:
            if (match := MOUSE.match(event)) is not None:
                data, event = match.groups()

                data = data.split(";")
                if (button := int(data[0])) in [0, 1, 2]:
                    match event:
                        case "M":
                            self.events[Mouse.Event.CLICK.name] = Mouse.Event.CLICK
                        case "m":
                            self.events[Mouse.Event.RELEASE.name] = Mouse.Event.RELEASE
                    self.button = Mouse.Button(button)
                elif (scroll := int(data[0])) in [65, 64]:
                    event = Mouse.Event(scroll)
                    self.events[event.name] = event
                elif (move := int(data[0])) == 35:
                    event = Mouse.Event(move)
                    self.events[event.name] = event
                    if len(data[1:]) < 2:
                        raise ValueError(f"Invalid mouse move sequence: {code}")
                    self.pos = (int(data[1]), int(data[2]))
                elif (drag := int(data[0])) in [32, 33, 34]:
                    event = Mouse.Event(drag)
                    self.events.update(
                        {Mouse.Event.DRAG.name: Mouse.Event.DRAG, event.name: event}
                    )
                    if len(data[1:]) < 2:
                        raise ValueError(f"Invalid mouse move sequence: {code}")
                    self.pos = (int(data[1]), int(data[2]))
                else:
                    raise ValueError(f"Invalid mouse sequence: {code!r}")

    def __contains__(self, key: Mouse.Event) -> bool:
        if isinstance(key, Mouse.Event):
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

    class Event(Enum):
        """Mouse event types."""

        CLICK = 0
        RELEASE = 1
        DRAG = 2
        MOVE = 35
        DRAG_RIGHT_CLICK = 34
        DRAG_LEFT_CLICK = 32
        DRAG_MIDDLE_CLICK = 33
        SCROLL_UP = 64
        SCROLL_DOWN = 65

    class Button(Enum):
        """Mouse buttons."""

        EMPTY = -1
        LEFT = 0
        MIDDLE = 1
        RIGHT = 2

    def event_of(self, *events: Mouse.Event) -> bool:
        """Check if the mouse event is one of the given mouse events."""
        return any(event.name in self.events for event in events)

    def __event_to_str__(self, event: Mouse.Event) -> str:
        symbol = event.name
        # __contains__ treats a list of events as running any
        if self.event_of(Mouse.Event.CLICK, Mouse.Event.RELEASE):
            symbol = self.button.name

        match self.events:
            case {"CLICK": _}:
                symbol = f"\x1b[32m{symbol}\x1b[39m"
            case {"RELEASE": _}:
                symbol = f"\x1b[31m{symbol}\x1b[39m"

        return symbol

    def __eprint__(self):
        events = f"[{', '.join([self.__event_to_str__(e) for e in self.events.values()])}]"
        position = f" {self.pos}" if self.pos[0] > 0 else ""
        return f"{events}{position}"

    def __repr__(self):
        return f"<Mouse: {self.code!r}>"


class Key:
    "A Key Event. All information relating to an event of a keyboard input."
    __slots__ = ("modifiers", "key", "code")

    def __init__(
        self,
        code: str = "",
    ):
        self.modifiers = 0
        self.key = ""
        self.code = code

        parts = ANSI.findall(code)
        if len(parts) == 2:
            self.modifiers |= Modifiers.Alt

        # sequence, data, event, key
        sequence, data, _, esc, key = parts[-1]
        key = key or esc
        if key != "":
            if (k := KEY.by_code(key)) is not None:
                mods = k.split("_")
                if "CTRL" in mods:
                    self.modifiers |= Modifiers.Ctrl
                if "ALT" in mods:
                    self.modifiers |= Modifiers.Alt
                if "SHIFT" in mods:
                    self.modifiers |= Modifiers.Shift
                self.key = mods[-1].lower()
            else:
                self.key = key
        elif sequence != "" and data != "" and (key := KEY.by_code(sequence)):
            mods = key.split("_")
            if "CTRL" in mods:
                self.modifiers |= Modifiers.Ctrl
            if "ALT" in mods:
                self.modifiers |= Modifiers.Alt
            if "SHIFT" in mods:
                self.modifiers |= Modifiers.Shift
            self.key = mods[-1].lower()
        else:
            self.key = "unkown"
        # mod, ckey, esc, data, event

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, str):
            return KEY.by_chord(__value) == self.code
        elif isinstance(__value, Key):
            return __value.code == self.code
        return False

    def __eprint__(self):
        return f"\x1b[33m{self}\x1b[39m"

    def __str__(self):
        ctrl = "ctrl+" if self.modifiers & Modifiers.Ctrl else ""
        alt = "alt+" if self.modifiers & Modifiers.Alt else ""
        if self.key in KEY:
            return f"{ctrl}{alt}{KEY.by_code(self.key)}"
        return f"{ctrl}{alt}{self.key}"

    def __repr__(self):
        return f"KeyEvent({self.code!r}, key={self.key}, {self.modifiers})"


class Record:
    """Input event based on an ansi code.

    This class serves to help identify what input event was triggered.
    It has rich comparison with string literals of chords along with
    helper methods to help specify/identify the key.
    """

    __slots__ = ("type", "key", "mouse")

    def __init__(self, code: str):
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


def eprint(event: EPrint):
    """Pritty print a input event to stdout."""
    if not isinstance(event, EPrint):
        raise TypeError(f"{event.__class__} does not implement __eprint__")
    print(event.__eprint__())
