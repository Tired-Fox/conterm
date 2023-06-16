from ctypes import POINTER, Array, byref
from ctypes.wintypes import DWORD, HANDLE, LPDWORD
from typing import TypeAlias
from dataclasses import dataclass

from .console import GetConsoleMode, SetConsoleMode, stdin, stdout
from .structs import INPUT_RECORD, InputRecord
from .signatures import _ReadConsoleInput

class Input: pass

def ReadConsoleInput() -> list[InputRecord] | None:
    # PERF: Done in input manager

    SIZE = 128
    buff = (INPUT_RECORD * SIZE)()
    num_records = DWORD()
    result = _ReadConsoleInput(stdin, buff, SIZE, byref(num_records))

    if result != 0:
        return [InputRecord(record) for record in buff[:num_records.value]]
    else:
        return None

@dataclass
class KeyCode:
    C = 67
