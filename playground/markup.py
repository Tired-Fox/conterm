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
from conterm.markup import Markup
from conterm.markup.macro import Macro

SAMPLE = "[i b u s white @blue]Some very styled text \\\\ \\[not macro]"
SAMPLE2 = (
    "[i b u s red]Some very styled text, [/ @red]only bg color, [/bg u s] back again"
)
URL = "[~https://example.com]https://example.com[/~] [~https://example.com]Example Url"
CUSTOM = "[rainbow time]$1"

from datetime import datetime
import pytermgui as ptg
from rich import print as pprint
from rich.console import Console

@Markup.custom()
def time_now() -> str:
    return str(datetime.now().strftime("%H:%M"))

@Markup.custom(True)
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
    # print(repr(Macro("[b d i u s sb rb r #f32 @#f32]")))
    # print(repr(Macro("[/b /d /i /u /s /sb /rb /r /fg /bg]")))

    # first = Macro("[b d sb r]")
    # second = Macro("[b /d sb /r u #f32]")
    # print(repr(first + second))
    # print(repr(first ^ second))

    print(Markup.strip(Markup.parse(SAMPLE, SAMPLE2, URL, CUSTOM, customs=[rainbow, ("time", time_now)])))
    Markup.print(SAMPLE, SAMPLE2, URL, CUSTOM, customs=[rainbow, ("time", time_now)])

    if False:
        from time import time_ns
        console = Console()
        # Test of speed between conterm, pytermgui, and rich.console
        start = time_ns()
        Markup.print("[b i u red]Hello World!")
        print(time_ns() - start) 
        start = time_ns()
        ptg.tim.print("[bold italic underline red]Hello World!")
        print(time_ns() - start) 
        start = time_ns()
        console.print("[bold italic underline red]Hello World!")
        print(time_ns() - start) 
