"""Logging Example"""

from time import sleep
from conterm.control.ansi.actions import set_title
from conterm.logging import LogLevel, Logger, log
from pathlib import Path


if __name__ == "__main__":
    set_title("Logging Example")

    log("\x1b[1mDefault formatted message\x1b[22m")
    sleep(0.2)

    # This is the format to use to write to a file
    # with Path(__file__).parent.joinpath("temp.txt").open("+w") as file:
    #     log("\x1b[1mSome message\x1b[22m", out=file)

    sleep(0.2)
    log("\x1b[1mCustom date time format\x1b[22m", level=LogLevel.Warn, dt_fmt="%I:%M:%S")

    logger = Logger(
        # Custom format
        fmt="[{code}] {msg}",
        # Custom date time format: Only use time
        dt_fmt="%I:%M:%S",
        codes=[
            # Override info, warn, and error
            (LogLevel.Info, "▮", "cyan"),
            (LogLevel.Warn, "▮", "yellow"),
            (LogLevel.Error, "▮", "red"),
            # Custom level/code: (level, code text, color)
            # text is not format only the color is applied.
            # color can be any conterm.markup color
            (404, "Not Found", "magenta")
        ],
        # Min allowed level that can be printed. Inclusive.
        # all higher/greater log levels are still logged
        min_level=LogLevel.Warn
    )

    # This log method is thread safe and can be called from anywhere
    logger.log("Custom message format")

    sleep(0.5)
    logger.log("Custom message format, only warnings and up", level=LogLevel.Warn)

    sleep(0.5)
    logger.log("Error log event", level=LogLevel.Error)

    # Custom log event
    logger.log("Custom log level", level=404)

