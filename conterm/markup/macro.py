from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from re import sub
from typing import Any

from conterm.control.ansi.event import Modifiers
from .color import Color
from .hyperlink import Hyperlink


class Reset:
    """Extra state class for macros."""

    def __repr__(self) -> str:
        return "RESET"


def _cod(condition, one, default: Any = ""):
    return one if condition else default


MOD_CODE_MAP = {
    "Bold": "1",
    "Dim": "2",
    "Italic": "3",
    "Underline": "4",
    "SBlink": "5",
    "RBlink": "6",
    "Reverse": "7",
    "Strike": "9",
    "U_Bold": "21",
    "U_Dim": "22",
    "U_Italic": "23",
    "U_Underline": "24",
    "U_SBlink": "25",
    "U_RBlink": "25",
    "U_Reverse": "27",
    "U_Strike": "29",
}

MOD_SYMBOL_MAP = {
    "b": "Bold",
    "d": "Dim",
    "i": "Italic",
    "u": "Underline",
    "sb": "SBlink",
    "rb": "RBlink",
    "r": "Reverse",
    "s": "Strike",
    "/b": "U_Bold",
    "/d": "U_Dim",
    "/i": "U_Italic",
    "/u": "U_Underline",
    "/rb": "U_RBlink",
    "/sb": "U_SBlink",
    "/r": "U_Reverse",
    "/s": "U_Strike",
}

def map_modifers(op: int, cl: int) -> list[str]:
    result = []

    for mod in ModifierOpen:
        if mod.value & op and mod.value & cl == 0:
            result.append(MOD_CODE_MAP[mod.name])
    for mod in ModifierClose:
        if mod.value & cl and mod.value & op == 0:
            result.append(MOD_CODE_MAP[mod.name])
    return result

def map_modifer_names(op: int, cl: int) -> list[str]:
    result = []

    for mod in ModifierOpen:
        if mod.value & op and mod.value & cl == 0:
            result.append(mod.name)
    for mod in ModifierClose:
        if mod.value & cl and mod.value & op == 0:
            result.append(mod.name.replace("U_", "/"))
    return result


class ModifierOpen(Enum):
    """Data class of modifier flags for integer packing."""
    Bold = 1
    Dim = 2
    Italic = 4
    Underline = 8
    SBlink = 16
    RBlink = 32
    Reverse = 64
    Strike = 128

class ModifierClose(Enum):
    U_Bold = 1
    U_Dim = 2
    U_Italic = 4
    U_Underline = 8
    U_SBlink = 16
    U_RBlink = 32
    U_Reverse = 64
    U_Strike = 128

RESET = Reset()
CustomMacros = dict[str, Callable[[str], str]]

def diff_url(current, other):
    if (current == RESET and isinstance(other, str)) or (
        isinstance(current, str) and not isinstance(other, str)
    ):
        return current
    if isinstance(current, str) and isinstance(other, str):
        return f"{Hyperlink.close}{current}"
    return None


def diff_color(new, old):
    # None, Reset, Set
    if isinstance(new, str) and len(new) > 0:
        return new
    if new == RESET and isinstance(old, str):
        return RESET
    return None

class Macro:
    """Representation of all data for a given macro."""

    __slots__ = (
        "macro",
        "customs",
        "url",
        "fg",
        "bg",
        "stash",
        "pop",
        "mod_open",
        "mod_close",
    )

    def __init__(self, macro: str = ""):
        self.macro = sub(" +", " ", macro)

        self.customs = []
        self.stash = False
        self.pop = None
        self.mod_open = 0
        self.mod_close = 0
        self.url = None
        self.fg = None
        self.bg = None

        macros = self.macro.lstrip("[").rstrip("]").split(" ")

        for macro in macros:
            self.__parse_macro__(macro)

    def __full_reset_macro__(self):
        self.url = RESET
        self.fg = RESET
        self.bg = RESET
        self.mod_open = 0
        self.mod_close = 239

    def __parse_close_macro__(self, macro):
        if macro == "/pop":
            self.pop = True
        elif macro == "/fg":
            self.fg = RESET
        elif macro == "/bg":
            self.bg = RESET 
        elif macro == "/~":
            self.url = RESET

    def __parse_open_macro__(self, macro):
        if macro.startswith("~"):
            macro = macro[1:]
            if len(macro) == 0:
                raise ValueError("Expected url assignment")
            self.url = Hyperlink.open(macro)
        elif macro.startswith("@"):
            self.bg = Color(macro[1:]).bg()
        else:
            try:
                self.fg = Color(macro).fg()
            except ValueError:
                if macro.strip() != "":
                    self.customs.append(macro)

    def __parse_macro__(self, macro):
        if macro in MOD_SYMBOL_MAP:
            macro = MOD_SYMBOL_MAP[macro]
            if macro in ModifierClose.__members__:
                self.mod_close |= ModifierClose[macro].value
            elif macro in ModifierOpen.__members__:
                self.mod_open|= ModifierOpen[macro].value
        elif macro.startswith("/"):
            if len(macro) == 1:
                self.__full_reset_macro__()
            else:
                self.__parse_close_macro__(macro)
        else:
            self.__parse_open_macro__(macro)

    def __add__(self, other: Macro) -> Macro:
        macro = Macro()
        macro.customs = set([*self.customs, *other.customs])
        macro.url = other.url if other.url is not None else self.url
        macro.fg = other.fg if other.fg is not None else self.fg
        macro.bg = other.bg if other.bg is not None else self.bg
        macro.mod_open = other.mod_open | self.mod_open
        macro.mod_close = other.mod_close | self.mod_close
        return macro

    def __mod__(self, old: Macro) -> Macro:
        """What the current macros values should be based on a previous/other
        macro. Remove duplicates between two macros for optimization"""
        macro = Macro()
        macro.customs = self.customs
        macro.url = diff_url(self.url, old.url)
        macro.fg = diff_color(self.fg, old.fg)
        macro.bg = diff_color(self.bg, old.bg)
        for mod in ModifierOpen:
            if mod.value & self.mod_open and mod.value & old.mod_open == 0:
                macro.mod_open |= mod.value
        for mod in ModifierClose:
            if mod.value & self.mod_close and mod.value & old.mod_close == 0:
                macro.mod_close |= mod.value
        return macro

    def __str__(self):
        parts = []
        if self.fg is not None:
            parts.append(self.fg if self.fg != RESET else "39")
        if self.bg is not None:
            parts.append(self.bg if self.bg != RESET else "49")

        parts.extend(map_modifers(self.mod_open, self.mod_close))

        result = ""
        if len(parts) > 0:
            result = f"\x1b[{';'.join(parts)}m"
        if self.url is not None:
            if self.url == RESET:
                result += Hyperlink.close
            else:
                result += self.url
        return result

    def __repr__(self):
        parts = []
        if self.fg is not None:
            parts.append(f"{self.fg!r}")
        if self.bg is not None:
            parts.append(f"@{self.bg!r}")

        if self.url is not None:
            parts.append(f"~{self.url}")

        parts.extend(map_modifer_names(self.mod_open, self.mod_close))

        if len(self.customs) > 0:
            parts.append(f"custom=[{', '.join(self.customs)}]")

        return f"Macro({', '.join(parts)})"
