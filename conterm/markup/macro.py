from __future__ import annotations
from collections.abc import Callable
from enum import Enum
from re import sub
from typing import Any
from .color import Color
from .hyperlink import Hyperlink


class Reset:
    """Extra state class for macros."""

    def __repr__(self) -> str:
        return "RESET"


def _cod(condition, one, default: Any = ""):
    return one if condition else default


class MacroState(Enum):
    Empty = 0
    Close = 1
    Open = 2

    def is_open(self) -> bool:
        """If the macro is open."""
        return self == MacroState.Open

    def is_close(self) -> bool:
        """If the macro is closed."""
        return self == MacroState.Close

    def is_none(self) -> bool:
        """If the macro is not defined."""
        return self == MacroState.Empty

    def rep(self, o, c):
        """Get ansi representation based ont he state."""
        if self == MacroState.Open:
            return str(o)
        if self == MacroState.Close:
            return str(c)
        return ""

    def lit(self, val) -> str:
        """Get the literal representation based on state."""
        if self == MacroState.Open:
            return val
        if self == MacroState.Close:
            return f"/{val}"
        return ""


RESET = Reset()
CustomMacros = dict[str, Callable[[str], str]]


def diff_modifier(current, other):
    if (current == MacroState.Open and other != MacroState.Open) or (
        current == MacroState.Close and other == MacroState.Open
    ):
        return current
    return MacroState.Empty


def diff_url(current, other):
    if (current == RESET and isinstance(other, str)) or (
        isinstance(current, str) and not isinstance(other, str)
    ):
        return current
    if isinstance(current, str) and isinstance(other, str):
        return f"{Hyperlink.close}{current}"
    return None


def diff_color(current, other):
    # None, Reset, Set
    if isinstance(current, str) and len(current) > 0:
        return current
    if current == RESET and other != RESET and other is not None:
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
        "bold",
        "italic",
        "underline",
        "strikethrough",
    )

    def __init__(self, macro: str = ""):
        self.macro = sub(" +", " ", macro)

        self.customs = []
        self.url = None
        self.fg = None
        self.bg = None
        self.bold = MacroState.Empty
        self.italic = MacroState.Empty
        self.underline = MacroState.Empty
        self.strikethrough = MacroState.Empty

        macros = self.macro.lstrip("[").rstrip("]").split(" ")

        if len(macros) == 1 and macros[0] == "/":
            self.__full_reset_macro__()
        else:
            for macro in macros:
                self.__parse_macro__(macro)

    def __full_reset_macro__(self):
        self.url = RESET
        self.fg = RESET
        self.bg = RESET
        self.bold = MacroState.Close
        self.italic = MacroState.Close
        self.underline = MacroState.Close
        self.strikethrough = MacroState.Close

    def __parse_close_macro__(self, macro):
        macro = macro.lstrip("/")
        if macro in "ibus":
            if macro == "i":
                self.italic = MacroState.Close
            elif macro == "b":
                self.bold = MacroState.Close
            elif macro == "u":
                self.underline = MacroState.Close
            elif macro == "s":
                self.strikethrough = MacroState.Close
        elif macro in ["fg", "bg"]:
            if macro.startswith("fg"):
                self.fg = RESET
            else:
                self.bg = RESET
        elif macro.startswith("url"):
            self.url = RESET

    def __parse_open_macro__(self, macro):
        if macro in "ibus":
            if macro == "i":
                self.italic = MacroState.Open
            elif macro == "b":
                self.bold = MacroState.Open
            elif macro == "u":
                self.underline = MacroState.Open
            elif macro == "s":
                self.strikethrough = MacroState.Open
        elif macro[:2] in ["fg", "bg"]:
            if "=" not in macro:
                raise ValueError("Invalid macro color assignment: Missing `=`")
            if macro.startswith("fg"):
                self.fg = Color(macro.split("=", 1)[-1]).fg()
            else:
                self.bg = Color(macro.split("=", 1)[-1]).bg()
        elif macro.startswith("url"):
            if "=" not in macro:
                raise ValueError("Expected url macro to have an link assignment")
            self.url = Hyperlink.open(macro.split("=", 1)[-1])
        elif macro.strip() != "":
            self.customs.append(macro)

    def __parse_macro__(self, macro):
        if macro.startswith("/"):
            self.__parse_close_macro__(macro)
        else:
            self.__parse_open_macro__(macro)

    def __add__(self, other: Macro) -> Macro:
        macro = Macro()
        macro.customs = set([*self.customs, *other.customs])
        macro.url = _cod(other.url is not None, other.url, self.url)
        macro.fg = _cod(other.fg is not None, other.fg, self.fg)
        macro.bg = _cod(other.bg is not None, other.bg, self.bg)
        macro.bold = _cod(other.bold != MacroState.Empty, other.bold, self.bold)
        macro.italic = _cod(other.italic != MacroState.Empty, other.italic, self.italic)
        macro.underline = _cod(
            other.underline != MacroState.Empty, other.underline, self.underline
        )
        macro.strikethrough = _cod(
            other.strikethrough != MacroState.Empty,
            other.strikethrough,
            self.strikethrough,
        )
        return macro

    def calc(self, other: Macro) -> Macro:
        """What the current macros values should be based on a previous/other
        macro."""
        macro = Macro()
        macro.customs = self.customs
        macro.url = diff_url(self.url, other.url)
        macro.fg = diff_color(self.fg, other.fg)
        macro.bg = diff_color(self.bg, other.bg)
        macro.bold = diff_modifier(self.bold, other.bold)
        macro.italic = diff_modifier(self.italic, other.italic)
        macro.underline = diff_modifier(self.underline, other.underline)
        macro.strikethrough = diff_modifier(self.strikethrough, other.strikethrough)
        return macro

    def __str__(self):
        parts = []
        if self.fg is not None:
            parts.append(self.fg if self.fg != RESET else "39")
        if self.bg is not None:
            parts.append(self.bg if self.bg != RESET else "49")

        if not self.bold.is_none():
            parts.append(self.bold.rep(1, 22))
        if not self.italic.is_none():
            parts.append(self.italic.rep(3, 23))
        if not self.underline.is_none():
            parts.append(self.underline.rep(4, 24))
        if not self.strikethrough.is_none():
            parts.append(self.strikethrough.rep(9, 29))

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
        if self.fg != "":
            parts.append(f"fg={self.fg!r}")
        if self.bg != "":
            parts.append(f"bg={self.bg!r}")

        if self.url is not None:
            parts.append(f"url{f'={self.url}' if self.url != '' else ''}")

        if self.bold != MacroState.Empty:
            parts.append(self.bold.lit("bold"))
        if self.italic != MacroState.Empty:
            parts.append(self.italic.lit("italic"))
        if self.underline != MacroState.Empty:
            parts.append(self.underline.lit("underline"))
        if self.strikethrough != MacroState.Empty:
            parts.append(self.strikethrough.lit("strikethrough"))

        if len(self.customs) > 0:
            parts.append(f"custom=[{', '.join(self.customs.keys())}]")

        return f"Macro({', '.join(parts)})"
