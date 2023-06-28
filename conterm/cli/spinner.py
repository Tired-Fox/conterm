from __future__ import annotations

from dataclasses import dataclass
from queue import Queue
from sys import stdout
from threading import Event, Thread
from time import sleep
from typing import Literal

from conterm.control.ansi.actions import (down, move_to, pos, restore_pos,
                                          save_pos)

ACTIVE = False

@dataclass
class Icons:
    """Predefined loading spinner icons."""
    DOTS = '⣾⣽⣻⢿⡿⣟⣯⣷'
    BOUNCE = '⠁⠂⠄⡀⢀⠠⠐⠈'
    VERTICAL = '▁▂▃▄▅▆▇█▇▆▅▄▃▁'
    HORIZONTAL = '▉▊▋▌▍▎▏▎▍▌▋▊▉'
    ARROW = '←↖↑↗→↘↓↙'
    BOX = '▖▘▝▗'
    CROSS = '┤┘┴└├┌┬┐'
    ELLIPSE = ['.', '..', '...']
    EXPLODE = '.oO@*'
    DIAMOND = '◇◈◆'
    STACK = "⡀⡁⡂⡃⡄⡅⡆⡇⡈⡉⡊⡋⡌⡍⡎⡏⡐⡑⡒⡓⡔⡕⡖⡗⡘⡙⡚⡛⡜⡝⡞⡟⡠⡡⡢⡣⡤⡥⡦⡧⡨⡩⡪⡫⡬⡭⡮⡯⡰⡱⡲⡳⡴⡵⡶⡷⡸⡹⡺⡻⡼⡽⡾⡿⢀⢁⢂⢃⢄⢅⢆⢇⢈⢉⢊⢋⢌⢍⢎⢏⢐⢑⢒⢓⢔⢕⢖⢗⢘⢙⢚⢛⢜⢝⢞⢟⢠⢡⢢⢣⢤⢥⢦⢧⢨⢩⢪⢫⢬⢭⢮⢯⢰⢱⢲⢳⢴⢵⢶⢷⢸⢹⢺⢻⢼⢽⢾⢿⣀⣁⣂⣃⣄⣅⣆⣇⣈⣉⣊⣋⣌⣍⣎⣏⣐⣑⣒⣓⣔⣕⣖⣗⣘⣙⣚⣛⣜⣝⣞⣟⣠⣡⣢⣣⣤⣥⣦⣧⣨⣩⣪⣫⣬⣭⣮⣯⣰⣱⣲⣳⣴⣵⣶⣷⣸⣹⣺⣻⣼⣽⣾⣿" 
    TRIANGLE = "◢◣◤◥"
    SQUARE = "◰◳◲◱"
    QUARTER_CIRCLE = "◴◷◶◵"
    HALF_CIRCLE = "◐◓◑◒"
    CORNER = "◜◝◞◟"
    FISH = [">))'>", " >))'>", "  >))'>", "   >))'>", "    >))'>", "   <'((<", "  <'((<", " <'((<"]

class _Spinner(Thread):
    def __init__(
        self,
        icons: list[str] | str = Icons.DOTS,
        prompt: str = "",
        rate: float = 1,
        total: int | None = None,
        format: Literal["prefix", "suffix"] = "prefix",
        *args,
        **kwargs
    ):
        global ACTIVE

        if ACTIVE:
            raise ValueError("Spinner is already running: cannot have more than one spinner at a time.")

        super().__init__(*args, **kwargs, daemon=True)
        self._icons_ = icons
        self._rate_ = rate
        self._prompt_ = prompt
        self._total_ = total
        self._queue_ = Queue()
        self._print_ = Queue()
        self._stop_ = Event()
        self._index_ = 0

        if isinstance(icons, str):
            self._longest_ = 1
        else:
            self._longest_ = max(map(len, icons))

        self._format_ = format
        self.exc = None

        _, y = pos()
        self._line_ = y
        ACTIVE = True

    def add(self, amount: int = 1):
        """Add a number to the progress."""
        if self._total_ is None:
            raise ValueError("Current spinner is not a progress spinner.")
        self._queue_.put(amount)

    def print(self, *text: str):
        """Print to stdout while the spinner is running."""
        self._print_.put(text)

    def write(self):
        if self._format_ == "prefix":
            stdout.write(f"{self._icons_[self._index_]} {self._prompt_}".ljust(self._longest_))
            stdout.flush()
        else:
            stdout.write(f"{self._prompt_} {self._icons_[self._index_]}".ljust(self._longest_))
            stdout.flush()

        restore_pos()

    def to_start(self):
        # Delete the prevous loading line
        save_pos()
        move_to(0, self._line_)

    def run(self):
        total = 0
        down()

        try:
            while not self._stop_.is_set():
                # If progress spinner then add totals if there are any
                if self._total_ is not None:
                    while self._queue_.qsize() > 0:
                        total += self._queue_.get()

                # Get next loading icon
                self._index_ = (self._index_ + 1) % len(self._icons_)

                # Display new line
                self.to_start() 
                self.write()
                while self._print_.qsize() > 0:
                    print(*self._print_.get())
                sleep(self._rate_)
        except KeyboardInterrupt as error:
            self.exc = error
        except Exception as error:
            self.exc = error

    def stop(self):
        self._stop_.set()
        self.join()

    def join(self):
        global ACTIVE

        Thread.join(self)
        ACTIVE = False
        if self.exc is not None:
            raise self.exc

def spinner(
    prompt: str,
    rate: float = 1,
    total: int | None = None,
    icons: list[str] | str = Icons.DOTS,
    format: Literal["prefix", "suffix"] = "prefix" 
) -> _Spinner:
    return _Spinner(icons=icons, rate=rate, prompt=prompt, total=total, format=format)

@dataclass
class Spinner:
    """Collection of predefined loading spinners."""

    @staticmethod
    def ellipse(
        prompt: str,
        rate: float = 0.65,
        total: int | None = None,
        format: Literal["prefix", "suffix"] = "prefix"
    ):
        """"""
        return _Spinner(icons=Icons.ELLIPSE, rate=rate, prompt=prompt, total=total, format=format)

    @staticmethod
    def dots(
        prompt: str,
        rate: float = 0.15,
        total: int | None = None,
    ):
        return _Spinner(icons=Icons.DOTS, rate=rate, prompt=prompt, total=total)

    @staticmethod
    def bounce(
        prompt: str,
        rate: float = 0.15,
        total: int | None = None,
    ):
        return _Spinner(icons=Icons.BOUNCE, rate=rate, prompt=prompt, total=total)


    @staticmethod
    def cross(
        prompt: str,
        rate: float = 0.15,
        total: int | None = None,
    ):
        return _Spinner(icons=Icons.CROSS, rate=rate, prompt=prompt, total=total)

    @staticmethod
    def vertical(
        prompt: str,
        rate: float = 0.15,
        total: int | None = None,
    ):
        return _Spinner(icons=Icons.VERTICAL, rate=rate, prompt=prompt, total=total)

    @staticmethod
    def horizontal(
        prompt: str,
        rate: float = 0.15,
        total: int | None = None,
    ):
        return _Spinner(icons=Icons.HORIZONTAL, rate=rate, prompt=prompt, total=total)

    @staticmethod
    def arrow(
        prompt: str,
        rate: float = 0.15,
        total: int | None = None,
    ):
        return _Spinner(icons=Icons.ARROW, rate=rate, prompt=prompt, total=total)

    @staticmethod
    def box(
        prompt: str,
        rate: float = 0.25,
        total: int | None = None,
    ):
        return _Spinner(icons=Icons.BOX, rate=rate, prompt=prompt, total=total)

    @staticmethod
    def explode(
        prompt: str,
        rate: float = 0.25,
        total: int | None = None,
    ):
        return _Spinner(icons=Icons.EXPLODE, rate=rate, prompt=prompt, total=total)

    @staticmethod
    def diamond(
        prompt: str,
        rate: float = 0.5,
        total: int | None = None,
    ):
        return _Spinner(icons=Icons.DIAMOND, rate=rate, prompt=prompt, total=total)

    @staticmethod
    def stack(
        prompt: str,
        rate: float = 0.25,
        total: int | None = None,
    ):
        return _Spinner(icons=Icons.STACK, rate=rate, prompt=prompt, total=total)

    @staticmethod
    def triangle(
        prompt: str,
        rate: float = 0.25,
        total: int | None = None,
    ):
        return _Spinner(icons=Icons.TRIANGLE, rate=rate, prompt=prompt, total=total)

    @staticmethod
    def square(
        prompt: str,
        rate: float = 0.25,
        total: int | None = None,
    ):
        return _Spinner(icons=Icons.SQUARE, rate=rate, prompt=prompt, total=total)

    @staticmethod
    def quarter_circle(
        prompt: str,
        rate: float = 0.15,
        total: int | None = None,
    ):
        return _Spinner(icons=Icons.QUARTER_CIRCLE, rate=rate, prompt=prompt, total=total)
    
    @staticmethod
    def half_circle(
        prompt: str,
        rate: float = 0.15,
        total: int | None = None,
    ):
        return _Spinner(icons=Icons.HALF_CIRCLE, rate=rate, prompt=prompt, total=total)

    @staticmethod
    def corner(
        prompt: str,
        rate: float = 0.25,
        total: int | None = None,
    ):
        return _Spinner(icons=Icons.CORNER, rate=rate, prompt=prompt, total=total)

    @staticmethod
    def fish(
        prompt: str,
        rate: float = 0.25,
        total: int | None = None,
    ):
        return _Spinner(icons=Icons.FISH, rate=rate, prompt=prompt, total=total, format="suffix")
