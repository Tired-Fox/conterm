from inspect import isclass
from typing import Any

from .themes import ONE_DARK, Theme

from .markup import Markup

# TODO: Theme: Presets and user defined overrides

THEME = ONE_DARK 

def pprint(*args: Any, sep: str = " ", end: str = "\n", theme: Theme = THEME):
    """Pretty print text and objects to stdout.

    Args:
        str: Processes and conterm.pretty.markup
        object: print the representation with color using conterm.pretty.markup
    """

    # recursive
    output = []
    for arg in args:
        if isinstance(arg, str):
            output.append(Markup.parse(arg))
        else:
            output.append(_pp_(arg, theme=theme))
    print(sep.join(output), end=end)

def _pp_(value: Any, indent: int = 0, theme: dict = THEME) -> str:
    if isinstance(value, (list, set, tuple)):
        return _pp_collection_(value, indent, theme)
    elif isinstance(value, (int, float, type(None), str)):
        return _pp_native_(value, theme)
    elif isinstance(value, dict):
        return _pp_dict_(value, indent, theme)
    elif callable(value):
        if isclass(value):
            if not isinstance(value, type):
                value = type(value)
            return Markup.parse(f"<[{theme['keyword']}]class[/fg] [{theme['object']}]{value.__name__}[/fg]>")
        else:
            parts = str(value).split(" ")
            return Markup.parse(f"<[{theme['keyword']}]function[/fg] [{theme['object']}]{parts[1]}[/fg] [{theme['keyword']}]at[/fg] [{theme['comment']}]{parts[-1][:-1]}[/fg]>")
    return str(value)
    # Iterable(1, 2, 3, ...)
    # Function
    # Class
    # Signatures

def _pp_collection_(value: list | set | tuple, indent: int = 0, theme: dict = THEME) -> str:
    brackets = ["[", "]"]
    if isinstance(value, set):
        brackets = ["{", "}"]
    elif isinstance(value, tuple):
        brackets = ["(", ")"]

    padding = " " * (indent + 2)

    items = []
    break_line = False
    for item in value:
        items.append(_pp_(item, indent + 2, theme))
        if isinstance(item, (list, dict, set, tuple)):
            break_line = True

    if break_line or (indent > 0 and len(value) > 1) or len(value) > 5:
        items = [f"\n{padding}{item}," for item in items]
        return f"{brackets[0]}{''.join(items)}\n{' '*indent}{brackets[1]}"
    else:
       return f"{brackets[0]}{', '.join(_pp_(item, indent + 2, theme) for item in value)}{brackets[1]}" 


def _pp_dict_(value: dict, indent: int = 0, theme: dict = THEME) -> str:
    # Key -> Value
    # Recursive format value
    items = [f"{_pp_(k, indent + 2, theme)}: {_pp_(v, indent+2, theme)}" for k, v in value.items()]
    if len(value) > 1:
        items = ''.join([f"\n{' ' * (indent + 2)}{item}," for item in items])
        return f"{{{items}\n{' '*indent}}}"
    else:
        return f"{{ {', '.join(items)} }}"

def _pp_native_(value: int | float | str | None, theme: dict = THEME) -> str:
    if value is None:
        return Markup.parse(f"[{theme['keyword']}]None")
    if isinstance(value, int | float):
        return Markup.parse(f"[{theme['number']}]{value}")
    if isinstance(value, str):
        return Markup.parse(f"[{theme['string']}]{value!r}")
    return str(value)
