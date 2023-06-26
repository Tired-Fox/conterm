"""Write out to terminal with ansi encoding. This is done with a simple in string
markup language.

Macros are wrapped in `[]`. Macros can be escaped with `\\`. When inside a macro
operations can be defined which are applied to all text following the macro.
`/` inside of a macro will signify that a operation is to end/reset.

All macros are automatically closed at the end of the string

Ansi Open Operations:
    - Styling
        - `r,g,b|#rrggbb|#rgb|xterm|system` Foreground color
        - `@<color>` Background Color
        - `i` italisize
        - `b` bold
        - `u` underline
        - `s` strikethrough
        - `d` dim
        - `r` reverse
        - `sb` slow blink
        - `rb` rapid blink
    - `~<url>` sets next text as hypertext
    - `<custom>` uses a custom macro provided by the user. Token that isn't a sys color
    - `stash` stashes styling current styling, doesn't include current macro that it is in.
    - `pop` pops the top stashed macro

Ansi close Operations (`/`):
    - Use respective symbol to reset/close/end that macro/ansi operations
    - Empty `/` without any symbols resets all styling

TODO:
    - [x] Parse stash and pop
    - [x] Parse alignment with `[<^>]{size}`. Left, center, right respecively followed
        by the width in characters
    - [x] alignment percentages or full width
    - [x] negative alignment subtracts from full width
    - [ ] Add support for terminal color mode detection
        - [ ] gray scale
        - [ ] 8 bit
        - [ ] 16 bit
        - [ ] full color
"""
from __future__ import annotations
import sys

from conterm.markup import Markup

# from conterm.markup.macro import Macro
ALIGN = "[<8]\\[[red]ERROR[/fg]][^-8 240]Hello World"
SAMPLE = "[i b u s white @blue]Some very styled text \\\\ \\[not macro]"
SAMPLE2 = (
    "[i b u s red]Some very styled text, [/ @red]only bg color, [/bg u s] back again"
)
URL = "[~https://example.com]https://example.com[/~] [~https://example.com]Example Url"
CUSTOM = "[rainbow time]$1"

from datetime import datetime

import pytermgui as ptg
from rich.console import Console


@Markup.insert
def time_now() -> str:
    return str(datetime.now().strftime("%H:%M"))

@Markup.modify
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
    # print(repr(first % second))

    print(Markup.strip(Markup.parse(ALIGN, SAMPLE, SAMPLE2, URL, CUSTOM, customs=[rainbow, ("time", time_now)])))
    Markup.print(ALIGN, SAMPLE, SAMPLE2, URL, CUSTOM, customs=[rainbow, ("time", time_now)])
    print("\n")

    
    output = "[^full]"
    for i in range(8):
        output += f"[{i}]▀"
    output += "    " 
    for i in range(8, 16):
        output += f"[{i}]▀"

    output += "[^full]"
    for color in range(23):
        output += f"[{232 + color} @{min(232 + color + 1, 255)}]▀"
    output += "[/fg /bg /^]\n\n"

    cursor = 16
    output += "[^full]"
    for row in range(1, 4):
        for column in range(37):
            if column == 36:
                continue

            output += f"[{cursor + column} @{cursor + column + 36}]▀"
        output += "[/fg /bg ^full]"
        cursor += 72
        if cursor > 232:
            break
    output = Markup.parse(output)
    # print(repr(output))
    print(output)

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
