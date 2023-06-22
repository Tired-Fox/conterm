"""Write out to terminal with ansi encoding. This is done with a simple in string
markup language.

Macros are wrapped in `[]`. Macros can be escaped with `\\`. When inside a macro
operations can be defined which are applied to all text following the macro.
`/` inside of a macro will signify that a operation is to end/reset.

All macros are automatically closed at the end of the string

Ansi Open Operations:
    - Styling
        - `fg=color` Foreground color
        - `bg=color` Background Color
        - `color=color` Both foreground and background color
        - `i` italisize
        - `b` bold
        - `u` underline
        - `s` strikethrough
    - `url` sets next text as hypertext and as the link. Can use `=` to set link
    - `{name}` uses a custom macro provided by the user
    - `stash` stashes styling. Can use `=` to give a name to the stash
    - `pop` pops a stashed style. Can use `=` to pop a specific stash

Ansi close Operations (`/`):
    - Use respective symbol to reset/close/end that macro/ansi operations
    - Empty `/` without any symbols resets all styling
"""
from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
import re
from typing import Any

from conterm.markup import Markup

SAMPLE = "[i b u s fg=white bg=blue]Some very styled text \\\\ \\[not macro]"
SAMPLE2 = (
    "[i b u s fg=red]Some very styled text,[/][bg=red] now removed italic and bold[/bg u s] back again"
)
URL = "[url=https://example.com]https://example.com[/url] [url=https://example.com]Example Url"
CUSTOM = "[rainbow]Custom Rainbow Text"

def rainbow(text: str) -> str:
    color = 1
    result = ""
    for c in text:
        result += f"\x1b[3{color}m{c}"
        color = (color % 7) + 1
    # Temp
    result += "\x1b[39m"
    return result

if __name__ == "__main__":
    print(Markup.strip(Markup.parse(SAMPLE, SAMPLE2, URL)))
    Markup.print(SAMPLE, SAMPLE2, URL)
