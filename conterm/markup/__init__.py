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
import re
from typing import TYPE_CHECKING

from .macro import CustomMacros, Macro, RESET
from .color import Color
from .hyperlink import Hyperlink

if TYPE_CHECKING:
    from _typeshed import SupportsWrite

MACRO = re.compile(r"(?<!\\)\[[^\]]+(?<!\\)\]")

__all__ = ["Markup", "Macro", "Color", "Hyperlink"]


class Markup:
    def __init__(self) -> None:
        self.markup = ""
        self._result_ = ""

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
        self, markup: str, _: CustomMacros or None = None
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

    def __parse__(self, tokens: list[Macro | str], *, close: bool = True) -> str:
        output = ""
        cmacro = Macro("")
        previous = "text"
        url_open = False

        for token in tokens:
            if isinstance(token, Macro):
                if previous == "macro":
                    cmacro += token
                else:
                    cmacro = token.calc(cmacro)
                previous = "macro"
            else:
                previous = "text"
                if isinstance(cmacro.url, str):
                    url_open = True
                elif cmacro.url == RESET:
                    url_open = False

                output += f"{cmacro}{token}"

        if close:
            output += f"\x1b[0m{Hyperlink.close if url_open else ''}"
        return output

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
        sep: str = " ",
        end: str = "\n",
        file: "SupportsWrite[str] | None" = None,
    ):
        """Print in string markup to stdout with a space gap."""
        print(Markup.parse(*markup, sep=sep), end=end, file=file)

    @staticmethod
    def parse(*markup: str, sep: str = " ") -> str:
        """Parse in string markup and return the ansi encoded string."""
        if len(markup) > 0:
            parser = Markup()

            parser.feed(markup[0])
            for text in markup[1:]:
                parser.feed(text, sep=sep)

            return str(parser)
        return ""
