from __future__ import annotations
from os import get_terminal_size
from sys import stdout
from typing import Any, Callable, Iterable, Literal, overload
from conterm.control.actions import erase_display, move_to, pos
from conterm.control import Key, Listener

from conterm.pretty.markup import Markup

__all__ = [
    "prompt",
    "select",
    "multi_select"
]

scolor = "green"

def clear(line):
    """Clear select text."""
    move_to(0, line)
    erase_display(0)

def _yes_no_(prompt, keep, color, title):
    start = pos()[1]
    def write(_):
        stdout.write(prompt + "[Y/n] ")
        stdout.flush()

    def on_key(event, state):
        if event == "y" or event == "Y":
            state["result"] = True
            return False
        elif event == "n" or event == "N":
            state["result"] = False
            return False
        elif event.key == "enter":
            return False

    state = {
        "result": True,
    }

    write(state["result"])
    with Listener(on_key=on_key, state=state) as listener:
        listener.join()

    if not keep or color:
        clear(start)

    if color and keep:
        Markup.print(f"[242]{title or prompt} [{scolor}]{'yes' if state['result'] else 'no'}")

    return state["result"]

def _uinput_(prompt, default, keep, color, password, title):
    start = pos()[1]

    def write(result, hide: bool):
        if password:
            stdout.write(f"{prompt} {'*' * len(result) if hide else result}\n[alt+h = show/hide]")
            stdout.flush()
        else:
            stdout.write(f"{prompt} {result}")
            stdout.flush()

    def on_key(event, state):
        if event == "enter":
            return False
        elif event == "backspace":
            state["result"] = state["result"][:-1]
            clear(start)
            write(state["result"], state["hide"])
        elif event == "alt+h" and password:
            state["hide"] = not state["hide"] 
            clear(start)
            write(state["result"], state["hide"])
        elif len(str(event)) == 1:
            state["result"] += str(event)
            clear(start)
            write(state["result"], state["hide"])

    state = {
        "result": default,
        "hide": password
    }

    write(state["result"], state["hide"])
    with Listener(on_key=on_key, state=state) as listener:
        listener.join()

    if not keep or color:
        clear(start)

    if color and keep:
        Markup.print(f"[242]{title or prompt} [{scolor}]{'*' * len(state['result']) if password else state['result']}")

    return state["result"]

def prompt(_prompt: str, *, password: bool = False, default: str = "", title: str | None = None, keep: bool = True, color: bool = True) -> str | bool:
    """Prompt the user for input. This can either be text or Yes/no.

    Args:
        _prompt (str): The prompt to display to the user. If ending with `?` then
            the prompt becomes a Yes/no prompt. Otherwise it must end with `:`
        password (bool): Whether the input is a password. Only applied to normal iput.
            This will hide all input but still collect what is entered.
        keep (bool): Whether to erase the prompt/input after it is submitted
        color (bool): Whether to color the result when it is displayed
    """
    _prompt = _prompt.strip()
    if not _prompt.endswith((":", "?")):
        raise ValueError("Prompts must end with ':' or '?'")

    yes_no = _prompt.endswith("?")

    if yes_no:
        return _yes_no_(_prompt, keep, color, title)
    else:
        return _uinput_(_prompt, default, keep, color, password, title)

@overload
def select(
    options: list[str],
    *,
    prompt: str = "",
    default: int | None = None,
    preprocess: Callable[[str], str] | None = None,
    page_size: int | None = None,
    style: Literal["icon", "color"] = "icon",
    color: str = "yellow",
    title: str | None = None,
    icons: tuple[str, str] = ("○", "◉"),
    help: bool = True
) -> str:
    ...

@overload
def select(
    options: dict[str, Any],
    *,
    prompt: str = "",
    default: int | None = None,
    preprocess: Callable[[str], str] | None = None,
    page_size: int | None = None,
    style: Literal["icon", "color"] = "icon",
    color: str = "yellow",
    title: str | None = None,
    icons: tuple[str, str] = ("○", "◉"),
    help: bool = True
) -> tuple[str, Any]:
    ...

def select(
    options: list[str] | dict[str, Any],
    *,
    prompt: str = "",
    default: int | str | None = None,
    preprocess: Callable[[str], str] | None = None,
    page_size: int | None = None,
    style: Literal["icon", "color"] = "icon",
    color: str = "yellow",
    title: str | None = None,
    icons: tuple[str, str] = ("○", "◉"),
    help: bool = True
) -> str | tuple[str, Any]:
    """Select (radio) terminal input.

    Args:
        prompt (str | None): The prompt to display above the options.
        defaults (int | None): Optional line to start as selected.
        preprocess (Callabe[[str], str]): A preprocess method to apply to the option
            string before it is displayed.
        style ("icon", "color"): Style of how the options are printed.
        color (str): Color to use while printing the select options.
        title (str | None): The text to use when displaying the selection option(s).
        icons (tuple[str, str]): Icons for not selected and selected respectively.
        help (bool): Whether to print select help info at bottom of print.

    Returns:
        Filtered list[str] if list[str] was provided as options.
        Filtered dict[str, Any] if dict[str, Any] was provided as options.
    """
    start = pos()[1]
    page_size = min(page_size or 5, get_terminal_size().lines - 3)

    if default is None:
        default = 0
    elif isinstance(default, str):
        if isinstance(options, list):
            default = options.index(default)
        else:
            default = list(options.keys()).index(default)

    bpad = min(len(options) - 1, default + page_size - 1)
    tpad = max(0, default - (page_size - 1 - (bpad - default)))

    padding = [tpad, bpad]
    keys = [key for key in (options if isinstance(options, list) else options.keys())]

    def write(line: int, padding: list[int]):
        """Print prompt, select options, and help."""
        if prompt != "":
            print(prompt)

        if line > padding[1]:
            padding[0] += 1
            padding[1] += 1
        if line < padding[0]:
            padding[0] = max(0, padding[0] - 1)
            padding[1] = max(page_size - 1, padding[1] - 1)

        if style == "icon":
            for i, option in enumerate(keys):
                if i >= padding[0] and i <= padding[1]:
                    option = preprocess(option) if preprocess is not None else option
                    symbol = " "
                    if i == padding[0] and padding[0] > 0:
                        symbol = '↑'
                    elif i == padding[1] and padding[1] < len(options) - 1:
                        symbol = '↓'
                    Markup.print(f"{symbol} {icons[int(line == i)]} {option}")
        else:
            for i, option in enumerate(keys):
                if i >= padding[0] and i <= padding[1]:
                    option = preprocess(option) if preprocess is not None else option
                    Markup.print(f"  {f'[{color}]' if i == line else ''}{option}")

        if help:
            print("\n[enter = Submit]")

    def on_key(event: Key, state: dict):
        """Manipulate state based on key events.
        
        j and down increment the line, k and up decrement the line, and enter submits the selection.
        """
        if event == "j" or event == "down":
            if state['line'] < len(options) - 1:
                state['line'] += 1
                clear(start)
                write(state['line'], state["padding"])
        elif event == "k" or event == "up":
            if state['line'] > 0:
                state['line'] -= 1
                clear(start)
                write(state['line'], state["padding"])
        elif event == "enter":
            return False
    
    state = {
        "line": default,
        "padding": padding
    }

    write(state['line'], state["padding"])

    with Listener(on_key=on_key, state=state) as listener:
        listener.join()

    clear(start)
    prompt = prompt if prompt != "" else "\\[SELECT]:"

    if isinstance(options, dict):
        selection = list(options.keys())[state['line']]
        result = selection, options[selection] 
    else:
        selection = options[state['line']]
        result = selection

    Markup.print(f"[242]{title or prompt} [{scolor}]{selection}")
    return result 


@overload
def multi_select(
    options: dict[str, Any],
    *,
    prompt: str = "",
    defaults: Iterable[int] | None = None,
    preprocess: Callable[[str], str] | None = None,
    page_size: int | None = None,
    style: Literal["icon", "color"] = "icon",
    color: str = "yellow",
    title: str | None = None,
    icons: tuple[str, str] = ("□", "▣"),
    allow_empty: bool = False,
    help: bool = True,
) -> dict[str, str]:
    ...

@overload
def multi_select(
    options: list[str],
    *,
    prompt: str = "",
    defaults: Iterable[int] | None = None,
    preprocess: Callable[[str], str] | None = None,
    page_size: int | None = None,
    style: Literal["icon", "color"] = "icon",
    color: str = "yellow",
    title: str | None = None,
    icons: tuple[str, str] = ("□", "▣"),
    allow_empty: bool = False,
    help: bool = True
) -> list[str]:
    ...

def multi_select(
    options: list[str] | dict[str, Any],
    *,
    prompt: str = "",
    defaults: Iterable[int] | None = None,
    preprocess: Callable[[str], str] | None = None,
    page_size: int | None = None,
    style: Literal["icon", "color"] = "icon",
    color: str = "yellow",
    title: str | None = None,
    icons: tuple[str, str] = ("□", "▣"),
    allow_empty: bool = False,
    help: bool = True
) -> list[str] | dict[str, Any]:
    """Multi select (radio) terminal input.
    
    Args:
        prompt (str | None): The prompt to display above the options.
        defaults (list[int] | None): Optionally have certain lines pre selected.
        style ("icon", "color"): Style of how the options are printed.
        color (str): Color to use while printing the multi select options.
        title (str | None): The text to use when displaying the selection option(s).
        icons (tuple[str, str]): Icons for not selected and selected respectively.
        allow_empty (bool): Whether to allow user to submit empty results. Defaults to False.
        help (bool): Whether to print multi select help info at bottom of print.

    Returns:
        Filtered list[str] if list[str] was provided as options.
        Filtered dict[str, Any] if dict[str, Any] was provided as options.
    """
    start = pos()[1]
    page_size = min(page_size if page_size is not None else 5, get_terminal_size().lines - 3)

    def get_default_index(default: str) -> int:
        if isinstance(options, list):
            return options.index(default)
        else:
            return list(options.keys()).index(default)

    selected = [get_default_index(default) for default in defaults or []]
    keys = [key for key in (options if isinstance(options, list) else options.keys())]

    bpad = page_size - 1
    tpad = 0
    default = 0

    if len(selected) > 0:
        default = selected[0]
        bpad = min(len(options) - 1, default + page_size - 1)
        tpad = max(0, default - (page_size - 1 - (bpad - default)))
    padding = [tpad, bpad]
    
    def write(line: int, state):
        """Print prompt, select options, and help."""
        if prompt != "":
            print(prompt)

        if line > state['padding'][1]:
            state['padding'][0] += 1
            state['padding'][1] += 1
        if line < state['padding'][0]:
            state['padding'][0] = max(0, state['padding'][0] - 1)
            state['padding'][1] = max(page_size - 1, state['padding'][1] - 1)

        if style == "icon":
            for i, option in enumerate(keys):
                if i >= state['padding'][0] and i <= state['padding'][1]:
                    option = preprocess(option) if preprocess is not None else option
                    symbol = " "
                    if i == state['padding'][0] and state['padding'][0] > 0:
                        symbol = '↑'
                    elif i == state['padding'][1] and state['padding'][1] < len(options) - 1:
                        symbol = '↓'
                    Markup.print(f"{symbol} {icons[int(i in state['selected'])]} {'[yellow]' if i == line else ''}{option}")
        else:
            for i, option in enumerate(keys):
                if i >= state['padding'][0] and i <= state['padding'][1]:
                    option = preprocess(option) if preprocess is not None else option
                    symbol = " "
                    if i == state['padding'][0] and state['padding'][0] > 0:
                        symbol = '↑'
                    elif i == state['padding'][1] and state['padding'][1] < len(options) - 1:
                        symbol = '↓'
                    Markup.print(f"{symbol} {f'[{color}]'if i in state['selected'] else ''}{'[b]' if i == line else ''}{option}")

        print()
        if len(options) > page_size:
            selected_options = ', '.join(f'\x1b[33m{keys[i]}\x1b[39m' for i in state['selected'])
            print(f"[{selected_options}]")
        if help:
            msg = "[space = select, enter = Submit]"
            if "msg" in state and state['msg'] != "":
                msg = f"{state['msg']}\n[space = select, enter = Submit]"
            print(msg)

    def on_key(event: Key, state: dict):
        """Manipulate state based on key events.
        
        j and down increment the line, k and up decrement the line, and enter submits the selection.
        """
        if event == "j" or event == "down":
            if state['line'] < len(options) - 1:
                state['line'] += 1
            clear(start)
            write(state['line'], state)
        elif event == "k" or event == "up":
            if state['line'] > 0:
                state['line'] -= 1
            clear(start)
            write(state['line'], state)
        elif event == " ":
            if state['line'] in state['selected']:
                state['selected'].remove(state['line'])
            else:
                state['selected'].add(state['line'])
            clear(start)
            write(state['line'], state)
        elif event == "enter":
            if not allow_empty and len(state['selected']) == 0:
                clear(start)
                state['msg'] = "\x1b[31;1mMust select at least one option\x1b[39;22m"
                write(state['line'], state)
            else:
                return False

    state = {
        "line": default,
        "selected": set(selected),
        "padding": padding
    }

    #custom select print
    write(0, state)

    with Listener(on_key=on_key, state=state) as listener:
        listener.join()

    clear(start)
    prompt = prompt if prompt != "" else "\\[MULTI SELECT]:"

    if isinstance(options, dict):
        selection = list(options.keys())
        selection = [selection[option] for option in state['selected']]
        result = {key: value for key, value in options.items() if key in selection} 
    else:
        selection = [options[line] for line in state["selected"]]
        result = selection
    
    Markup.print(f"[242]{title or prompt}[/] \\[{', '.join(f'[{scolor}]{opt}[/]' for opt in selection)}]")
    return selection
