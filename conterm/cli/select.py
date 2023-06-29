from __future__ import annotations
from sys import stdout
from typing import Any, Literal, overload
from conterm.control.ansi.actions import del_line, up
from conterm.control.ansi import Key, Listener

from conterm.pretty.markup import Markup

__all__ = [
    "prompt",
    "select",
    "multi_select"
]

def _select_clear_(options, prompt, help, msg=False):
    """Clear select text."""
    count = options
    if prompt != "":
        count += 1
    if help:
        count += 2
    if msg:
        count += 1
    up(count)
    del_line(count)

def _yes_no_(prompt, keep, color):
    def write(_):
        stdout.write(prompt + "[Y/n] ")
        stdout.flush()

    def clear():
        del_line()

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
        clear()

    if color and keep:
        Markup.print(f"[242]{prompt} [yellow]{'yes' if state['result'] else 'no'}")

    return state["result"]

def _uinput_(prompt, keep, color, password):
    def clear():
        if password:
            up()
            del_line(2)
        else:
            del_line()

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
            clear()
            write(state["result"], state["hide"])
        elif event == "alt+h" and password:
            state["hide"] = not state["hide"] 
            clear()
            write(state["result"], state["hide"])
        elif len(str(event)) == 1:
            state["result"] += str(event)
            clear()
            write(state["result"], state["hide"])

    state = {
        "result": "",
        "hide": password
    }

    write(state["result"], state["hide"])
    with Listener(on_key=on_key, state=state) as listener:
        listener.join()

    if not keep or color:
        clear()

    if color and keep:
        Markup.print(f"[242]{prompt} [yellow]{'*' * len(state['result']) if password else state['result']}")

    return state["result"]

def prompt(_prompt: str, *, password: bool = False, keep: bool = True, color: bool = True) -> str | bool:
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
        return _yes_no_(_prompt, keep, color)
    else:
        return _uinput_(_prompt, keep, color, password)

@overload
def select(
    options: list[str],
    *,
    prompt: str = "",
    default: int | None = None,
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
    default: int | None = None,
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
        style ("icon", "color"): Style of how the options are printed.
        color (str): Color to use while printing the select options.
        title (str | None): The text to use when displaying the selection option(s).
        icons (tuple[str, str]): Icons for not selected and selected respectively.
        help (bool): Whether to print select help info at bottom of print.

    Returns:
        Filtered list[str] if list[str] was provided as options.
        Filtered dict[str, Any] if dict[str, Any] was provided as options.
    """

    def write(line: int):
        """Print prompt, select options, and help."""
        if prompt != "":
            print(prompt)

        if style == "icon":
            for i, option in enumerate(options if not isinstance(options, dict) else options.keys()):
                Markup.print(f"  {icons[int(line == i)]} {option}")
        else:
            for i, option in enumerate(options if not isinstance(options, dict) else options.keys()):
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
                _select_clear_(len(options), prompt, help)
                write(state['line'])
        elif event == "k" or event == "up":
            if state['line'] > 0:
                state['line'] -= 1
                _select_clear_(len(options), prompt, help)
                write(state['line'])
        elif event == "enter":
            return False
    
    state = {
        "line": default if default is not None else 0
    }

    #custom select print
    write(state['line'])

    with Listener(on_key=on_key, state=state) as listener:
        listener.join()

    _select_clear_(len(options), prompt, help)
    prompt = prompt if prompt != "" else "\\[SELECT]:"

    if isinstance(options, dict):
        selection = list(options.keys())[state['line']]
        Markup.print(f"[242]{title or prompt}  [yellow]{selection}")
        return selection, options[selection]

    Markup.print(f"[242]{title or prompt}  [yellow]{options[state['line']]}")
    return options[state['line']]


@overload
def multi_select(
    options: dict[str, Any],
    *,
    prompt: str = "",
    defaults: list[int] | None = None,
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
    defaults: list[int] | None = None,
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
    defaults: list[int] | None = None,
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
    
    def write(line: int, state):
        """Print prompt, select options, and help."""
        if prompt != "":
            print(prompt)

        if style == "icon":
            for i, option in enumerate(options if not isinstance(options, dict) else options.keys()):
                Markup.print(f"  {icons[int(i in state['selected'])]} {'[yellow]' if i == line else ''}{option}")
        else:
            for i, option in enumerate(options if not isinstance(options, dict) else options.keys()):
                Markup.print(f" {f'[{color}]'if i in state['selected'] else ''}{'[b]' if i == line else ''}{option}")

        if help:
            msg = "\n[space = select, enter = Submit]"
            if "msg" in state and state['msg'] != "":
                msg = f"\n{state['msg']}\n[space = select, enter = Submit]"
            print(msg)

    def on_key(event: Key, state: dict):
        """Manipulate state based on key events.
        
        j and down increment the line, k and up decrement the line, and enter submits the selection.
        """
        if event == "j" or event == "down":
            if state['line'] < len(options) - 1:
                state['line'] += 1
            _select_clear_(len(options), prompt, help, "msg" in state and state['msg'] != "")
            write(state['line'], state)
        elif event == "k" or event == "up":
            if state['line'] > 0:
                state['line'] -= 1
            _select_clear_(len(options), prompt, help, "msg" in state and state['msg'] != "")
            write(state['line'], state)
        elif event == " ":
            if state['line'] in state['selected']:
                state['selected'].remove(state['line'])
            else:
                state['selected'].add(state['line'])
            _select_clear_(len(options), prompt, help, "msg" in state and state['msg'] != "")
            write(state['line'], state)
        elif event == "enter":
            if not allow_empty and len(state['selected']) == 0:
                _select_clear_(len(options), prompt, help, "msg" in state and state['msg'] != "")
                state['msg'] = "\x1b[31;1mMust select at least one option\x1b[39;22m"
                write(state['line'], state)
            else:
                return False

    state = {
        "line": 0,
        "selected": set(defaults or [])
    }

    #custom select print
    write(0, state)

    with Listener(on_key=on_key, state=state) as listener:
        listener.join()

    _select_clear_(len(options), prompt, help, "msg" in state and state['msg'] != "")
    prompt = prompt if prompt != "" else "\\[MULTI SELECT]:"

    if isinstance(options, dict):
        selection = list(options.keys())
        selection = [selection[option] for option in state['selected']]
        Markup.print(f"[242]{title or prompt}  [yellow]\\[{', '.join(selection)}]")
        return {key: value for key, value in options.items() if key in selection}
    
    selection = [options[line] for line in state["selected"]]
    Markup.print(f"[242]{title or prompt}  [yellow]\\[{', '.join(selection)}]")
    return selection
