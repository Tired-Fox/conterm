from __future__ import annotations
from collections.abc import Callable
from copy import deepcopy
from ctypes import byref
from ctypes.wintypes import DOUBLE, DWORD
from enum import Enum
from functools import cache, cached_property
from math import isinf
import sys
from typing import Literal, overload

from conterm.keys import KeyCode

from .console import GetConsoleMode, SetConsoleMode, stdin, stdout
from .structs import (
    INPUT_RECORD,
    Mod,
    EventType,
    InputRecord,
    KeyEvent,
    MouseEvent,
)
from .signatures import _ReadConsoleInput

import string

ascii = string.ascii_uppercase + string.ascii_lowercase

_ENABLE_WINDOW_INPUT = 0x0008
_ENABLE_MOUSE_INPUT = 0x0010
_ENABLE_EXTENDED_FLAGS = 0x0080
ENABLE_INPUT = _ENABLE_EXTENDED_FLAGS | _ENABLE_WINDOW_INPUT | _ENABLE_MOUSE_INPUT


def _ReadInput() -> list[InputRecord] | None:
    SIZE = 128
    buff = (INPUT_RECORD * SIZE)()
    num_records = DWORD()
    result = _ReadConsoleInput(stdin, buff, SIZE, byref(num_records))

    if result != 0:
        return [InputRecord(record) for record in buff[: num_records.value]]
    else:
        return None


Modifiers = dict[Literal["shift", "ctrl", "alt"], bool]


class Key:
    def __init__(self, event: KeyEvent, modifiers: Modifiers) -> None:
        apply_modifiers(event, modifiers)
        self.press = event.key_down
        self.ctrl = modifiers["ctrl"]
        self.shift = modifiers["shift"]
        self.alt = modifiers["alt"]
        self.char = event.char if event is not None else ""
        self.code = event.key

    @overload
    def pressed(self, key: int) -> bool:
        ...

    @overload
    def pressed(self, key: str) -> bool:
        ...

    def pressed(self, key: int | str) -> bool:
        if isinstance(key, int):
            return self.code == key
        elif isinstance(key, str):
            return self.char == key
        raise TypeError(f"Invalid key for pressed: {key}")

    @cached_property
    def is_ascii(self) -> bool:
        return self.char in ascii

    def __eq__(self, obj):
        return (
            isinstance(obj, Key)
            and self.ctrl == obj.ctrl
            and self.alt == obj.alt
            and obj.shift == self.shift
        )

    def __repr__(self) -> str:
        result = []
        if self.ctrl:
            result.append("ctrl")
        if self.alt:
            result.append("alt")
        if self.char in ascii:
            result.append(self.char.upper() if self.shift else self.char.lower())
        return "+".join(result)


class Mouse:
    def __init__(
        self, modifiers: Modifiers, event: MouseEvent | None = None
    ) -> None:
        if event is not None:
            self.pos = event.pos
            self.buttons = Mouse.Button.from_flags(event.button_state)
            self.modifiers = set(Mod.from_flags(event.modifiers))
            self.events = Mouse.Event.from_flags(event.event_flags)
        else:
            self.pos = (0, 0)
            self.buttons = []
            self.modifiers = set()
            self.event = [] 

        if modifiers["shift"]:
            self.modifiers.add(Mod.Shift)
        if modifiers["alt"]:
            self.modifiers.add(Mod.LeftAlt)
            self.modifiers.add(Mod.RightAlt)
        if modifiers["ctrl"]:
            self.modifiers.add(Mod.LeftCtrl)
            self.modifiers.add(Mod.RightCtrl)

    def has_mods(self, *mods: Mod) -> bool:
        return all(mod in self.modifiers for mod in mods)

    def has_mod(self, mod: Mod) -> bool:
        return mod in self.modifiers

    def is_event(self, event: Mouse.Event) -> bool:
        return event in self.events

    def pressed(self, button: Mouse.Button) -> bool:
        """Check if a mouse button is pressed."""
        return button in self.buttons

    def __eq__(self, obj):
        return isinstance(obj, Mouse) and self.pos == obj.pos

    def __repr__(self) -> str:
        return f"Mouse({self.pos}, buttons={self.buttons}, mod={self.modifiers}, events={[event.name for event in self.events]})"

    class Button(Enum):
        Left = 0x0001
        Middle = 0x0004
        Right = 0x0002
        Empty = 0

        @staticmethod
        def from_flags(flags: int) -> list[Mouse.Button]:
            result = []
            for button in Mouse.Button:
                if flags & button.value:
                    result.append(button)
            return result

    class Event(Enum):
        Click = 0x0010
        Release = 0x0012
        DOUBLE = 0x0002
        HWheeled = 0x0008
        Wheeled = 0x0004
        Moved = 0x0001
        Empty = 0

        @staticmethod
        def from_flags(flags: int) -> list[Mouse.Event]:
            result = []
            for event in Mouse.Event:
                if flags & event.value:
                    result.append(event)
            return result


def apply_modifiers(key: KeyEvent | None, modifiers: Modifiers):
    if key is not None and not key.char in ascii:
        if key.shift():
            modifiers["shift"] = True
        else:
            modifiers["shift"] = False
        if key.ctrl():
            modifiers["ctrl"] = True
        else:
            modifiers["ctrl"] = False
        if key.alt():
            modifiers["alt"] = True
        else:
            modifiers["alt"] = False


class Event:
    def __init__(self, record: InputRecord, modifiers: Modifiers) -> None:
        self.event_type = record.event_type
        self.event = None
        match self.event_type:
            case EventType.Key:
                self.key = Key(record.event.key_event, modifiers)
            case EventType.Mouse:
                self.mouse = Mouse(modifiers, record.event.mouse_event)

    def __repr__(self):
        return repr(self.event)

def ReadInput():
    old_console_mode = GetConsoleMode(stdin)
    if not SetConsoleMode(stdin, ENABLE_INPUT):
        raise Exception("Failed to set console mode")

    while True:
        records = _ReadInput()
        if records:
            for record in records:
                yield Event(record)

    if not SetConsoleMode(stdin, old_console_mode.value):
        raise Exception("Failed to reset console mode")
