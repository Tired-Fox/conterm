from sys import stdin, stdout
from typing import Literal
from . import read, read_ready

def up(count: int = 1):
    stdout.write(f"\x1b[{count}A")
    stdout.flush()

def down(count: int = 1):
    stdout.write(f"\x1b[{count}B")
    stdout.flush()

def left(count: int = 1):
    stdout.write(f"\x1b[{count}C")
    stdout.flush()

def right(count: int = 1):
    stdout.write(f"\x1b[{count}D")
    stdout.flush()

def to_x(_x: int = 0):
    stdout.write(f"\x1b[{_x}G")
    stdout.flush()

def to_y(_y: int = 0):
    stdout.write(f"\x1b[{_y}d")
    stdout.flush()

def move_to(_x: int = 0, _y: int = 0):
    if _x == 0 and _y == 0:
        stdout.write("\x1b[H")
    else:
        stdout.write(f"\x1b[{_y};{_x}H")
    stdout.flush()

def save_pos():
    stdout.write(f"\x1b[s")
    stdout.flush()

def restore_pos():
    stdout.write(f"\x1b[u")
    stdout.flush()

def delete(count: int = 1):
    stdout.write(f"\x1b[{count}P")
    stdout.flush()

def erase(count: int = 1):
    stdout.write(f"\x1b[{count}X")
    stdout.flush()

def del_line(count: int = 1):
    stdout.write(f"\x1b[{count}M")
    stdout.flush()

def erase_display(mode: Literal[0, 1, 2] = 2):
    """Erase in the erase_display
    
    Modes:
        0: Erase from start of display to cursor
        1: Erase from cursor to end of display
        2: Erase entire display
    """
    stdout.write(f"\x1b[{mode}J")
    stdout.flush()

def cursor(mode: Literal[0, 1, 2, 3, 4, 5, 6] | None = None, show: bool | None = None):
    """Set the cursor shape

    Args:
        mode (int, None): The shape of the cursor. Optional.
        show (bool, None): Whether to show or hide the cursor. Optional.

    Modes:
        0: User Shape
        1: Blinking Block
        2: Steady Block
        3: Blinking Underline
        4: Steady Underline
        5: Blinking Bar
        6: Steady Bar
    """
    if mode is not None:
        stdout.write(f"\x1b[{mode}q")
    if show is not None:
        stdout.write(f"\x1b[25{'h' if show else 'l'}")
    stdout.flush()

def insert_line(count: int = 1):
    stdout.write(f"\x1b[{count}L")
    stdout.flush()

def set_title(title: str = ""):
    stdout.write(f"\x1b]0;{title}\x07")
    stdout.flush()

def pos() -> tuple[int, int]:
    """Get the cursors current position. (x, y)

    Returns:
        (int, int): The x and y coordinates of the cursor.
    """
    stdout.write("\x1b[6n")
    stdout.flush()

    # Collect input which could be blank meaning no ansi input
    char = ""
    try:
        char += read(1)
        while read_ready(stdin):
            char += read(1)
    finally: pass

    char = char.lstrip("\x1b[").rstrip("R")
    y, x = char.split(";")
    return int(x), int(y)
