"""Conterm logging module.

This module doesn't prove to replace other logging libraries.
It means to only provide a simple logging interface that can be used with this conterm.
"""
from dataclasses import dataclass
from datetime import datetime
from io import TextIOWrapper
from sys import stderr
from threading import Lock
from typing import TextIO

from pathlib import Path

from conterm.pretty.markup import Markup

StrLike = str | Path
Buffer = TextIO | TextIOWrapper

__llock__ = Lock()

_CODES_ = {
    0: ("INFO", "cyan"),
    1: ("WARN", "yellow"),
    2: ("ERROR", "red")
}

@dataclass
class LogLevel:
    """Default log levels.

    Info: 0
    Warn: 1
    Error: 2
    """

    Info = 0
    Warn = 1
    Error = 2

def _format_code_(level: int) -> str:
    if (lvl := _CODES_.get(level, None)) is not None:
        return Markup.parse(f"[{lvl[1]}]{lvl[0]}")
    return str(level)

def log(
    *msg: str,
    level: int = LogLevel.Info,
    fmt: str = "{dt} [{code}] {msg}",
    dt_fmt: str = "%m/%d/%YT%I:%M:%S",
    out: Buffer | StrLike = stderr,
    sep: str = " "
):
    """Log a message to the output.

    Args:
        *msg (str): All parts of the message. Joined by `sep` which is ` ` by default.
        level (int): The log level of the event. This determines what the log code is.
            `LogLevel.Info`, `LogLevel.Warn`, `LogLevel.Error`
        fmt (str): The log format when outputting. Can use keywords `dt`, `code`, and `message` inside
            curly bracets, `{}`. Ex: `{dt} [{code}] {msg}` will produce `03/13/2023T10:52:15 [INFO] Some message`.
            Defaults to `{dt} [{code}] {msg}`
        dt_fmt (str): The `strftime` format to use on the current date passed to the format. This format is
            first applied to the date then the result is passed to the log format. Defaults to `%m/%d/%YT%I:%M:%S`
        out (str | Path | TextIOWrapper): The output source for the logs. If the output is to something other
            than the terminal, ansi sequences are automatically stripped. Defaults to `stderr`.
        sep (str): The seperator to use between message parts. Defaults to ` `.        
    """
    with __llock__:
        code = _format_code_(level)
        _log = fmt.format(
            msg=sep.join(msg),
            code=code,
            dt=datetime.now().strftime(dt_fmt)
        ).strip()

        if isinstance(out, Buffer) and out.isatty():
            out.write(f"{_log.strip()}\n")
        else:
            _log = f"{Markup.strip(_log).strip()}\n"
            if isinstance(out, StrLike):
                with Path(out).open("+a") as file:
                    file.write(_log)
            else:
                out.write(_log)


class Logger:
    """Logger that keeps track of formatting and restricted log level,
    along with custom log levels.

    Args:
        *msg (str): All parts of the message. Joined by `sep` which is ` ` by default.
        fmt (str): The log format when outputting. Can use keywords `dt`, `code`, and `message` inside
            curly bracets, `{}`. Ex: `{dt} [{code}] {msg}` will produce `03/13/2023T10:52:15 [INFO] Some message`.
            Defaults to `{dt} [{code}] {msg}`
        dt_fmt (str): The `strftime` format to use on the current date passed to the format. This format is
            first applied to the date then the result is passed to the log format. Defaults to `%m/%d/%YT%I:%M:%S`.
        out (str | Path | TextIOWrapper): The output source for the logs. If the output is to something other
            than the terminal, ansi sequences are automatically stripped. Defaults to `stderr`.
        min_level (int): The log level of the event. This determines what the log code is.
            `LogLevel.Info`, `LogLevel.Warn`, `LogLevel.Error`. Defaults to `LogLevel.Info`.
        codes (list[tuple[int, str, str]]): List of custom log levels/codes that are formatted as
            (level, display text, color).
    """
    def __init__(
        self,
        fmt: str = "{dt} [{code}] {msg}",
        dt_fmt: str = "%m/%d/%YT%I:%M:%S",
        out: Buffer | StrLike = stderr,
        min_level: int = LogLevel.Info,
        codes: list[tuple[int, str, str]] | None = None
    ):
        self.fmt = fmt
        self.dt_fmt = dt_fmt
        self.min_level = min_level

        self.codes = {}
        for code in codes or []:
            self.codes[code[0]] = (code[1], code[2])

        self.__file__ = False
        self.__lock__ = Lock()

        if isinstance(out, StrLike):
            self.out = open(out, "+w", encoding="utf-8")
            self.__file__ = True
        else:
            self.out = out

    def __del__(self):
        if self.__file__:
            self.out.close()
            self.__file__ = False

    def _format_code_(self, level) -> str:
        if (lvl := self.codes.get(level, None)) is not None:
            return Markup.parse(f"[{lvl[1]}]{lvl[0]}")
        elif (lvl := _CODES_.get(level, None)) is not None:
            return Markup.parse(f"[{lvl[1]}]{lvl[0]}")
        return str(level)
        

    def log(self, *msg: str, level: int = LogLevel.Info, sep: str = " "):
        """Log and event given message parts and log level. If the level is less than
        the minimum level then it will not be logged.

        Args:
            *msg (str): All parts of the message. Joined by `sep` which is ` ` by default.
            level (int): The log level of the event. This determines what the log code is.
                `LogLevel.Info`, `LogLevel.Warn`, `LogLevel.Error`. Defaults to `LogLevel.Info`.
            sep (str): The seperator to use between message parts. Defaults to ` `.        
        """
        # Used thread safe locked logger
        if level < self.min_level:
            return

        with self.__lock__:
            code = self._format_code_(level)
            _log = self.fmt.format(
                msg=' '.join(msg),
                code=code,
                dt=datetime.now().strftime(self.dt_fmt)
            ).strip()

            if isinstance(self.out, Buffer) and self.out.isatty():
                self.out.write(f"{_log.strip()}\n")
            else:
                _log = f"{Markup.strip(_log).strip()}\n"
                self.out.write(_log)
