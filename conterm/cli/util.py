import contextlib
from io import StringIO
from typing import Any, Callable, Literal, overload

__all__ = [
    "catch_stdout",
    "catch_stderr",
    "run_click"
]

# Trick type system to think a string is returned if result is set to False
@overload
def catch_stdout(result: Literal[True] = True) -> Callable[..., Callable[..., tuple[Any, str]]]:
    ...

# Trick type system to think a tuple[Any, str] is returned if result is set to False
@overload
def catch_stdout(result: Literal[False] = False) -> Callable[..., Callable[..., str]]:
    ...

def catch_stdout(result: Literal[True, False] = True):
    def wrapper(func: Callable):
        def decorator(*args, **kwargs) -> tuple[Any, str] | str:
            out = StringIO("")

            with contextlib.redirect_stdout(out):
                result = func(*args, **kwargs)

            out.seek(0)
            stdout = out.read()
            out.close()

            if result:
                return result, stdout
            return stdout
        return decorator
    return wrapper

# Trick type system to think a string is returned if result is set to False
@overload
def catch_stderr(result: Literal[True] = True) -> Callable[..., Callable[..., tuple[Any, str]]]:
    ...

# Trick type system to think a tuple[Any, str] is returned if result is set to False
@overload
def catch_stderr(result: Literal[False] = False) -> Callable[..., Callable[..., str]]:
    ...

def catch_stderr(result: Literal[True, False] = True):
    def wrapper(func: Callable):
        def decorator(*args, **kwargs) -> tuple[Any, str] | str:
            out = StringIO("")

            with contextlib.redirect_stderr(out):
                result = func(*args, **kwargs)

            out.seek(0)
            stdout = out.read()
            out.close()

            if result:
                return result, stdout
            return stdout
        return decorator
    return wrapper

@catch_stdout(result=False)
def run_click(entry, cmd: list[str] | str):
    """Method that runs a click command/group with a cmd and returns
    the stdout, if there is one.

    Args:
        - entry (click.Group | click.Command): The click entry point.
        - cmd (str | list[str]): The command to pass to the click entry point.
    """
    import click
    if not isinstance(entry, (click.Group, click.Command)):
        raise TypeError("Expected click entry point to be a click Group or Command.")

    try:
        if isinstance(cmd, str):
            entry.main(cmd.replace("  ", " ").split(" "))
        elif isinstance(cmd, list):
            entry.main(cmd)
        else:
            raise ValueError("Expected args to be a string or a list of strings")
    # Catch end of cli parse (SystemExit), so program doesn't exit
    except SystemExit:
        pass
