"""Helper for getting key names and key codes."""
import sys
from typing import ItemsView, KeysView, ValuesView

if sys.platform == "win32":
    from .win import KEYS
elif sys.platform == "linux":
    from .linux import KEYS
else:
    raise ImportError(f"Unsupported platform: {sys.platform}")

modifier_map = {"ctrl": 0, "alt": 1, "shift": 2}

FKeys = {
    "combos": [
        ("SHIFT", 2),
        ("ALT", 3),
        ("ALT_SHIFT", 4),
        ("CTRL", 5),
        ("CTRL_SHIFT", 6),
        ("CTRL_ALT", 7),
        ("CTRL_ALT_SHIFT", 8)
    ],
    "keys": {
        "F1": "\x1b[1;{}P",
        "F2": "\x1b[1;{}Q",
        "F3": "\x1b[1;{}R",
        "F4": "\x1b[1;{}S",
        "F5": "\x1b[15;{}~",
        "F6": "\x1b[17;{}~",
        "F7": "\x1b[18;{}~",
        "F8": "\x1b[19;{}~",
        "F9": "\x1b[20;{}~",
        "F10": "\x1b[21;{}~",
        "F11": "\x1b[23;{}~",
        "F12": "\x1b[24;{}~",
    }
}

class KeyCode:
    """Data structure for all the possible keycodes that are supported."""

    def __init__(self):
        self._keys = {
            # Arrows
            "UP": "\x1b[A",
            "DOWN": "\x1b[B",
            "RIGHT": "\x1b[C",
            "LEFT": "\x1b[D",
            # Shift + Arrows
            "SHIFT_UP": "\x1b[1;2A",
            "SHIFT_DOWN": "\x1b[1;2B",
            "SHIFT_RIGHT": "\x1b[1;2C",
            "SHIFT_LEFT": "\x1b[1;2D",
            # Alt + Arrows
            "ALT_UP": "\x1b[1;3A",
            "ALT_DOWN": "\x1b[1;3B",
            "ALT_RIGHT": "\x1b[1;3C",
            "ALT_LEFT": "\x1b[1;3D",
            # Alt + Arrows
            "CTRL_UP": "\x1b[1;5A",
            "CTRL_DOWN": "\x1b[1;5B",
            "CTRL_RIGHT": "\x1b[1;5C",
            "CTRL_LEFT": "\x1b[1;5D",
            # Ctrl + Alt + Arrows
            "CTRL_ALT_UP": "\x1b[1;7A",
            "CTRL_ALT_DOWN": "\x1b[1;7B",
            "CTRL_ALT_RIGHT": "\x1b[1;7C",
            "CTRL_ALT_LEFT": "\x1b[1;7D",
            # Alt + Shift + Arrow
            "ALT_SHIFT_UP": "\x1b[1;4A",
            "ALT_SHIFT_DOWN": "\x1b[1;4B",
            "ALT_SHIFT_RIGHT": "\x1b[1;4C",
            "ALT_SHIFT_LEFT": "\x1b[1;4D",
            # Ctrl + Shift + Arrow
            "CTRL_SHIFT_UP": "\x1b[1;4A",
            "CTRL_SHIFT_DOWN": "\x1b[1;4B",
            "CTRL_SHIFT_RIGHT": "\x1b[1;4C",
            "CTRL_SHIFT_LEFT": "\x1b[1;4D",
            # Ctrl + Alt + Shift + Arrows
            "CTRL_ALT_SHIFT_UP": "\x1b[1;8A",
            "CTRL_ALT_SHIFT_DOWN": "\x1b[1;8B",
            "CTRL_ALT_SHIFT_RIGHT": "\x1b[1;8C",
            "CTRL_ALT_SHIFT_LEFT": "\x1b[1;8D",
            "BACKSPACE": "\x7f",
            "ESC": "\x1b",
            "END": "\x1b[F",
            "HOME": "\x1b[H",
            "INSERT": "\x1b[2~",
            "DELETE": "\x1b[3~",
            "SHIFT_TAB": "\x1b[Z",
            # The ALT character in key combinations is the same as ESC
            "ALT": "\x1b",
            "TAB": "\t",
            "ENTER": "\n",
            "RETURN": "\n",
            "PAGEUP": "\x1b[5~",
            "PAGEDOWN": "\x1b[6~",
            # Ctrl + Key :note: This removes the ability to also bind shift
            "CTRL_BACKSPACE": "\x08",
            "CTRL_SPACE": "\x00",
            "CTRL_A": "\x01",
            "CTRL_B": "\x02",
            "CTRL_C": "\x03",
            "CTRL_D": "\x04",
            "CTRL_E": "\x05",
            "CTRL_F": "\x06",
            "CTRL_G": "\x07",
            "CTRL_H": "\x08",
            "CTRL_I": "\t",
            "CTRL_J": "\n",
            "CTRL_K": "\x0b",
            "CTRL_L": "\x0c",
            "CTRL_M": "\r",
            "CTRL_N": "\x0e",
            "CTRL_O": "\x0f",
            "CTRL_P": "\x10",
            "CTRL_Q": "\x11",
            "CTRL_R": "\x12",
            "CTRL_S": "\x13",
            "CTRL_T": "\x14",
            "CTRL_U": "\x15",
            "CTRL_V": "\x16",
            "CTRL_W": "\x17",
            "CTRL_X": "\x18",
            "CTRL_Y": "\x19",
            "CTRL_Z": "\x1a",
            "F1": "\x1bOP",
            "F2": "\x1bOQ",
            "F3": "\x1bOR",
            "F4": "\x1bOS",
            "F5": "\x1b[15~",
            "F6": "\x1b[17~",
            "F7": "\x1b[18~",
            "F8": "\x1b[19~",
            "F9": "\x1b[20~",
            "F10": "\x1b[21~",
            "F11": "\x1b[23~",
            "F12": "\x1b[24~",
            **{
                f'{prefix}_{key}': value.format(index)
                for key, value in FKeys['keys'].items()
                for prefix, index in FKeys['combos']
            },
            **KEYS,
        }

    def __getattr__(self, key) -> str:
        return self._keys.get(key, "")

    def __contains__(self, key: str) -> bool:
        return key in self.values()

    def by_code(self, code: str, default: str | None = None) -> str | None:
        """Get the key name from the key code."""
        for name, value in self._keys.items():
            if code == value:
                return name
        return default

    def by_chord(self, chord: str, default: str | None = None) -> str | None:
        """Get the key code given the key chord.

        Example:
            - `ctrl+enter`: `\\n`
            - `ctrl+alt+d`: `\\x1b\\x04`
        """
        parts = chord.split("+")
        parts.sort(key=lambda p: modifier_map.get(p, len(p) + 10))

        name = "_".join(parts).upper()
        if (key := self._keys.get(name)) is not None:
            return key

        ctrl = "ctrl" in chord.lower()
        alt = "\x1b" if "alt" in chord.lower() else ""
        shift = "shift" in chord.lower()
        key = parts[-1].upper() if shift else parts[-1]

        if ctrl and (key := self._keys.get(f"CTRL_{key.upper()}")) is not None:
            return f"{alt}{key}"
        if key == " ":
            return " "
        if key.isalpha():
            return f"{alt}{key}"

        return default

    def values(self) -> ValuesView[str]:
        """List of all key codes."""
        return self._keys.values()

    def keys(self) -> KeysView[str]:
        """List of all key names."""
        return self._keys.keys()

    def items(self) -> ItemsView[str, str]:
        """List of key name to key code pairs."""
        return self._keys.items()


keys = KeyCode()
