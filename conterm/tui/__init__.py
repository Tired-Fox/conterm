"""
Mini module for creating tui applications. This library is fairly simple.
If more complex features are desired please see other Tui libraries.
"""
from __future__ import annotations

from copy import deepcopy
from enum import Enum
from queue import Empty, Full, Queue
from random import randrange
from time import sleep
from typing import Callable, Iterable, Literal, TypedDict, Unpack
from conterm.control import Listener
from conterm.control.event import Record
from conterm.pretty.markup import Markup
import re

from conterm.tui.buffer import Buffer, Pixel
from conterm.tui.style import S, ColorFormat, Style as _AnsiStyle, Color

def clamp(value: int, lower, upper) -> int:
    return max(lower, min(value, upper))

def default_handler(context: Context, node: Node, event: Record, _state: dict):
    if event.type == "KEY":
        if event.key == "j" or event.key == "down":
            return (Command.ScrollDown, context)
        elif event.key == "k" or event.key == "up":
            return (Command.ScrollUp, context)
        if event.key == "h" or event.key == "left":
            return (Command.ScrollLeft, context)
        elif event.key == "l" or event.key == "right":
            return (Command.ScrollRight, context)

class ApplicationBuilder:
    def __init__(self, app: Application) -> None:
        self._application_ = app

    def new(
        self,
        pos: tuple[int | float, int | float] | None = None,
        size: tuple[int | float, int | float] | None = None,
        title: str | None = None,
        style: Style | None = None,
        event_handler: EventHandler | None = None,
        state: dict | None = None,
    ) -> Context:
        params = {
            'pos': pos,
            'size': size,
            'title': title,
            'style': style,
            'event_handler': event_handler,
            'state': state
        }
        params = {key: value for key, value in params.items() if value is not None}
        self._application_._CHILDREN_.append(Context(Node(**params)))
        return self._application_._CHILDREN_[-1]

    def add(self, node: Node):
        self._application_._CHILDREN_.append(Context(node))

    def extend(self, nodes: Iterable[Node]):
        self._application_._CHILDREN_.extend(Context(node) for node in nodes)

    def set_current(self, new: Context | ContextBuilder) -> Context | None:
        if isinstance(new, ContextBuilder):
            self._application_.set_current(new._context_)
        else:
            self._application_.set_current(new)

def default_global_handler(context, node, record: Record, state: dict) -> tuple:
    if record.type == "KEY":
        key = record.key
        if key == "q" or key == "Q":
            return (Command.Quit, context)
        elif key == "backspace":
            return (Command.Deselect, context)
    return (Command.NOOP, None)

class Application:
    _CHILDREN_: list[Context]
    _CURRENT_: Context | None

    def __init__(self, global_handler: EventHandler = default_global_handler, *children: Context) -> None:
        self.event_bus = Queue()
        self.buffer = Buffer()
        self._CHILDREN_ = list(children)
        self._CURRENT_ = self._CHILDREN_[0] if len(self._CHILDREN_) > 0 else None
        self._global_handler_ = global_handler

    def __enter__(self) -> ApplicationBuilder:
        return ApplicationBuilder(self)

    def __exit__(self, _et, ev, _etb): 
        if ev is None:
            self.run()
        else:
            raise ev

    @property
    def current(self) -> Context | None:
        return self._CURRENT_

    def set_current(self, new: Context) -> Context | None:
        self._CURRENT_ = new
        self._CURRENT_.node.focus = 'selected'

    def app_handler(self, record: Record):
        if record.type == "KEY":
            key = record.key
            if key == "tab":
                prv = self._CHILDREN_[self.focus]
                prv.node.focus = "unfocus"
                self.event(Command.Updated, prv)
                log.write(f"{prv.node.focus}: {self.focus} to ")

                self.focus = (self.focus + 1) % len(self._CHILDREN_)
                nxt = self._CHILDREN_[self.focus]
                nxt.node.focus = "focus"
                log.write(f"{self._CHILDREN_[self.focus].node.focus}: {self.focus}\n")
                log.flush()
                return (Command.Updated, nxt)
            elif key == "shift+tab":
                log.write(f"{self.focus} to {(self.focus + 1) % len(self._CHILDREN_)} with ")
                self._CHILDREN_[self.focus].node.focus = "unfocus"
                self.event(Command.Updated, self._CHILDREN_[self.focus])
                self.focus = (self.focus - 1) % len(self._CHILDREN_)
                self._CHILDREN_[self.focus].node.focus = "focus"
                log.write(f"{self._CHILDREN_[self.focus].node.focus}\n")
                log.flush()
                return (Command.Updated, self._CHILDREN_[self.focus])
            elif key == "enter":
                log.write(f"selected {self.focus}\n")
                log.flush()
                self._CHILDREN_[self.focus].node.focus = "selected"
                self._CURRENT_ = self._CHILDREN_[self.focus]
                return (Command.Updated, self._CHILDREN_[self.focus])

    def handler(self, record: Record, _: dict) -> bool:
        if self.current is None:
            data = self.app_handler(record)
        elif self.current.node.event_handler is None:
            data = default_handler(self.current, self.current.node, record, self.current.node.state)
        else:
            data = self.current.node.event_handler(
                    self.current,
                    self.current.node,
                    record,
                    self.current.node.state
            )

        if data is None:
            current = self.current or Context(Node())
            node = current.node if current is not None else None
            state = node.state if node is not None else None
            data = self._global_handler_(
                current,
                node,
                record,
                state 
            )

        if data is None:
            return True
        else:
            command, node = data

        try:
            self.event_bus.put((command, node), block=False)
            if command == Command.Quit:
                # Stop key event listener
                return False
        except Full: pass

        return True

    def event(self, command: Command, context: Context | None = None):
        try:
            self.event_bus.put((command, context), block=False)
        except Full:
            pass

    def _handle_command_(self):
        while True:
            try:
                command, context = self.event_bus.get(block=False)
                if command == Command.Updated:
                    context.node.render()
                    self.buffer.write()
                elif command == Command.ScrollUp:
                    context.node.scroll_up()
                    context.node.render()
                    self.buffer.write()
                elif command == Command.ScrollDown:
                    context.node.scroll_down()
                    context.node.render()
                    self.buffer.write()
                elif command == Command.ScrollLeft:
                    context.node.scroll_left()
                    context.node.render()
                    self.buffer.write()
                elif command == Command.ScrollRight:
                    context.node.scroll_right()
                    context.node.render()
                    self.buffer.write()
                elif command == Command.Deselect:
                    # PERF: Make this pert parent object so it works with nesting
                    context.node.focus = "focus"
                    context.node.render()
                    self._CURRENT_ = context.parent
                    if self._CURRENT_ is None:
                        self.render()
                    else:
                        self._CURRENT_.render()
                        self.buffer.write()
                elif command == Command.Quit:
                    # Terminal reset codes goes here
                    return
            except Empty:
                pass

    def layout(self):
        pass
    
    def init(self):
        self.layout()
        for context in self._CHILDREN_:
            context.init(self.buffer)

        if self._CURRENT_ is None and len(self._CHILDREN_) > 0:
            self._CHILDREN_[0].node.focus = 'focus'
            self._CHILDREN_[0].node.render()
            self.focus = 0

    def render(self):
        for child in self._CHILDREN_:
            child.render()
        self.buffer.write()

    def run(self):
        self.init()
        self.render()
        with Listener(
            on_event=self.handler,
            on_interrupt=lambda: self.event_bus.put((Command.Quit, None), block=False),
        ) as listener:
            self._handle_command_()
            listener.join()

    
class Context:
    _NODE_: Node
    _PARENT_: Application | Context | None
    _CHILDREN_: list[Context]

    def __init__(self, node: Node, *children: Context) -> None:
       self._NODE_ = node
       self._PARENT_ = None
       self._CHILDREN_ = list(children)
       for child in self._CHILDREN_:
           child._PARENT_ = self

    def __enter__(self) -> ContextBuilder:
        return ContextBuilder(self)

    def __exit__(self, *_):
        pass

    def event(self, command: Command, context: Context | None):
        if self._PARENT_ is not None:
            self._PARENT_.event(command, context)

    def render(self):
        self.node.render()

    @property
    def node(self) -> Node:
        return self._NODE_

    @property
    def parent(self) -> Context | None:
        return self._PARENT_ if not isinstance(self._PARENT_, Application) else None

    @staticmethod
    def _compare_(actual, expected) -> bool:
        if isinstance(expected, dict):
            for key, value in expected.items():
                if not hasattr(actual, key):
                    return False
                attr = getattr(actual, key)
                if not Context._compare_(attr, value):
                    return False
        else:
            if not actual == expected:
                return False
        return True

    def init(self, buffer: Buffer):
        # PERF: Different based on node type
        self.node._BUFFER_ = buffer
        
    def sibling(self, compare: dict | None = None) -> Context | None:
        if self._PARENT_ is not None:
            index = self._PARENT_._CHILDREN_.index(self)
            if compare is None:
                return self._PARENT_._CHILDREN_[index+1] if index+1 < len(self._PARENT_._CHILDREN_) else None
            else:
                children = self._PARENT_._CHILDREN_[:index] + self._PARENT_._CHILDREN_[index+1:]
                for child in children:
                    if Context._compare_(child.node, compare):
                        return child
                return None
        return None

    def child(self, compare: dict) -> Context | None:
        if compare is None:
            return None if len(self) == 0 else self._CHILDREN_[0]

        for child in self._CHILDREN_:
            if Context._compare_(child.node, compare):
                return child
        return None

    def __len__(self) -> int:
        return len(self._CHILDREN_)

class ContextBuilder:
    def __init__(self, context: Context):
        self._context_ = context

    def add(self, node: Node):
        self._context_._CHILDREN_.append(Context(node))

    def extend(self, *nodes: Node):
        self._context_._CHILDREN_.extend(Context(node) for node in nodes)

    def new(self, *_, **kwargs: Unpack[NodeArgs]) -> ContextBuilder:
        self._context_._CHILDREN_.append(Context(Node(**kwargs)))
        return ContextBuilder(self._context_._CHILDREN_[-1])

    @property
    def node(self) -> Node:
        return self._context_.node

    @property
    def handler(self) -> EventHandler | None:
        return self._context_.node.event_handler

    @handler.setter
    def handler(self, new: EventHandler | None):
        self._context_.node.event_handler = new


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

class Styles(TypedDict, total=False):
    border: bool
    border_color: ColorFormat
    border_corners: CornerType | tuple[CornerType, CornerType, CornerType, CornerType]
    border_edges: EdgeType | tuple[EdgeType, EdgeType] | tuple[
        EdgeType, EdgeType, EdgeType, EdgeType
    ]
    text_align: AlignType 
    overflow: HOverflowType | tuple[HOverflowType, VOverflowType]
    align_items: AlignType
    padding: int | tuple[int, int] | tuple[int, int, int, int]
    margin: int | tuple[int, int] | tuple[int, int, int, int]
    item_type: Literal['text', 'select']


class Style:
    __slots__ = (
        "text_align",
        "overflow",
        "align_items",
        "padding",
        "margin",
        "border",
        "border_color",
        "border_corners",
        "border_edges",
        "item_type"
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

        self.text_align: AlignType = styles.get("text_align", "start")
        if isinstance(to := styles.get("overflow", ('wrap', 'scroll')), tuple):
            self.overflow = to
        else:
            self.overflow = (to, to)
        if self.overflow[1] == 'wrap':
            self.overflow = (self.overflow[0], 'scroll')

        self.align_items: AlignType = styles.get("align_items", "start")
        self.padding: tuple[int, int, int, int] = _norm_sizing(styles.get("padding", 0))
        self.margin: tuple[int, int, int, int] = _norm_sizing(styles.get("margin", 0))
        self.item_type: Literal['text', 'select'] = styles.get("item_type", 'text')

    def copy(self) -> Style:
        """Copyt the current styles."""
        return deepcopy(self)

    def __repr__(self) -> str:
        values = ", ".join(f'{key}={getattr(self, key)}' for key in Styles.__annotations__.keys())
        return f"{{{values}}}"


def calc_perc(val: int | float, total: int) -> int:
    if isinstance(val, float):
        val = round(val * total)
    return val


ANSI = re.compile(r"\x1b\[[\d;]+m")


class Rect:
    __slots__ = ("left", "right", "top", "bottom")

    def __init__(
        self,
        x: int | float,
        y: int | float,
        w: int | float,
        h: int | float,
        mw: int,
        mh: int
    ):
        self.left = min(calc_perc(x, mw), mw - 1)
        self.right = min(self.left + calc_perc(w, mw), mw)
        self.top = min(calc_perc(y, mh), mh - 1)
        self.bottom = min(self.top + calc_perc(h, mh), mh)

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


def _norm_sizing(
    sizing: int | tuple[int, int] | tuple[int, int, int, int]
) -> tuple[int, int, int, int]:
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
            raise ValueError(
                f"Invalid tuple of sizing values. Expected 2 or 4 found {len(sizing)}"
            )
    elif isinstance(sizing, int):
        return tuple([sizing for _ in range(4)])
    else:
        raise ValueError(f"Invalid sizing type; was {type(sizing)}")

def _align_(collection: list, size: int, fill, alignment):
    if alignment == "center":
        remainder = size - len(collection)
        half = remainder // 2
        result = [fill for _ in range(half)]
        result.extend(collection)
        result.extend(fill for _ in range(remainder - half))
        return result
    elif alignment == "end":
        return [*[fill for _ in range(size - len(collection))], *collection]
    return collection

class Command(Enum):
    Quit = -1
    """Quit the application."""
    NOOP = 0
    """No Operation. Do nothing."""
    Deselect = 1
    """Deselect the node if posible."""
    Select = 2
    """Select the node or item if possible."""
    Updated = 4
    """Updates the nodes. This will re-render the node."""
    ScrollDown = 5
    """Scrolls the content of the node down. Also acts an `Updated` command."""
    ScrollUp = 6
    """Scrolls the content of the node up. Also acts an `Updated` command."""
    ScrollLeft = 7
    """Scrolls the content of the node Left. Also acts an `Updated` command."""
    ScrollRight = 8
    """Scrolls the content of the node Right. Also acts an `Updated` command."""

class Line:
    def __init__(
        self,
        line: str,
        width: int,
        overflow: HOverflowType,
        alignment: AlignType
    ):
        _style = _AnsiStyle()
        previous = 0
        self.pixels = []
        for ansi in ANSI.finditer(line):
            if ansi.start() > previous:
                # add all chars with previous style
                self.pixels.extend(
                    Pixel(c, _style) for c in line[previous : ansi.start()]
                )
            _style = _AnsiStyle.from_ansi(ansi.group(0))
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
                        _align_(
                            line[times * step :],
                            width,
                            Pixel("", _AnsiStyle()),
                            alignment,
                        )
                    )
            else:
                lines.append(
                    _align_(
                        line, width, Pixel("", _AnsiStyle()), alignment
                    )
                )
        return lines

    def __repr__(self) -> str:
        return repr(self.pixels)

class NodeArgs(TypedDict, total=False):
    pos: tuple[int | float, int | float]
    size: tuple[int | float, int | float]
    title: str
    style: Style
    event_handler: EventHandler
    state: dict

class Node:
    def __init__(
        self,
        buffer: Buffer | None = None,
        *_,
        **kwargs: Unpack[NodeArgs],
    ):
        self.style = kwargs.get('style', Style())
        self.title = kwargs.get('title', "")
        self.size = kwargs.get('size', (1.0, 1.0))
        self.pos = kwargs.get('pos', (0, 0))
        self.event_handler: EventHandler | None = kwargs.get('event_handler', None)
        
        self.state = kwargs.get('state', {}) or {}

        self._BUFFER_ = buffer
        self.focus: Literal['unfocus', 'focus', 'selected'] = "unfocus"
        self.text: str = ""
        self.scroll_y = 0
        self.scroll_x = 0

    def push(self, *text: str, sep: str = " "):
        """Write a string of text to the node. If the Style{'item_type': 'select'} is set
        every call to `push` will add the text to the previous entry. All new line sequences (`\\n`)
        are preserved.

        Args:
            *text (str): The text that should be displayed. Each entry is seperated by the
                `sep` param.
            sep (str): Seperator that goes between each entry of `text`
        """
        self.text += sep.join(text).replace("\n", "\r")

    def write(self, *text: str, sep: str = " "):
        """Write a string of text to the node. If the Style{'item_type': 'select'} is set
        every call to `write` becomes an entry in the selection list. All new line sequences (`\\n`)
        are preserved.

        Args:
            *text (str): The text that should be displayed. Each entry is seperated by the
                `sep` param.
            sep (str): Seperator that goes between each entry of `text`
        """
        self.text += '\n' + sep.join(text).replace("\n", "\r")

    def format(self, *text: str, sep: str = " ", mar: bool = True):
        """Adding a formatted string of text to the node. If the Style{'item_type': 'select'} is set
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
        """Get a specific entry in the selection list. If Style{'item_type': 'select'} is not set then
        None is returned.
        """
        if self.style.item_type == "select":
            return self.text.split("\n")[index].replace("\r", "\n")
        return None

    def clear(self):
        """Clear the nodes text."""
        self.text = ""

    def scroll_up(self):
        if self.style.overflow[1] != 'hidden':
            self.scroll_y -= 1

    def scroll_down(self):
        if self.style.overflow[1] != 'hidden':
            self.scroll_y += 1

    def scroll_left(self):
        if self.style.overflow[0] == 'scroll':
            self.scroll_x -= 1

    def scroll_right(self):
        if self.style.overflow[0] == 'scroll':
            self.scroll_x += 1

    def _border_(self, buffer: Buffer):
        """Generate the nodes border pixels."""
        if self.style.border:
            edges = tuple(
                [Edges[self.style.border_edges[i]].value[i % 2] for i in range(4)]
            )

            def get_edges(i: int) -> tuple[str, str]:
                # [top, left, bottom, right]
                # 0 => [0, 1]
                # 1 => [0, 3]
                # 2 => [2, 3]
                # 3 => [2, 1]
                result = (0 if i in [0, 1] else 2, 3 if i in [1, 2] else 1)
                return (
                    self.style.border_edges[result[0]],
                    self.style.border_edges[result[1]],
                )

            corners = tuple(
                [
                    Corners.from_edges(self.style.border_corners[i], *get_edges(i), i)
                    for i in range(4)
                ]
            )

            style = _AnsiStyle()
            if self.focus == "selected":
                style.style |= S.Bold.value
                style.fg = f";3{Color.new(self.style.border_color)}"
            elif self.focus == 'unfocus':
                style.fg = f';3{Color.new(243)}'

            if len(buffer) >= 2:
                (left, top, right, bottom) = self.valid_rect(buffer.width, buffer.height).points()
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

                if top + self.size[1] < buffer.height:
                    for i in range(left, right):
                        if i == left:
                            buffer[bottom - 1][i].set(corners[3], style)
                        elif i == right - 1:
                            buffer[bottom - 1][i].set(corners[2], style)
                        else:
                            buffer[bottom - 1][i].set(edges[2], style)
            self._title_(buffer)

    def valid_rect(self, mw: int, mh: int) -> Rect:
        """The valid rect the node can write into."""
        return Rect(*self.pos, *self.size, mw, mh)

    def _title_(self, buffer: Buffer):
        """Generate the nodes title."""
        r = self.valid_rect(buffer.width, buffer.height)
        (left, top, right, _) = r.points()
        w = r.width
        if (self.style.border and w < 3) or w < 1 or len(self.title) == 0:
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
        _style = _AnsiStyle()
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
                _style = _AnsiStyle.from_ansi(ansi.group(0))
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
            if self.style.overflow[1] == "scroll":
                buffer[rect.bottom-1][rect.right].set('⮟')
                buffer[rect.top][rect.right].set('⮝')

        lines = []
        if len(text) == 0:
            return []
        elif self.style.overflow[1] == 'hidden':
            lines = flatten_norm(text[:rect.height])
        else:
            # if select then bold selected and have padded scrolling
            # else normal scroll
            if self.style.item_type == 'text':
                lines = flatten_norm(text)
                maxv = len(lines) - rect.height - 1
                self.scroll_y = clamp(self.scroll_y, 0, maxv)
                lines = lines[self.scroll_y:]
            elif self.style.item_type == 'select':
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

                lines = [*previous[lower:], *text[self.scroll_y].normalized,*_next[:upper]]

        max_line_length = max(len(l) for l in lines) if len(lines) > 0 else 0
        if max_line_length > rect.width:
            if self.style.overflow[0] == "scroll":
                buffer[rect.bottom][rect.left].set('⮜')
                buffer[rect.bottom][rect.right-1].set('⮞')

        if self.style.overflow[0] == 'scroll':
            self.scroll_x = clamp(
                self.scroll_x,
                0, 
                max_line_length - rect.width,
            )
            for i in range(len(lines)):
                lines[i] = lines[i][min(len(lines[i]), self.scroll_x):]
        return lines

    def _text_(self, buffer: Buffer):
        rect = self.valid_rect(buffer.width, buffer.height)
        if self.style.border:
            rect.left += 1
            rect.top += 1
            rect.right -= 1
            rect.bottom -= 1
        (pl, pt, pr, pb) = self.style.padding
        rect.left += pl
        rect.right += pr
        rect.top += pt
        rect.bottom += pb

        text = []
        for line in self.text.strip().split("\n"):
            val = Line(line, rect.width, self.style.overflow[0], self.style.text_align)
            if len(val) > 0:
                text.append(val)

        text = self._scroll_(text, rect, buffer)

        if len(text) < rect.height:
            text = _align_(text, rect.height, [], self.style.align_items)

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
        return f"{self.__class__.__name__}(style={self.style!r})"


def __over_time__():
    buffer = Buffer()

    style = Style(border=True, border_color="cyan", text_align="end", align_items="end")
    node = Node(buffer, pos=(0.25, 0.25), size=(0.5, 0.5), style=style)

    message = [
        "[red]H",
        "e",
        "l",
        "l",
        "o",
        ",",
        " ",
        "[green]W",
        "o",
        "r",
        "l",
        "d",
        "[/]!",
    ]
    title = "Hello, World!"

    for i in range(len(title)):
        # Add char to title
        node.title += title[i]
        # Fill not yet written characters with whitespace to keep constant placement
        node.clear()
        node.format("".join(message[: i + 1]) + (" " * (12 - i)))

        # Choose random xterm color
        node.style.border_color = randrange(0, 256)

        # Render the node into the buffer
        node.render()

        # Write the buffer to stdout
        buffer.write()
        sleep(0.25)


def __standard__():
    buffer = Buffer()

    style = Style(
        border=True, border_color="cyan", text_align="center", align_items="center"
    )
    node = Node(buffer, size=(1.0, 1.0), style=style, title="Test Node")
    node.write("[red]Hello, [green]world[/]!")
    node.render()
    buffer.write()


def __multiple__():
    buffer = Buffer()

    style1 = Style(
        border=True,
        border_color="cyan",
        # top, left, bottom, right
        border_edges=("dashed", "dotted", "single", "single"),
        # tl, tr, br, bl
        border_corners=("single", "rounded", "single", "rounded"),
        text_align="end",
        align_items="end",
    )

    style2 = style1.copy()
    style2.border_color = "yellow"
    style2.border_edges = ("dashed", "dotted", "double", "single")
    style2.border_corners = ("single", "rounded", "double", "double")
    style2.text_align = "center"
    style2.align_items = "center"

    style3 = style2.copy()
    style3.border_color = "green"
    style3.text_align = "start"
    style3.align_items = "start"

    node1 = Node(buffer, size=(0.33, 0.25), style=style1, title="Node 1")
    node1.write("Hello, node 1!")
    node2 = Node(buffer, pos=(0.33, 0), size=(0.66, 1.0), style=style2, title="Node 2")
    node2.write("Hello, node 2!")
    node3 = Node(buffer, pos=(0, 0.25), size=(0.33, 0.75), style=style3, title="Node 3")
    node3.write("Hello, node 3!")
    nodes = [node1, node2, node3]
    for node in nodes:
        node.render()
    buffer.write()

def __scrolling__():
    """
        Select -> Use nodes handler
        Deselect -> Go to parents handlers if not None 
    """
    with Application() as app:
        with app.new(
            size=(20, 10),
            style=Style(
                border= True,
                item_type = 'select',
                overflow =  ('scroll', 'scroll')
            ),
            title="Scrolling Node",
        ) as selector:
            def handler(context: Context, node, event: Record, state):
                if event.type == "KEY":
                    key = event.key
                    if key == "j" or key == "down":
                        node.title = "down"
                    elif key == "k" or key == "up":
                        node.title = "up"
                    if key == "h" or key == "left":
                        node.title = "left"
                    elif key == "l" or key == "right":
                        node.title = "right"
                    elif key == "enter":
                        message = context.sibling({"id": "message"})
                        if message is not None:
                            message.node.write(f"{node.scroll_y}: selected")
                            return (Command.Updated, message)
                return default_handler(context, node, event, state)

            selector.handler = handler
            for i in range(20):
                selector.node.write(f"{i}: Sample text {'-' * 5}\n  preserve newline")

        app.add(Node(
            pos=(0, 10),
            size=(20, 3),
            style=Style(border = True)
        ))

if __name__ == "__main__":
    # __over_time__()
    # __standard__()
    # input()
    # __multiple__()
    # input()
    try:
        log = open("log.txt", "+w")
        __scrolling__()
    finally:
        log.close()


SingleDouble = Literal["single", "double"]
CornerType = Literal["single", "double", "rounded"]
EdgeType = Literal["single", "dashed", "dotted", "double"]
HOverflowType = Literal["wrap", "hidden", "scroll"]
VOverflowType = Literal["hidden", "scroll"]
AlignType = Literal['start', 'center', 'end']
EventHandler = Callable[[Context, Node | None, Record, dict | None], tuple | None]
