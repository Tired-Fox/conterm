from collections.abc import Callable
from ctypes import byref
from ctypes.wintypes import DWORD
from functools import cache, cached_property
import sys
from typing import Literal

from .console import GetConsoleMode, SetConsoleMode, stdin, stdout
from .structs import INPUT_RECORD, ControlKeyState, EventType, InputRecord, KeyEvent, MouseEvent
from .signatures import _ReadConsoleInput

import string

ascii = string.ascii_uppercase + string.ascii_lowercase


class Input:
    pass


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
        self.ctrl = modifiers["ctrl"]
        self.shift = modifiers["shift"] 
        self.alt = modifiers["alt"] 
        self.char = event.char

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
    def __init__(self, event: MouseEvent, modifiers: Modifiers) -> None:
        self.pos = event.pos

    def __eq__(self, obj):
        return (
            isinstance(obj, Mouse)
            and self.pos == obj.pos
        )

    def __repr__(self) -> str:
        return ""


def apply_modifiers(key: KeyEvent, modifiers: Modifiers):
    if not key.char in ascii:
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
                self.event = Key(record.event.key_event, modifiers)
            case EventType.Mouse:
                self.event = Mouse(record.event.mouse_event, modifiers)

        

def ReadInput():
    old_console_mode = GetConsoleMode(stdin)
    if not SetConsoleMode(stdin, ENABLE_INPUT):
        raise Exception("Failed to set console mode") 

    while True:
        records = _ReadInput()
        if records:
            for record in records:
                yield record

    if not SetConsoleMode(stdin, old_console_mode.value):
        raise Exception("Failed to reset console mode")

