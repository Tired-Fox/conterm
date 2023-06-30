from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass
from sys import stderr
import sys
from threading import Event, Lock, Thread
from time import sleep
from typing import Literal
from queue import Queue

from conterm.control.ansi.actions import move_to, pos

__all__ = [
    "Icons",
    "TaskManager",
    "Spinner",
    "Progress",
    "Task"
]

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
    CLASSIC = "◜◝◞◟"
    FISH = [">))'>", " >))'>", "  >))'>", "   >))'>", "    >))'>", "   <'((<", "  <'((<", " <'((<"]

class Output:
    def __init__(self) -> None:
        self.lock = Lock()
        self.messages = Queue()

    def write(self, text: str):
        with self.lock:
            self.messages.put(text)

    def flush(self):
        pass

def fileno(file_or_fd):
    fd = getattr(file_or_fd, 'fileno', lambda: file_or_fd)()
    if not isinstance(fd, int):
        raise ValueError("Expected a file (`.fileno()`) or a file descriptor")
    return fd

class TaskManager(Thread):
    def __init__(self, *tasks: Task, clear: bool = False) -> None:
        super().__init__(daemon=True)
        self.__tasks__ = list(tasks)
        self.__lock__ = Lock()
        self.__stop__ = Event()
        self._rate_ = 0.1
        _, self._line_ = pos()
        self.exc = None
        self.clear = clear

        self._out_ = sys.stdout
        sys.stdout = Output()

        self.messages = []

    def run(self):
        try:
            while not self.__stop__.is_set():
                self.__lock__.acquire()

                while sys.stdout.messages.qsize() > 0:
                    self.messages.append(sys.stdout.messages.get())
                move_to(0, self._line_)
                # Got to first line of manager then overwrite
                self._out_.write("\n")
                for task in self.__tasks__:
                    task.update(self._rate_)
                    self._out_.write(f"{task}\n")
                if len(self.messages) > 0:
                    messages = ''.join(self.messages)
                    self._out_.write(f"\n\x1b[1m[stdout]\x1b[22m\n{messages}")
                self._out_.flush()
                self.__lock__.release()
                sleep(self._rate_)
        except KeyboardInterrupt as interrupt:
            self.exc = interrupt
        except Exception as error:
            self.exc = error
        finally:
            if self.__lock__.locked():
                self.__lock__.release()

    def __getitem__(self, key: int) -> Task:
        with self.__lock__:
            return self.__tasks__[key]

    def pop(self, key: int) -> Task:
        with self.__lock__:
            return self.__tasks__.pop(key)

    def add(self, subtask: Task):
        with self.__lock__:
            self.__tasks__.append(subtask)

    def extend(self, subtasks: list[Task]):
        with self.__lock__:
            self.__tasks__.extend(subtasks)

    def remove(self, subtask: Task):
        with self.__lock__:
            self.__tasks__.remove(subtask)

    def __del__(self):
        if self._out_ is not None:
            sys.stdout = self._out_
            self._out_ = None
            sys.stdout.flush()

    def stop(self):
        self.join()

    def join(self):
        self.__stop__.set()
        Thread.join(self)

        # Print final state of tasks
        move_to(0, self._line_)
        # Got to first line of manager then overwrite
        self._out_.write("\n")
        for task in self.__tasks__:
            task.update(self._rate_)
            self._out_.write(f"{task}\n")
        if len(self.messages) > 0:
            messages = ''.join(self.messages)
            self._out_.write(f"\n\x1b[1m[stdout]\x1b[22m\n{messages}\x1b[1m[/stdout]\x1b[22m\n")
        self._out_.flush()

        if self._out_ is not None:
            sys.stdout = self._out_
            self._out_ = None

        if self.exc is not None:
            raise self.exc

class Task:
    def __init__(self, *tasks: str | Task, rate: float = 0.5, target: int = 0, callback: Callable | None = None):
        self._lock_ = Lock()
        self._plock_ = Lock()
        self._count_ = 0
        self._max_ = rate
        self._length_ = 0
        self._tasks_ = []
        self._subtasks_ = []
        self._total_ = 0
        self._target_ = target
        self._callback_ = callback
        self._complete_ = None
        self.extend(*tasks)

    def __getitem__(self, key: int) -> str | Task:
        with self._lock_:
            return self._subtasks_[key]

    def task(self, key: int) -> Task:
        with self._lock_:
            return self._subtasks_[key]

    def pop(self, key: int) -> str | Task:
        with self._lock_:
            return self._subtasks_.pop(key)

    @property
    def complete(self) -> bool:
        if self._target_ == 0:
            if self._complete_ is not None:
                return self._complete_
            return False
        return self._total_ >= self._target_

    @complete.setter
    def complete(self, state: bool):
        if self._target_ == 0:
            self._complete_ = state

    def increment(self, amount: int = 1):
        with self._plock_:
            self._total_ = max(0, min(self._target_, self._total_ + amount))
            if self.complete and self._callback_ is not None:
                self._callback_()
                self._callback_ = None

    def add(self, subtask: str | Task, link: bool = True):
        with self._lock_:
            self._tasks_.append(subtask)
        if isinstance(subtask, Task):
            if link:
                subtask._callback_ = self.increment
            self._subtasks_.append(subtask)

    def extend(self, *subtasks: str | Task, link: bool = True):
        with self._lock_:
            self._tasks_.extend(subtasks)
        for task in subtasks:
            if isinstance(task, Task):
                if link:
                    task._callback_ = self.increment
                self._subtasks_.append(task)

    def remove(self, subtask: str | Task):
        with self._lock_:
            if subtask in self._tasks_:
                self._tasks_.remove(subtask)
            if subtask in self._subtasks_:
                self._subtasks_.remove(subtask)

    def __len__(self) -> int:
        with self._lock_:
            count = 1
            for task in self._tasks_:
                if isinstance(task, str):
                   count += 1 
                else:
                    count += len(task)

        return count

    def __lines__(self) -> list[str]:
        return []

    def update(self, rate: float):
        with self._lock_:
            for task in self._subtasks_:
                if isinstance(task, Task):
                    task.update(rate)

    def __str__(self) -> str:
        return "\n".join(self.__lines__())

class Spinner(Task):
    def __init__(
        self,
        *tasks: str | Task,
        prompt: str,
        icons: str | list[str] = Icons.DOTS,
        rate: float = 0.2,
        format: Literal["p", "s"] = "p",
        target: int = 0
    ):
        super().__init__(*tasks, rate=rate, target=target)
        self._prompt_ = prompt
        self._icons_ = icons
        self._index_ = 0
        self._format_ = format
        self._length_ = len(prompt) + 1
        if isinstance(icons, str):
            self._length_ += 1
        else:
            self._length_ += max(map(len, icons))

        if self._target_ > 0:
            self._length_ += 3 + (len(str(self._target_)) * 2)

    def update(self, rate: float):
        if not self.complete:
            self._count_ += rate
            if self._count_ >= self._max_:
                self._index_ = (self._index_ + 1) % len(self._icons_)
                self._count_ = 0

        super().update(rate)

    def __lines__(self) -> list[str]:
        result = ""
        icon = self._icons_[self._index_] 
        if self.complete:
            result = f"\x1b[32m●\x1b[39m {self._prompt_}"
            if self._target_ != 0:
                result = f"{result} \x1b[32m[{self._total_}/{self._target_}]\x1b[39m"
        elif self._format_ == "p":
            result = f"{icon} {self._prompt_}"
            if self._target_ != 0:
                result = f"{result} [{self._total_}/{self._target_}]"
        elif self._format_ == "s":
            result = f"{self._prompt_} {icon}"
            if self._target_ != 0:
                result = f"[{self._total_}/{self._target_}]"

        result = [result.ljust(self._length_)]
        with self._lock_:
            for task in self._tasks_:
                if isinstance(task, str):
                    result.append(f"    {task}")
                elif isinstance(task, Task):
                    result.extend([f'  {l}' for l in task.__lines__()])
        return result

class Progress(Task):
    FILL = '▏▎▍▌▋▊▉█'

    def __init__(
        self,
        *tasks: str | Task,
        prompt: str,
        target: int,
        width: int = 10,
        format: Literal["arrow", "symbol", "fill"] = "fill",
        symbol: str = '*',
        brackets: bool = True,
        callback: Callable | None = None
    ):
        super().__init__(*tasks, target=target, callback=callback)
        # Progress bar specific data
        self._prompt_ = prompt
        self._brackets_ = ["[", "]"] if brackets else ["", ""]
        self._length_ = len(prompt) + 1 + width + len(''.join(self._brackets_))
        self._symbol_ = symbol
        self._width_ = width
        self._format_ = format

    def __lines__(self) -> list[str]:
        result = ""
        color = '\x1b[32m' if self.complete else ''

        with self._plock_:
            percent = self._total_ / self._target_
            index = self._width_ * percent
            remain = int(len(self.FILL) * (index - int(index))) 
            index = int(index)
            bar = ""

            if self._format_ == "fill":
                bar = self.FILL[-1] * max(0, index)
                if percent != 1:
                    bar += self.FILL[remain]
            elif self._format_ == "arrow":
                bar = '-' * max(0, index)
                if percent != 1:
                    bar += ">"
            elif self._format_ == "symbol":
                bar = self._symbol_ * max(0, index)

            result += f"{self._prompt_} {self._brackets_[0]}{color}{bar.ljust(self._width_)}\x1b[39m{self._brackets_[1]}"

        result = [result.ljust(self._length_)]
        with self._lock_:
            for task in self._tasks_:
                if isinstance(task, str):
                    result.append(f"  {task}")
                elif isinstance(task, Task):
                    result.extend([f'  {l}' for l in task.__lines__()])
        return result
