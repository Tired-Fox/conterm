from __future__ import annotations
from sys import stdout
from typing import Any, Literal, overload
from conterm.control.ansi.actions import del_line, up
from conterm.control.ansi import InputManager, Key, Listener

from conterm.printing.markup import Markup

@overload
def prompt(_prompt: str, *, keep: bool = True, color: bool = True, yes_no: Literal[False] = False) -> str:
    ...

@overload
def prompt(_prompt: str, *, keep: bool = True, color: bool = True, yes_no: Literal[True] = True) -> bool:
    ...

def prompt(_prompt: str, *, keep: bool = True, color: bool = True, yes_no: bool = False) -> str | bool:
    result = ""

    if yes_no:
        result = True
        stdout.write(_prompt.strip() + "[Y/n] ")
        stdout.flush()
        for event in InputManager.watch():
            if event == "KEY":
                if event.key == "y" or event.key == "Y":
                    result = True
                    break
                elif event.key == "n" or event.key == "N":
                    result = False
                    break
                elif event.key == "enter":
                    break
    else:
        result = input(f"{_prompt.strip()} ")

    if not keep or color:
        if not yes_no:
            up() 
        del_line()

    if color and keep:
        if yes_no:
            Markup.print(f"[242]{_prompt.strip()} [yellow]{'yes' if result else 'no'}")
        else:
            Markup.print(f"[242]{_prompt.strip()} [yellow]{result}")

    return result

@overload
def select(
    options: list[str],
    *,
    prompt: str = "",
    default: int | None = None,
    style: Literal["icon", "color"] = "icon",
    color: str = "yellow",
    icons: list[str] = ["○", "◉"],
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
    icons: list[str] = ["○", "◉"],
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
    icons: list[str] = ["○", "◉"],
    help: bool = True
) -> str | tuple[str, Any]:
    """Select (radio) terminal input."""

    def clear():
        """Clear select text."""
        count = len(options)
        if prompt != "":
            count += 1
        if help:
            count += 2
        up(count)
        del_line(count)

    def select_print(line: int):
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
                clear()
                select_print(state['line'])
        elif event == "k" or event == "up":
            if state['line'] > 0:
                state['line'] -= 1
                clear()
                select_print(state['line'])
        elif event == "enter":
            return False
    
    state = {
        "line": default if default is not None else 0
    }

    #custom select print
    select_print(state['line'])

    with Listener(on_key=on_key, state=state) as listener:
        listener.join()

    clear()
    prompt = prompt if prompt != "" else "\\[SELECT]:"

    if isinstance(options, dict):
        selection = list(options.keys())[state['line']]
        Markup.print(f"[242]{prompt} [yellow]{selection}")
        return selection, options[selection]

    Markup.print(f"[242]{prompt} [yellow]{options[state['line']]}")
    return options[state['line']]


@overload
def multi_select(
    options: dict[str, Any],
    *,
    prompt: str = "",
    defaults: list[int] | None = None,
    style: Literal["icon", "color"],
    color: str = "yellow",
    icons: list[str] = ["□", "▣"],
    help: bool = True,
) -> dict[str, str]:
    ...

@overload
def multi_select(
    options: list[str],
    *,
    prompt: str = "",
    defaults: list[int] | None = None,
    style: Literal["icon", "color"],
    color: str = "yellow",
    icons: list[str] = ["□", "▣"],
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
    icons: list[str] = ["□", "▣"],
    allow_empty: bool = False,
    help: bool = True
) -> list[str] | dict[str, Any]:
    """Multi select (radio) terminal input."""
    
    def clear(state):
        """Clear select text."""
        count = len(options)
        if prompt != "":
            count += 1
        if help:
            count += 2
        if "msg" in state and state['msg'] != "":
            count += 1
            state['msg'] = ""
        up(count)
        del_line(count)

    def select_print(line: int, state):
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
            clear(state)
            select_print(state['line'], state)
        elif event == "k" or event == "up":
            if state['line'] > 0:
                state['line'] -= 1
            clear(state)
            select_print(state['line'], state)
        elif event == "space":
            if state['line'] in state['selected']:
                state['selected'].remove(state['line'])
            else:
                state['selected'].add(state['line'])
            clear(state)
            select_print(state['line'], state)
        elif event == "enter":
            if len(state['selected']) == 0 and not allow_empty:
                clear(state)
                state['msg'] = "Must select at least one option"
                select_print(state['line'], state)
            else:
                return False

    state = {
        "line": 0,
        "selected": set(defaults or [])
    }

    #custom select print
    select_print(0, state)

    with Listener(on_key=on_key, state=state) as listener:
        listener.join()

    clear(state)
    prompt = prompt if prompt != "" else "\\[MULTI SELECT]:"

    if isinstance(options, dict):
        selection = list(options.keys())
        selection = [selection[option] for option in state['selected']]
        Markup.print(f"[242]{prompt} [yellow]\\[{', '.join(selection)}]")
        return {key: value for key, value in options.items() if key in selection}
    
    selection = [options[line] for line in state["selected"]]
    Markup.print(f"[242]{prompt} [yellow]\\[{', '.join(selection)}]")
    return selection
