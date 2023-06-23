"""conterm's markup module

This module is centered around pretty printing items to the screen.

For now it only implements an in string markup language for easy to write
stylized terminal output

Todo:
    - inline/in string markup
        - [ ] Custom Macros
        - [ ] Stash styling
        - [ ] Pop styling
        - [ ] Url collecting next string for link
    - Pretty Print
        - [ ] Themes: Dracula, Nord, One Dark, etc...
        - [ ] native types: int/float, string, bool, None, Object, dict, list, set, tuple
        - [ ] Code Blocks?
            - Using a langauge parser
"""
from collections.abc import Callable
from functools import wraps
import re
from typing import TYPE_CHECKING

from .macro import CustomMacros, Macro, RESET
from .color import Color
from .hyperlink import Hyperlink

def sort_customs(custom: tuple[str, Callable]):
    if not hasattr(custom[1], "__custom_modify__"):
        return 3
    return 2 if getattr(custom[1], "__custom_modify__") else 1

if TYPE_CHECKING:
    from _typeshed import SupportsWrite

MACRO = re.compile(r"(?<!\\)\[[^\]]+(?<!\\)\]")

__all__ = ["Markup", "Macro", "Color", "Hyperlink"]

class Markup:
    def __init__(self, customs: list[Callable|tuple[str,Callable]] | None = None) -> None:
        self.markup = ""
        self._result_ = ""
        self._customs_: CustomMacros = {}
        for custom in customs or []:
            if isinstance(custom, tuple):
                self._customs_[custom[0]] = custom[1]
            else:
                self._customs_[custom.__name__] = custom

        self._stash_ = {}
        self._stash_stack_ = []

    def stash(self, macro: Macro, name: str = ""):
        if name == "":
            name = f"{macro.macro}-{len(self._stash_stack_)}"
        self._stash_[name] = macro
        self._stash_stack_.append(name)

    def pop(self, key: str | None = None) -> Macro | None:
        """Pop a stashed macro from the stack. Optionally pop a named stashed macro.
        
        Returns:
            None when there are no macro's to pop
        """
        if key is None:
            return self._stash_.pop(self._stash_stack_.pop())

        index = self._stash_stack_.index(key)
        self._stash_stack_.pop(index)
        return self._stash_.pop(key)

    def feed(self, markup: str, *, sep: str = ""):
        """Feed/give the parser more markup to handle.
        The markup is added to the current markup and reuslt with a space gap."""
        self.markup += f"{sep}{markup}"
        self._result_ += f"{sep}{self.__parse__(self.__tokenize__(markup))}"

    def __str__(self) -> str:
        return self._result_

    def __repr__(self) -> str:
        return self.markup

    def __tokenize__(
        self, markup: str
    ) -> list[Macro | str]:
        tokens = []
        last = 0

        for macro in MACRO.finditer(markup):
            if macro.start() > last:
                tokens.append(
                    re.sub(
                        r"(?<!\\)\\(?!\\)", "", markup[last : macro.start()]
                    ).replace("\\\\", "\\")
                )
            last = macro.start() + len(macro.group(0))
            tokens.append(Macro(macro.group(0)))
        if last < len(markup):
            tokens.append(
                re.sub(r"(?<!\\)\\(?!\\)", "", markup[last:]).replace("\\\\", "\\")
            )

        return tokens

    def __stash_pop__(self, cmacro: Macro, token: Macro) -> Macro:
        if token.stash:
            self.stash(cmacro)
            cmacro = Macro()
        if token.pop:
            if (
                isinstance(token.pop, str)
                and token.pop != ""
                and (val := self.pop(token.pop)) is not None
            ):
                cmacro = val
            elif (val := self.pop()):
                cmacro = val 
        return cmacro

    def collect_customs(self, customs: list[str]):
        return sorted(
            map(
                lambda c: (c, self._customs_[c]),
                filter(
                    lambda f: f in self._customs_, 
                    customs
                ), 
            ),
            key=sort_customs
        )

    def __parse__(self, tokens: list[Macro | str], *, close: bool = True) -> str:
        output = ""
        cmacro = Macro()
        previous = "text"
        url_open = False

        for token in tokens:
            if isinstance(token, Macro):
                cmacro = self.__stash_pop__(cmacro, token)
                if previous == "macro":
                    cmacro += token
                else:
                    cmacro = token % cmacro
                previous = "macro"
            else:
                previous = "text"
                if isinstance(cmacro.url, str):
                    url_open = True
                elif cmacro.url == RESET:
                    url_open = False

                repl = 1
                # PERF: Use name loop arg for exceptions
                for _, custom in self.collect_customs(cmacro.customs):
                    modify = getattr(custom, "__custom_modify__")
                    if modify:
                        token = str(custom(token))
                    else:
                        token = re.sub(f"\\${repl}", str(custom(token)), token, 1)
                        repl += 1

                output += f"{cmacro}{token}"

        if close:
            output += f"\x1b[0m{Hyperlink.close if url_open else ''}"
        return output

    @staticmethod
    def custom(modify: bool = False):
        """Create a custom macro. If args is true then
        the next text token is passed in to be modified and returned. If
        args is left out or is False then the next text element will have the
        result of the method inserted similar to regex, using `$1..9`.

        Example:
            ```
            @Markup.custom(True)
            def rainbow(text: str) -> str
            ```

            or

            ```
            @Markup.custom()
            def time() -> str
            ```
        """
        def wrapper(func: Callable):
            @wraps(func)
            def decorator(text: str, *args, **kwargs):
                if modify:
                    return func(text)
                return func()
            setattr(decorator, "__custom_modify__", modify)
            return decorator
        return wrapper

    @staticmethod
    def strip(ansi: str = ""):
        """Strip ansi code from a string.

        Note:
            This method uses a regex to parse out any ansi codes. Below is the regex
            `\\x1b\[[<?]?(?:(?:\d{1,3};?)*)[a-zA-Z~]|\\x1b]\d;;[^\\x1b]*\\x1b\\|[\\x00-\\x1B]`
            The regex first trys to match a control sequence, then a link opening or closing
            sequence, finally it wall match any raw input sequence like `\\x04` == `ctrl+d`
        """
        # First check for control sequences. This covers most sequences, but some may slip through
        # Then check for Link opening and closing tags: \x1b]8;;<link>\x1b\ or \x1b]8;;\x1b\
        # Finally check for any raw characters like \x04 == ctrl+d
        return re.sub(
            r"\x1b\[[<?]?(?:(?:\d{1,3};?)*)[a-zA-Z~]|\x1b]\d;;[^\x1b]*\x1b\\|[\x00-\x1B]",
            "",
            ansi,
        )

    @staticmethod
    def print(
        *markup: str,
        customs: list[Callable|tuple[str,Callable]] | None = None,
        sep: str = " ",
        end: str = "\n",
        file: "SupportsWrite[str] | None" = None,
    ):
        """Print in string markup to stdout with a space gap."""
        print(Markup.parse(*markup, customs=customs, sep=sep), end=end, file=file)

    @staticmethod
    def parse(*markup: str, customs: list[Callable|tuple[str,Callable]] | None = None, sep: str = " ") -> str:
        """Parse in string markup and return the ansi encoded string."""
        customs = customs or []

        if len(markup) > 0:
            parser = Markup(customs=customs)

            parser.feed(markup[0])
            for text in markup[1:]:
                parser.feed(text, sep=sep)

            return str(parser)
        return ""
