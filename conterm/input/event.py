"""Events

The logic in this module helps to indetify and compare events.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import re
from typing import Literal

from conterm.input.keys import KEY

ANSI = re.compile(
    r"(?P<sequence>\x1b\[(?P<data>(?:\d{1,3};?)*)(?P<event>[ACBDmMZFHPQRS~]{1,2})?)|(\x1b(?![PQRS]))|(?P<key>.{1,3}|[\n\r\t])"
)
# sequence, data, event, key
MOUSE = re.compile(r"(?:\[<(.+)([ACBDFHMZm~]))")
# data, event


@dataclass
class Modifiers:
    Ctrl = 0x0001
    Alt = 0x0002
    Shift = 0x0002


class Mouse:
    def __init__(
        self,
        code: str = "",
    ):
        self.modifiers = 0
        self.type: Mouse.Event = Mouse.Event.Empty
        self.button: Mouse.Button = Mouse.Button.Empty
        self.code = code
        self.pos = (-1, -1)

        if (match := MOUSE.match(code)) is not None:
            data, event = match.groups()
            data = data.split(";")
            if (button := int(data[0])) in [0, 1, 2]: 
                match event:
                    case "M":
                        self.type = Mouse.Event.Click
                    case "m":
                        self.type = Mouse.Event.Release
                self.button = Mouse.Button(button)
            elif (dir := int(data[0])) in [65, 64]:
                self.type = Mouse.Event(dir)
            elif (t := int(data[0])) in  [35, 32]:
                self.type = Mouse.Event(t)
                if len(data[1:]) < 2:
                    raise ValueError(f"Invalid mouse move sequence: {code}")
                self.pos = (int(data[1]), int(data[2]))
            else:
                raise ValueError(f"Invalid mouse sequence: {code!r}")
                

    class Event(Enum):
        Empty = -1
        Click = 0
        Release = 1
        Move = 35
        Drag = 32
        ScrollUp = 64
        ScrollDown = 65

    class Button(Enum):
        Empty = -1
        Left = 0
        Middle = 1
        Right = 2

    def __pretty__(self):
        symbol = self.type.name
        if self.type in [Mouse.Event.Click, Mouse.Event.Release]:
            symbol = self.button.name

        match self.type:
            case Mouse.Event.Click:
                symbol = f"\x1b[32m{symbol}\x1b[39m"
            case Mouse.Event.Release:
                symbol = f"\x1b[31m{symbol}\x1b[39m"

        position = f" {self.pos}" if self.pos[0] > 0 else ""
        return f"{symbol}{position}"

    def __repr__(self):
        return f"<Mouse: {self.code!r}>"



class Key:
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
        sequence, esc, data, event, key = parts[-1]
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

    def __pretty__(self):
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

    def __init__(self, code: str):
        self.type: Literal["KEY", "MOUSE"] = "KEY"
        self.event = None

        if code.startswith("\x1b[<"):
            self.type = "MOUSE"
            self.event = Mouse(code)
        else:
            self.event = Key(code)

    def __eq__(self, other) -> bool:
        if isinstance(other, Record):
            return other.type == self.type
        elif isinstance(other, str):
            return other == self.type

    def __repr__(self) -> str:
        event = self.event.__pretty__() if self.event is not None else ""
        return f"<{self.type}: {event}>"

def pprint(event: Key | Mouse):
    print(event.__pretty__())
