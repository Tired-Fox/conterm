from typing import Literal

from conterm.pretty.markup.color_consts import NamedColor

class Color:
    type: Literal["rgb", "hex", "xterm", "named"]
    value: int = -1
    r: int = -1
    g: int = -1
    b: int = -1

    def __init__(self, color: str) -> None:
        if color.startswith("#"):
            color = color.lstrip("#")
            if len(color) not in [3, 6]:
                raise ValueError(f"Expected hex value to have 3 to 6 digits: {len(color)} found")
            if len(color) == 3:
                color = f"{color[0]*2}{color[1]*2}{color[2]*2}"
            self.type = "hex"
            self.r = int(color[:2], 16)
            self.g = int(color[2:4], 16)
            self.b = int(color[4:6], 16)
        elif "," in color:
            self.type = "rgb"
            color = color.split(",")
            if len(color) < 3:
                raise ValueError(f"Expected rgb color to have 3 values: {len(color)} found")
            self.r = int(color[0])
            self.g = int(color[1])
            self.b = int(color[2])
        else:
            try:
                self.value = int(color)
                self.type = "xterm"
            except Exception as error:
                named = NamedColor.get(color.lower())
                if named is None:
                    raise ValueError(f"Invalid named color: {color}") from error

                self.r = named[1][0]
                self.g = named[1][1]
                self.b = named[1][2]
                self.type = "named"

    def __color__(self, code) -> str:
        if self.type == "xterm":
            return f"{code}8;5;{self.value}"
        if self.type in ["rgb", "hex", "named"]:
            return f"{code}8;2;{self.r};{self.g};{self.b}"
        return ""

    def fg(self) -> str:
        return self.__color__(3)

    def bg(self) -> str:
        return self.__color__(4)

if __name__ == "__main__":
    print(f"\x1b[{Color('#f43').fg()}mColored Text\x1b[0m")
