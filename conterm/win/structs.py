from ctypes import wintypes
from ctypes.wintypes import *
from ctypes import Structure, Union, POINTER
from enum import Enum, EnumType
from typing import Any

COORD = wintypes._COORD


def klass(name: str) -> str:
    return f"\x1b[33m{name}\x1b[39m"


def attr(name: str) -> str:
    return f"\x1b[38;5;244m{name}\x1b[39m"


def ptuple(value: tuple) -> str:
    return f"{OP}{', '.join(pkeyword(v) for v in value)}{CP}"


def pkeyword(value: Any) -> str:
    return f"\x1b[38;5;253m{value}\x1b[39m"


OP = "\x1b[38;5;243m(\x1b[39m"
CP = "\x1b[38;5;243m)\x1b[39m"
OB = "\x1b[38;5;243m[\x1b[39m"
CB = "\x1b[38;5;243m]\x1b[39m"


class Mod(Enum):
    CapsLock = 0x0080
    Enhanced = 0x0100
    LeftAlt = 0x0002
    LeftCtrl = 0x0008
    NumLock = 0x0020
    RightAlt = 0x0001
    RightCtrl = 0x0004
    ScrollLock = 0x0040
    Shift = 0x0010

    @staticmethod
    def ctrl(flag: int) -> bool:
        return (
            Mod.LeftCtrl.value & flag != 0
            or Mod.RightCtrl.value & flag != 0
        )

    @staticmethod
    def alt(flag: int) -> bool:
        return (
            Mod.LeftAlt.value & flag != 0
            or Mod.RightAlt.value & flag != 0
        )

    @staticmethod
    def shift(flag: int) -> bool:
        return Mod.Shift.value & flag != 0

    @staticmethod
    def from_flags(flag: int) -> tuple["Mod", ...]:
        if flag > 0:
            return tuple([ftype for ftype in Mod if ftype.value & flag])
        return tuple()


class UCHAR(Union):
    _fields_ = [("UnicodeChar", WCHAR), ("AsciiChar", CHAR)]


class Char:
    __slots__ = ("unicode", "ascii")

    def __init__(self, char: UCHAR) -> None:
        self.unicode: str = char.UnicodeChar
        self.ascii: bytes = char.AsciiChar

    def __win32_repr__(self, indent: int = 0) -> list[str]:
        return [
            f"{klass('Char')}{OP}{attr('uni')}=\x1b[32m{self.unicode!r}\x1b[39m, {attr('ascii')}=\x1b[32m{self.ascii!r}\x1b[39m{CP}"
        ]

    def __repr__(self) -> str:
        return "\n".join(self.__win32_repr__())


class KEY_EVENT(Structure):
    _fields_ = [
        ("bKeyDown", BOOL),
        ("wRepeateCount", WORD),
        ("wVirtualKeyCode", WORD),
        ("wVirtualScanCode", WORD),
        ("uChar", UCHAR),
        ("dwControlKeyState", DWORD),
    ]


class KeyEvent:
    __slots__ = (
        "key_down",
        "repeate_count",
        "key",
        "scan_code",
        "char",
        "modifiers",
        "literal",
    )

    def __eq__(self, obj) -> bool:
        return isinstance(obj, KeyEvent) and obj.char == self.char

    def __init__(self, event: KEY_EVENT) -> None:
        self.key_down: bool = event.bKeyDown != 0
        self.repeate_count = int(event.wRepeateCount)
        self.key = int(event.wVirtualKeyCode)
        self.scan_code = int(event.wVirtualScanCode)
        self.char = chr(self.key).lower()
        self.literal = Char(event.uChar)
        # TODO: Parse into enum
        self.modifiers = event.dwControlKeyState
        if Mod.Shift.value & self.modifiers:
            self.char = str(self.char).upper()[0]

    def shift(self) -> bool:
        return Mod.shift(self.modifiers)

    def ctrl(self) -> bool:
        return Mod.ctrl(self.modifiers)

    def alt(self) -> bool:
        return Mod.alt(self.modifiers)

    def __win32_repr__(self, indent: int = 0) -> list[str]:
        pressed = "down" if self.key_down else "up"
        offset = " " * indent
        ctrl = "|".join(
            pkeyword(flag.name) for flag in Mod.from_flags(self.modifiers)
        )
        return [
            f"{klass('KeyEvent')}{OP}",
            f"{offset}  \x1b[35m{pressed}\x1b[39m,",
            f"{offset}  {attr('repeat')}={pkeyword(self.repeate_count)},",
            f"{offset}  {attr('key_code')}={pkeyword(self.key)},",
            f"{offset}  {attr('scan_code')}={pkeyword(self.scan_code)},",
            f"{offset}  {attr('char')}={self.char!r},",
            f"{offset}  {attr('control_keys')}={ctrl if ctrl != '' else pkeyword('None')}{CP}",
        ]

    def __repr__(self) -> str:
        return "\n".join(self.__win32_repr__())


class MOUSE_EVENT(Structure):
    _fields_ = [
        ("dwMousePosition", COORD),
        ("dwButtonState", DWORD),
        ("dwControlKeyState", DWORD),
        ("dwEventFlags", DWORD),
    ]


class ButtonState(Enum):
    LeftFirst = 0x0001
    LeftSecond = 0x0004
    LeftThird = 0x0008
    LeftFourth = 0x0010
    Last = 0x0002

    @staticmethod
    def from_flags(flag: int) -> tuple["ButtonState", ...]:
        if flag > 0:
            return tuple([ftype for ftype in ButtonState if ftype.value & flag])
        return tuple()


class MouseEventType(Enum):
    DoubleClick = 0x0002
    HWheel = 0x0008
    Wheeled = 0x0004
    Moved = 0x0001
    Click = 0x0000

    @staticmethod
    def from_flags(flag: int) -> tuple["MouseEventType", ...]:
        if flag > 0:
            return tuple([ftype for ftype in MouseEventType if ftype.value & flag])
        return tuple()


class MouseEvent:
    __slots__ = ("pos", "button_state", "modifiers", "event_flags")

    def __init__(self, event: MOUSE_EVENT):
        self.pos = (event.dwMousePosition.X, event.dwMousePosition.Y)
        self.button_state = event.dwButtonState
        self.modifiers = event.dwControlKeyState
        # TODO: Parse into list of enums
        self.event_flags = event.dwEventFlags

    def __win32_repr__(self, indent: int = 0) -> list[str]:
        offset = " " * indent
        btn = "|".join(
            pkeyword(flag.name) for flag in ButtonState.from_flags(self.button_state)
        )
        ctrl = "|".join(
            pkeyword(flag.name) for flag in Mod.from_flags(self.modifiers)
        )
        return [
            f"{klass('MouseEvent')}{OP}",
            f"{offset}  {attr('pos')}={ptuple(self.pos)},",
            f"{offset}  {attr('btn_state')}={btn if btn != '' else pkeyword('None')},",
            f"{offset}  {attr('control_keys')}={ctrl if ctrl != '' else pkeyword('None')},",
            f"{offset}  {attr('events')}={pkeyword(self.event_flags)}{CP}",
        ]

    def __repr__(self) -> str:
        return "\n".join(self.__win32_repr__())


class FOCUS_EVENT(Structure):
    _fields_ = [("bSetFocus", BOOL)]


class INPUT_EVENT(Union):
    _fields_ = [
        ("KeyEvent", KEY_EVENT),
        ("MouseEvent", MOUSE_EVENT),
        ("WindowBufferSizeEvent", COORD),
        ("MenuEvent", UINT),
        ("FocusEvent", FOCUS_EVENT),
    ]


class InputEvent:
    __slots__ = (
        "key_event",
        "mouse_event",
        "focus_event",
        "window_buffer_size_event",
    )

    def __init__(self, event: INPUT_EVENT) -> None:
        self.key_event: KeyEvent = KeyEvent(event.KeyEvent)
        self.mouse_event: MouseEvent = MouseEvent(event.MouseEvent)
        self.focus_event: bool = event.FocusEvent
        self.window_buffer_size_event: tuple[int, int] = (
            int(event.WindowBufferSizeEvent.X),
            int(event.WindowBufferSizeEvent.Y),
        )

    def __win32_repr__(self, indent: int = 0) -> list[str]:
        offset = " " * indent
        ke = "\n".join(self.key_event.__win32_repr__(indent + 2))
        me = "\n".join(self.mouse_event.__win32_repr__(indent + 2))
        return [
            f"{klass('InputEvent')}{OP}",
            f"{offset}  {attr('key_event')}={ke}",
            f"{offset}  {attr('mouse_event')}={me}",
            f"{offset}  {attr('focus_event')}={pkeyword(self.focus_event)}",
            f"{offset}  {attr('win_buff_size')}={ptuple(self.window_buffer_size_event)}{CP}",
        ]

    def __repr__(self) -> str:
        return "\n".join(self.__win32_repr__())


class INPUT_RECORD(Structure):
    _fields_ = [("EventType", WORD), ("Event", INPUT_EVENT)]


class EventType(Enum):
    Key = 0x0001
    Focus = 0x0010
    Menu = 0x0008
    Mouse = 0x0002
    Resize = 0x0004


class InputRecord:
    __slots__ = ("event_type", "event")

    def __init__(self, record: INPUT_RECORD) -> None:
        self.event_type = EventType(record.EventType)
        self.event = InputEvent(record.Event)

    def __win32_repr__(self, indent: int = 0) -> list[str]:
        lines = self.event.__win32_repr__(indent)
        lines[0] = f"{OB}{self.event_type.name}{CB}{lines[0]}"
        return lines

    def __repr__(self) -> str:
        return "\n".join(self.__win32_repr__())


class CONSOLE_SCREEN_BUFFER_INFO(Structure):
    _fields_ = [
        ("dwSize", COORD),
        ("dwCursorPosition", COORD),
        ("wAttributes", wintypes.WORD),
        ("srWindow", wintypes.SMALL_RECT),
        ("dwMaximumWindowSize", COORD),
    ]
