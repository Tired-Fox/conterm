"""
Mini module for creating tui applications. This library is fairly simple.
If more complex features are desired please see other Tui libraries.
"""
from __future__ import annotations

from copy import deepcopy
from enum import Enum
from random import randrange
import re
from time import sleep
from typing import Literal, TypedDict, Unpack
from conterm.pretty.markup import Markup

from conterm.tui.buffer import Buffer, Pixel
from conterm.tui.style import ColorFormat, Style as _AnsiStyle, Color


class Edges(Enum):
    single = ('─', '│')
    dashed = ('┄', '┆')
    dotted = ('┈', '┊')
    double = ('═', '║')

class Corners(Enum):
    single = ('┌', '┐', '┘', '└')
    double = ('╒', '╓', '╔', '╕', '╖', '╗', '╛', '╜', '╝', '╘', '╙', '╚')
    rounded = ('╭', '╮', '╯', '╰')

    @staticmethod
    def from_edges(corner: str, block: str, inline: str, ci: int = 1):
        """Get the valid corners given the current edges. If the corner is a double
        it will attempt to connect to the sides with singles if appropriate. If the edges
        on both sides are single lines then it will connect to both with double lines.

        Returns:
            top left, top right, bottom right, bottom left corners respectively
        """
        if corner == 'double':
            if inline != 'double':
                if block == 'double':
                    corners = Corners.double.value
                    return corners[3*(ci) + 0]
                else:
                    corners = Corners.double.value
                    return corners[3*(ci) + 2]
            else:
                if block == 'double':
                    corners = Corners.double.value
                    return corners[3*(ci) + 2]
                else:
                    corners = Corners.double.value
                    return corners[3*(ci) + 1]

        return Corners[corner].value[ci]


SingleDouble = Literal['single', 'double']
CornerType = Literal['single', 'double', 'rounded']
EdgeType = Literal['single', 'dashed', 'dotted', 'double']

class Styles(TypedDict, total=False):
    border: bool 
    border_color: ColorFormat
    border_corners: CornerType | tuple[CornerType, CornerType, CornerType, CornerType]
    border_edges: EdgeType | tuple[EdgeType, EdgeType] | tuple[EdgeType, EdgeType, EdgeType, EdgeType]
    text_align: Literal['center', 'start', 'end']
    text_overflow: Literal['wrap', 'hidden', 'scroll']
    align_items: Literal['center', 'start', 'end']
    padding: int | tuple[int, int] | tuple[int, int, int, int]
    margin: int | tuple[int, int] | tuple[int, int, int, int]

class Style:
    __slots__ = (
        "text_align",
        "text_overflow",

        "align_items",
        "padding",
        "margin",

        "border",
        "border_color",
        "border_corners",
        "border_edges",
    )

    def __init__(self, **styles: Unpack[Styles]):
        self.border = styles.get("border", False)
        self.border_color = styles.get("border_color", "white")
        self.border_corners = styles.get("border_corners", "single")
        if isinstance(self.border_corners, str):
            self.border_corners = tuple([self.border_corners for _ in range(4)])

        self.border_edges = styles.get("border_edges", "single")
        if isinstance(self.border_edges, str):
            self.border_edges = tuple([self.border_edges for _ in range(4)])
        elif isinstance(self.border_edges, tuple) and len(self.border_edges) == 2:
            self.border_edges = (
                self.border_edges[0],
                self.border_edges[1],
                self.border_edges[0],
                self.border_edges[1],
            )

        self.text_align = styles.get('text_align', "start")
        self.text_overflow = styles.get("text_overflow", "wrap")

        self.align_items = styles.get('align_items', "start")
        self.padding = styles.get("padding", 0)
        self.margin = styles.get("margin", 0)

    def copy(self) -> Style:
        """Copyt the current styles."""
        return deepcopy(self)

    def __repr__(self) -> str:
        border = (
            "border=False"
            if not self.border
            else f"border=True, border-color={self.border_color}"
        )
        return f"{{{border}, text-align={self.text_align}, align-items={self.align_items}}}"

def calc_perc(val: int | float, total: int) -> int:
    if isinstance(val, float):
        return int(total * val)
    return val

ANSI = re.compile(r"\x1b\[[\d;]+m")

class Rect:
    __slots__ = ("left", "right", "top", "bottom")
    def __init__(self, x: int | float, y: int | float, w: int | float, h: int | float, buffer: Buffer):
        self.left = min(calc_perc(x, buffer.width), buffer.width - 1)
        self.right = min(self.left + calc_perc(w, buffer.width), buffer.width)
        self.top = min(calc_perc(y, buffer.height), buffer.height - 1)
        self.bottom = min(self.top + calc_perc(h, buffer.height), buffer.height) 

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    def points(self) -> tuple[int, int, int, int]:
        """Left, top, right, and bottom points respectively."""
        return (self.left, self.top, self.right, self.bottom)

    def dims(self) -> tuple[int, int]:
        """Width and height respectively."""
        return (self.width, self.height)

def _norm_sizing(sizing: int | tuple[int, int] | tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    """Sizing left, top, right, and bottom respectively.

    Args:
        sizing (int | tuple[int, int] | tuple[int, int, int, int]): tuple of left, top, right and bottom
            int values. Can also be a tuple of inline and block int values that spread to the four respective values. Can finally be a single int value that spreads to all four values.
    """
    if isinstance(sizing, tuple):
        if len(sizing) == 2:
            return (sizing[0], sizing[1], sizing[0], sizing[1])
        elif len(sizing) == 4:
            return sizing
        else:
            raise ValueError(f"Invalid tuple of sizing values. Expected 2 or 4 found {len(sizing)}")
    elif isinstance(sizing, int):
        return tuple([sizing for _ in range(4)])
    else:
        raise ValueError(f"Invalid sizing type; was {type(sizing)}")

class Node:
    def __init__(
        self,
        *,
        pos: tuple[int | float, int | float] = (0, 0),
        size: tuple[int | float, int | float] = (1.0, 1.0),
        title: str = "",
        style: Style,
    ):
        self.style = style
        self.title = title
        self.size = size
        self.pos = pos
        self.text: Markup = Markup()

    def write(self, *text: str, sep: str = ' '):
        """Write a string of text to the node.

        Args:
            *text (str): The text that should be displayed. Each entry is seperated by the
                `sep` param.
            markup (bool): Whether to parse the text as a markup string.
            sep (str): Seperator that goes between each entry of `text`
            mar (bool): Markup auto reset (`mar`) toggle. If true every text entry is closed
                with a reset ansi sequence, `\\x1b[0m`.
        """
        if len(text) > 0:
            self.text.feed(text[0], mar=True)
            for t in text[1:]:
                self.text.feed(t, sep=sep, mar=True)

    def format(self, *text: str, sep: str = ' '):
        """Adding a formatted string of text to the node.

        Args:
            *text (str): The text that should be displayed. Each entry is seperated by the
                `sep` param.
            markup (bool): Whether to parse the text as a markup string.
            sep (str): Seperator that goes between each entry of `text`
            mar (bool): Markup auto reset (`mar`) toggle. If true every text entry is closed
                with a reset ansi sequence, `\\x1b[0m`.
        """
        if len(text) > 0:
            self.text.feed(text[0], mar=False)
            for t in text[1:]:
                self.text.feed(t, sep=sep, mar=False)

    def push(self, *text: str, sep: str = ' '):
        """Adding a plain string of text to the node.

        Args:
            *text (str): The text that should be displayed. Each entry is seperated by the
                `sep` param.
            markup (bool): Whether to parse the text as a markup string.
            sep (str): Seperator that goes between each entry of `text`
            mar (bool): Markup auto reset (`mar`) toggle. If true every text entry is closed
                with a reset ansi sequence, `\\x1b[0m`.
        """
        if len(text) > 0:
            self.text.markup += sep.join(text)

    def clear(self):
        """Clear the nodes text."""
        self.text.clear()

    def _border_(self, buffer: Buffer):
        """Generate the nodes border pixels."""
        if self.style.border:
            edges = tuple([
                Edges[self.style.border_edges[i]].value[i%2]
                for i in range(4) 
            ])
            def get_edges(i: int) -> tuple[str, str]:

                # [top, left, bottom, right]
                # 0 => [0, 1]
                # 1 => [0, 3]
                # 2 => [2, 3]
                # 3 => [2, 1]
                result = (
                    0 if i in [0, 1] else 2,
                    3 if i in [1, 2] else 1
                ) 
                return (
                    self.style.border_edges[result[0]],
                    self.style.border_edges[result[1]]
                )

            corners = tuple([
                Corners.from_edges(
                    self.style.border_corners[i],
                    *get_edges(i),
                    i
                )
                for i in range(4)
            ])


            style = _AnsiStyle(fg=Color.new(self.style.border_color))
            if len(buffer) >= 2:
                (left, top, right, bottom) = self.valid_rect(buffer).points()
                for row in buffer[top+1:bottom]:
                    row[left].set(edges[1], style)
                    row[right - 1].set(edges[3], style)

                for i in range(left, right):
                    if i == left:
                        buffer[top][i].set(corners[0], style)
                    elif i == right - 1:
                        buffer[top][i].set(corners[1], style)
                    else:
                        buffer[top][i].set(edges[0], style)

                if top + self.size[1] < buffer.height:
                    for i in range(left, right):
                        if i == left:
                            buffer[bottom - 1][i].set(corners[3], style)
                        elif i == right - 1:
                            buffer[bottom - 1][i].set(corners[2], style)
                        else:
                            buffer[bottom - 1][i].set(edges[2], style)
            self._title_(buffer)

    def valid_rect(self, buffer: Buffer) -> Rect:
        """The valid rect the node can write into."""
        return Rect(*self.pos, *self.size, buffer)

    def _title_(self, buffer: Buffer):
        """Generate the nodes title."""
        r = self.valid_rect(buffer)
        (left, top, right, _) = r.points()
        w = r.width
        if (self.style.border and w < 5) or w < 3 or len(self.title) == 0: 
            return

        right = max(0, right - 1)
        left = min(left + 1, right)
        w -= 2

        title = self.title
        if len(title) > w:
            title = title[:w-3] + "..."
        end = left + len(title)

        for pixel, char in zip(buffer[top][left:end], title):
            pixel.set(char)

    def _align_(self, collection: list[Pixel], size: int, fill, alignment):
        if alignment == 'center':
            remainder = size - len(collection)
            half = remainder // 2
            result = [fill for _ in range(half)]
            result.extend(collection)
            result.extend(fill for _ in range(remainder - half))
            return result
        elif alignment == 'end':
            return [*[fill for _ in range(size - len(collection))], *collection]
        return collection

    def _to_pixels_(self) -> list[list[Pixel]]:
        lines = str(self.text).split("\n")
        _style = _AnsiStyle()
        text: list[list[Pixel]] = []
        previous = 0
        for line in lines:
            text.append([])
            for ansi in ANSI.finditer(line):
                if ansi.start() > previous:
                    # add all chars with previous style
                    text[-1].extend(Pixel(c, _style) for c in line[previous:ansi.start()])
                _style = _AnsiStyle.from_ansi(ansi.group(0))
                previous = ansi.start() + len(ansi.group(0))
            if previous < len(line):
                text[-1].extend(Pixel(c, _style) for c in line[previous:])
        return text

    def _normalize_pixels_(self, text: list[list[Pixel]], rect: Rect) -> list[list[Pixel]]:
        lines = []
        for line in text:
            if self.style.text_overflow == 'wrap' and len(line) > rect.width:
                step = rect.width
                times = len(line) // rect.width
                prev = 0
                for i in range(times):
                    lines.append(line[i*step:(i+1)*step])
                    prev = i*step
                if prev < rect.width:
                    lines.append(self._align_(line[times*step:], rect.width, Pixel('', _AnsiStyle()), self.style.text_align))
            else:
                lines.append(self._align_(line, rect.width, Pixel('', _AnsiStyle()), self.style.text_align))

        if len(lines) < rect.height:
            lines = self._align_(lines, rect.height, [], self.style.align_items)
        return lines


    def _text_(self, buffer: Buffer):
        rect = self.valid_rect(buffer)
        (pl, pt, pr, pb) = _norm_sizing(self.style.padding)
        if self.style.border:
            rect.left += 1
            rect.top += 1
            rect.right -= 1
            rect.bottom -= 1
        rect.left += pl
        rect.right += pr
        rect.top += pt
        rect.bottom += pb

        text = self._to_pixels_()
        text = self._normalize_pixels_(text, rect)

        for line, row in zip(text, buffer[rect.top:rect.bottom]):
            for char, pixel in zip(line, row[rect.left:rect.right]):
                pixel.set(char.symbol, char.style)

    def render(self, buffer: Buffer):
        # 0, 0, w, h
        self._border_(buffer) 
        self._text_(buffer)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(style={self.style!r})"


def __over_time__():
    buffer = Buffer()

    style = Style(
        border=True,
        border_color="cyan",
        text_align='end',
        align_items='end'
    )
    node = Node(pos=(.25, .25), size=(.5, .5), style=style)

    message = ["[red]H", "e", "l", "l", "o", ",", " ", "[green]W", "o", "r", "l", "d", "[/]!"]
    title = "Hello, World!"

    for i in range(len(title)):
        # Add char to title
        node.title += title[i]
        # Fill not yet written characters with whitespace to keep constant placement
        node.clear()
        node.format(''.join(message[:i+1]) + (" " * (12 - i)))

        # Choose random xterm color
        node.style.border_color = randrange(0, 256)

        # Render the node into the buffer
        node.render(buffer)

        # Write the buffer to stdout
        buffer.write()
        sleep(.25)

def __standard__():
    buffer = Buffer()

    style = Style(border=True, border_color="cyan", text_align='center', align_items='center')
    node = Node(size=(1.0, 1.0), style=style, title="Test Node")
    node.write("[red]Hello, [green]world[/]!")
    node.render(buffer)
    buffer.write()

def __multiple__():
    buffer = Buffer()

    style1 = Style(
        border=True,
        border_color="cyan",
        # top, left, bottom, right
        border_edges=('dashed', 'dotted', "single", "single"),
        # tl, tr, br, bl
        border_corners=('single', 'rounded', 'single', 'rounded'),
        text_align='center',
        align_items='center'
    )

    style2 = style1.copy()
    style2.border_color = "yellow"
    style2.border_edges=('dashed', 'dotted', "double", "single")
    style2.border_corners=('single', 'rounded', 'double', 'double')

    style3 = style2.copy()
    style3.border_color = "green"

    node1 = Node(size=(.50, .25), style=style1, title="Node 1")
    node2 = Node(pos=(.50, 0), size=(.50, 1.0), style=style2, title="Node 2")
    node3 = Node(pos=(0, .25), size=(.50, .75), style=style3, title="Node 3")
    nodes = [node1, node2, node3]
    for node in nodes:
        node.render(buffer)
    buffer.write()

if __name__ == "__main__":
    __over_time__()
    input()
    __standard__()
    input()
    __multiple__()
    input()
