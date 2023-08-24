from __future__ import annotations
from copy import deepcopy
from enum import Enum
import re
from typing import Callable, Literal, TypedDict, Unpack
from conterm.pretty.markup import Markup
from conterm.tui.tree import EventHandler, do_scroll
from conterm.tui.buffer import Buffer, Pixel
from conterm.tui.style import ColorFormat, Style, S, Color
from conterm.tui.util import (
    AlignType,
    CornerType,
    EdgeType,
    HOverflowType,
    Rect,
    SizeType,
    VOverflowType,
    align,
    clamp,
    norm_sizing,
)

ANSI = re.compile(r"\x1b\[[\d;]+m")

class SettingType(TypedDict, total=False):
    border: bool
    border_color: ColorFormat
    border_corners: CornerType | tuple[CornerType, CornerType, CornerType, CornerType]
    border_edges: EdgeType | tuple[EdgeType, EdgeType] | tuple[
        EdgeType, EdgeType, EdgeType, EdgeType
    ]
    text_align: AlignType 
    overflow: HOverflowType | tuple[HOverflowType, VOverflowType]
    align_items: AlignType
    padding: SizeType

class Settings:
    __slots__ = (
        "text_align",
        "overflow",
        "align_items",
        "padding",
        "border",
        "border_color",
        "border_corners",
        "border_edges",
    )

    def __init__(self, **settings: Unpack[SettingType]):
        self.border = settings.get("border", True)
        self.border_color = settings.get("border_color", "yellow")
        self.border_corners = settings.get("border_corners", "single")
        if isinstance(self.border_corners, str):
            self.border_corners = tuple([self.border_corners for _ in range(4)])

        self.border_edges = settings.get("border_edges", "single")
        if isinstance(self.border_edges, str):
            self.border_edges = tuple([self.border_edges for _ in range(4)])
        elif isinstance(self.border_edges, tuple) and len(self.border_edges) == 2:
            self.border_edges = (
                self.border_edges[0],
                self.border_edges[1],
                self.border_edges[0],
                self.border_edges[1],
            )

        self.text_align: AlignType = settings.get("text_align", "start")
        if isinstance(to := settings.get("overflow", ('wrap', 'scroll')), tuple):
            self.overflow = to
        else:
            self.overflow = (to, to)
        if self.overflow[1] == 'wrap':
            self.overflow = (self.overflow[0], 'scroll')

        self.align_items: AlignType = settings.get("align_items", "start")
        self.padding: tuple[int, int, int, int] = norm_sizing(settings.get("padding", 0))

    def copy(self) -> Settings:
        """Copyt the current styles."""
        return deepcopy(self)

    def __repr__(self) -> str:
        values = ", ".join(f'{key}={getattr(self, key)}' for key in Settings.__annotations__.keys())
        return f"{{{values}}}"

class NodeArgs(TypedDict, total=False):
    id: str
    pos: tuple[int | float, int | float | Callable[[int], int]]
    size: tuple[int | float, int | float | Callable[[int], int]]
    title: str
    settings: Settings
    event_handler: EventHandler
    state: dict
    contains: Literal['text', 'list']

class Edges(Enum):
    single = ("─", "│")
    dashed = ("┄", "┆")
    dotted = ("┈", "┊")
    double = ("═", "║")


class Corners(Enum):
    single = ("┌", "┐", "┘", "└")
    double = ("╒", "╓", "╔", "╕", "╖", "╗", "╛", "╜", "╝", "╘", "╙", "╚")
    rounded = ("╭", "╮", "╯", "╰")

    @staticmethod
    def from_edges(corner: str, block: str, inline: str, ci: int = 1):
        """Get the valid corners given the current edges. If the corner is a double
        it will attempt to connect to the sides with singles if appropriate. If the edges
        on both sides are single lines then it will connect to both with double lines.

        Returns:
            top left, top right, bottom right, bottom left corners respectively
        """
        if corner == "double":
            if inline != "double":
                if block == "double":
                    corners = Corners.double.value
                    return corners[3 * (ci) + 0]
                else:
                    corners = Corners.double.value
                    return corners[3 * (ci) + 2]
            else:
                if block == "double":
                    corners = Corners.double.value
                    return corners[3 * (ci) + 2]
                else:
                    corners = Corners.double.value
                    return corners[3 * (ci) + 1]

        return Corners[corner].value[ci]

class Line:
    def __init__(
        self,
        line: str,
        width: int,
        overflow: HOverflowType,
        alignment: AlignType
    ):
        _style = Style()
        previous = 0
        self.pixels = []
        for ansi in ANSI.finditer(line):
            if ansi.start() > previous:
                # add all chars with previous style
                self.pixels.extend(
                    Pixel(c, _style) for c in line[previous : ansi.start()]
                )
            _style = Style.from_ansi(ansi.group(0))
            previous = ansi.start() + len(ansi.group(0))
        if previous < len(line):
            self.pixels.extend(Pixel(c, _style) for c in line[previous:])

        self.normalized = self._normalized_(width, overflow, alignment)
        self.norm_len = len(self.normalized)

    def __len__(self) -> int:
        return len(self.pixels)

    def _normalized_(
        self,
        width: int,
        overflow: HOverflowType,
        alignment: AlignType
    ) -> list[list[Pixel]]:
        text = []
        prev = 0
        for i, pixel in enumerate(self.pixels):
            if pixel.symbol == "\r":
                text.append(self.pixels[prev:i])
                prev= i + 1
        if prev < len(self.pixels):
            text.append(self.pixels[prev:])

        lines = []
        for line in text:
            if overflow == "wrap" and len(line) > width:
                step = width
                times = len(line) // width
                prev = 0
                for i in range(times):
                    lines.append(line[i * step : (i + 1) * step])
                    prev = i * step
                if prev < width:
                    lines.append(
                        align(
                            line[times * step :],
                            width,
                            Pixel("", Style()),
                            alignment,
                        )
                    )
            else:
                lines.append(
                    align(
                        line, width, Pixel("", Style()), alignment
                    )
                )
        return lines

    def __repr__(self) -> str:
        return repr(self.pixels)

class Node:
    def __init__(
        self,
        buffer: Buffer | None = None,
        *_,
        **kwargs: Unpack[NodeArgs],
    ):
        self.id = kwargs.get("id", None)
        self.settings = kwargs.get('settings', Settings())
        self.title = kwargs.get('title', "")

        self.size = kwargs.get('size', (1.0, 1.0))
        self.pos = kwargs.get('pos', (0, 0))

        self.event_handler: EventHandler = kwargs.get('event_handler', do_scroll)
        self.contains: Literal['text', 'list'] = kwargs.get('contains', 'text')
        
        self.state = kwargs.get('state', {}) or {}

        self._BUFFER_ = buffer
        self.focus: Literal['static', 'normal', 'unfocus', 'focus', 'selected'] = "normal"
        if self.settings.overflow[0] != "scroll" and self.settings.overflow[1] != "scroll":
            self.focus = 'static'
        self.text: str = ""
        self.scroll_y = 0
        self.scroll_x = 0

    def push(self, *text: str, sep: str = " "):
        """Write a string of text to the node. If `contains='list'` is set
        every call to `push` will add the text to the previous entry. All new line sequences (`\\n`)
        are preserved.

        Args:
            *text (str): The text that should be displayed. Each entry is seperated by the
                `sep` param.
            sep (str): Seperator that goes between each entry of `text`
        """
        self.text += sep.join(text).replace("\n", "\r")

    def write(self, *text: str, sep: str = " "):
        """Write a string of text to the node. If `contains='list'` is set
        every call to `write` becomes an entry in the selection list. All new line sequences (`\\n`)
        are preserved.

        Args:
            *text (str): The text that should be displayed. Each entry is seperated by the
                `sep` param.
            sep (str): Seperator that goes between each entry of `text`
        """
        self.text += '\n' + sep.join(text).replace("\n", "\r")

    def format(self, *text: str, sep: str = " ", mar: bool = True):
        """Adding a formatted string of text to the node. If `contains='list'` is set
        every call to `format` becomes an entry in the selection list. All new line sequences (`\\n`)
        are preserved.

        Args:
            *text (str): The text that should be displayed. Each entry is seperated by the
                `sep` param.
            markup (bool): Whether to parse the text as a markup string.
            sep (str): Seperator that goes between each entry of `text`
            mar (bool): Markup auto reset (`mar`) toggle. If true every text entry is closed
                with a reset ansi sequence, `\\x1b[0m`.
        """
        self.text += '\n' + Markup.parse(sep.join(text).replace("\n", "\r"), sep=sep, mar=mar)

    def entry(self, index: int) -> str | None:
        """Get a specific entry in the selection list. If `contains='list'` is not set then
        None is returned.
        """
        if self.contains == "list":
            return self.text.split("\n")[index].replace("\r", "\n")
        return None

    def clear(self):
        """Clear the nodes text."""
        self.text = ""

    def scroll_up(self):
        if self.settings.overflow[1] != 'hidden':
            self.scroll_y -= 1

    def scroll_down(self):
        if self.settings.overflow[1] != 'hidden':
            self.scroll_y += 1

    def scroll_left(self):
        if self.settings.overflow[0] == 'scroll':
            self.scroll_x -= 1

    def scroll_right(self):
        if self.settings.overflow[0] == 'scroll':
            self.scroll_x += 1

    def _border_(self, buffer: Buffer):
        """Generate the nodes border pixels."""
        if self.settings.border:
            edges = tuple(
                [Edges[self.settings.border_edges[i]].value[i % 2] for i in range(4)]
            )

            def get_edges(i: int) -> tuple[str, str]:
                # [top, left, bottom, right]
                # 0 => [0, 1]
                # 1 => [0, 3]
                # 2 => [2, 3]
                # 3 => [2, 1]
                result = (0 if i in [0, 1] else 2, 3 if i in [1, 2] else 1)
                return (
                    self.settings.border_edges[result[0]],
                    self.settings.border_edges[result[1]],
                )

            corners = tuple(
                [
                    Corners.from_edges(self.settings.border_corners[i], *get_edges(i), i)
                    for i in range(4)
                ]
            )

            style = Style()
            if self.focus == 'selected':
                style.style |= S.Bold.value
            if self.focus == 'unfocus':
                style.fg = f';3{Color.new(243)}'
                style.style |= S.Bold.value
            elif self.focus == "focus":
                style.fg = f';3{Color.new(self.settings.border_color)}'
            # else:
            #     style.fg = f';3{Color.new(self.style.border_color)}'

            if len(buffer) >= 2:
                rect = self.rect()
                (left, top, right, bottom) = rect.points()
                for row in buffer[top + 1 : bottom]:
                    row[left].set(edges[1], style)
                    row[right - 1].set(edges[3], style)

                for i in range(left, right):
                    if i == left:
                        buffer[top][i].set(corners[0], style)
                    elif i == right - 1:
                        buffer[top][i].set(corners[1], style)
                    else:
                        buffer[top][i].set(edges[0], style)

                if top + rect.height <= buffer.height:
                    for i in range(left, right):
                        if i == left:
                            buffer[bottom - 1][i].set(corners[3], style)
                        elif i == right - 1:
                            buffer[bottom - 1][i].set(corners[2], style)
                        else:
                            buffer[bottom - 1][i].set(edges[2], style)
            self._title_(buffer)

    @property
    def width(self) -> int:
        if self._BUFFER_ is not None:
            return self._BUFFER_.width
        return 0
    @property
    def height(self) -> int:
        if self._BUFFER_ is not None:
            return self._BUFFER_.height
        return 0

    def rect(self) -> Rect:
        """The valid rect the node can write into."""
        return Rect(*self.pos, *self.size, self.width, self.height)

    def _title_(self, buffer: Buffer):
        """Generate the nodes title."""
        r = self.rect()
        (left, top, right, _) = r.points()
        w = r.width
        if (self.settings.border and w < 3) or w < 1 or len(self.title) == 0:
            return

        right = max(0, right - 1)
        left = min(left + 1, right)
        w -= 2

        title = self.title
        if len(title) > w:
            title = title[: w - 1] + "…"
        end = left + len(title)

        for pixel, char in zip(buffer[top][left:end], title):
            pixel.set(char)

    def _to_lines_(self) -> list[list[Pixel]]:
        lines = self.text.split("\n")
        _style = Style()
        text: list[list[Pixel]] = []
        previous = 0
        for line in lines:
            chars = []
            for ansi in ANSI.finditer(line):
                if ansi.start() > previous:
                    # add all chars with previous style
                    chars.extend(
                        Pixel(c, _style) for c in line[previous : ansi.start()]
                    )
                _style = Style.from_ansi(ansi.group(0))
                previous = ansi.start() + len(ansi.group(0))
            if previous < len(line):
                chars.extend(Pixel(c, _style) for c in line[previous:])
            if len(chars) > 0:
                text.append(chars)
        return text

    def _scroll_(self, text: list[Line], rect: Rect, buffer: Buffer) -> list[list[Pixel]]:
        def flatten_norm(lines: list[Line]) -> list[list[Pixel]]:
            result = []
            for line in lines:
                result.extend(line.normalized)
            return result

        if len(text) > rect.height:
            if self.settings.overflow[1] == "scroll":
                buffer[rect.bottom-1][rect.right-1].set('⮟')
                buffer[rect.top][rect.right-1].set('⮝')

        lines = []
        if len(text) == 0:
            return []
        elif self.settings.overflow[1] == 'hidden':
            lines = flatten_norm(text[:rect.height])
        else:
            # if select then bold selected and have padded scrolling
            # else normal scroll
            if self.contains == 'text':
                lines = flatten_norm(text)
                maxv = len(lines) - rect.height - 1
                self.scroll_y = clamp(self.scroll_y, 0, maxv)
                lines = lines[self.scroll_y:]
            elif self.contains == 'list':
                self.scroll_y = clamp(self.scroll_y, 0, len(text) - 1)

                previous = flatten_norm(text[:self.scroll_y])
                _next = flatten_norm(text[self.scroll_y+1:])

                lower = ((rect.height - text[self.scroll_y].norm_len) // 2)
                upper = ((rect.height - text[self.scroll_y].norm_len) - lower)
                lower = len(previous) - lower

                if lower < 0:
                    upper = min(upper - lower, len(_next))
                    lower = 0
                if upper > len(_next):
                    lower = max(0, lower - upper + len(_next))
                    upper = len(_next)

                for char in text[self.scroll_y].pixels:
                    char.style.style |= S.Bold.value
                    if self.focus == "selected":
                        char.style.fg = ";37"

                lines = [*previous[lower:], *text[self.scroll_y].normalized,*_next[:upper]]

        max_line_length = max(len(l) for l in lines) if len(lines) > 0 else 0
        if max_line_length > rect.width:
            if self.settings.overflow[0] == "scroll":
                buffer[rect.bottom][rect.left].set('⮜')
                buffer[rect.bottom][rect.right-1].set('⮞')

        if self.settings.overflow[0] == 'scroll':
            self.scroll_x = clamp(
                self.scroll_x,
                0, 
                max_line_length - rect.width,
            )
            for i in range(len(lines)):
                lines[i] = lines[i][min(len(lines[i]), self.scroll_x):]
        return lines

    def _text_(self, buffer: Buffer):
        rect = self.rect()
        if self.settings.border:
            rect.left += 1
            rect.top += 1
            rect.right -= 1
            rect.bottom -= 1
        (pl, pt, pr, pb) = self.settings.padding
        rect.left += pl
        rect.right -= pr
        rect.top += pt
        rect.bottom -= pb

        text = []
        for line in self.text.strip().split("\n"):
            val = Line(line, rect.width, self.settings.overflow[0], self.settings.text_align)
            if len(val) > 0:
                text.append(val)

        text = self._scroll_(text, rect, buffer)

        if len(text) < rect.height:
            text = align(text, rect.height, [], self.settings.align_items)

        for i, row in enumerate(buffer[rect.top : rect.bottom]):
            line = text[i] if i < len(text) else None
            for j, pixel in enumerate(row[rect.left : rect.right]):
                pixel.set(' ')
                if line != None and j < len(line):
                    char = line[j]
                    pixel.set(char.symbol, char.style)

    def render(self):
        if self._BUFFER_ is not None:
            self._border_(self._BUFFER_)
            self._text_(self._BUFFER_)

    def __len__(self) -> int:
        return len(self.text.split("\n"))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(style={self.settings!r})"
