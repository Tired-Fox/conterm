"""
Mini module for creating tui applications. This library is fairly simple.
If more complex features are desired please see other Tui libraries.
"""
from __future__ import annotations
from abc import abstractmethod

from copy import deepcopy
from enum import Enum
from math import floor
from queue import Empty, Full, Queue
from random import randrange
import threading
from time import sleep, time
from typing import Any, Callable, Iterable, Literal, Protocol, TypedDict, Unpack, overload, runtime_checkable
from conterm.control import Listener
from conterm.control.event import Record
from conterm.pretty.markup import Markup
import re

from conterm.tui.buffer import Buffer, Pixel
from conterm.tui.style import S, ColorFormat, Style as _AnsiStyle, Color

def clamp(value: int, lower, upper) -> int:
    return max(lower, min(value, upper))

def default_handler(*_):
    return

def scroll_node(context: TreeNode, event: Record):
    if event.type == "KEY":
        if event.key == "j" or event.key == "down":
            context.scroll("down")
            context.event(Command.Updated, context)
        elif event.key == "k" or event.key == "up":
            context.scroll("up")
            context.event(Command.Updated, context)
        if event.key == "h" or event.key == "left":
            context.scroll("left")
            context.event(Command.Updated, context)
        elif event.key == "l" or event.key == "right":
            context.scroll("right")
            context.event(Command.Updated, context)

class Updater(threading.Thread):
    def __init__(self, app: Application, *args, **kwargs):
        self._stop_ = threading.Event()
        self.update = app._update_
        self.app = app
        self.state = AppState(app)
        super().__init__(name="python_update_loop", daemon=True)

    def run(self) -> None:
        last_time = time()
        while True:
            try:
                command, context = self.app.event_bus.get(block=False)
                if command == Command.Updated:
                    context.render()
                    self.app.buffer.write()
                elif command == Command.Select:
                    for focusable in self.app.focusable:
                        focusable.focus('normal')
                    self._CURRENT_ = self.app.focusable[self.app.focused]
                    self._CURRENT_.focus('selected')
                    self.app.render()
                elif command == Command.Deselect:
                    # PERF: Make this part parent object so it works with nesting
                    for focusable in self.app.focusable:
                        focusable.focus('unfocus')
                    self._CURRENT_ = None
                    self.app.focusable[self.app.focused].focus('focus')
                    self.app.render()
                elif command == Command.Quit:
                    # Terminal reset codes goes here
                    return
            except Empty:
                pass

            if self.update is not None:
                self.update(time() - last_time, self.state)
                last_time = time()
        # last_time = time()
        # while not self._stop_.is_set():
        #     if (ct := time() - last_time) >= 1/60:
        #         self.update(ct, self.app)
        #         last_time = time()
    
    def stop(self):
        self._stop_.set()
        self.join()

class ApplicationBuilder:
    def __init__(self, app: Application) -> None:
        self._application_ = app

    def context(self, *_, **kwargs: Unpack[NodeArgs]) -> Context:
        new = Context(Node(**kwargs))
        new.set_buffer(self._application_.buffer)
        self._application_._CHILDREN_.append(new)
        new._PARENT_ = self._application_
        return new

    def section(self, *_, pos=(0, 0), size=(1.0, 1.0), padding: SizeType = 0) -> Section:
        new = Section(pos=pos, size=size, padding=padding)
        new.set_buffer(self._application_.buffer)
        self._application_._CHILDREN_.append(new)
        new._PARENT_ = self._application_
        return new

    def extend(self, nodes: Iterable[Node]):
        start = len(self._application_._CHILDREN_)
        self._application_._CHILDREN_.extend(Context(node) for node in nodes)
        for child in self._application_._CHILDREN_[start:]:
            child._PARENT_ = self._application_

    def set_update(self, new: Callable[[int], int] | None):
        self._application_._update_ = new

    def set_current(self, new: Context | ContextBuilder | Section | SectionBuilder) -> Context | None:
        if isinstance(new, ContextBuilder):
            self._application_.set_current(new._context_)
        elif isinstance(new, SectionBuilder):
            self._application_.set_current(new._section_)
        else:
            self._application_.set_current(new)

def default_global_handler(context: TreeNode, record: Record) -> tuple:
    if record.type == "KEY":
        key = record.key
        if key == "q" or key == "Q":
            return (Command.Quit, context)
        elif key == "backspace":
            return (Command.Deselect, context)
    return (Command.NOOP, None)

class Application:
    _CHILDREN_: list[TreeNode]
    _CURRENT_: TreeNode | None

    def __init__(
        self, 
        *children: Context,
        update: Callable[[float, AppState], None] | None = None,
        global_handler: EventHandler = default_global_handler,
    ) -> None:
        self.event_bus = Queue()
        self.buffer = Buffer()
        self._CHILDREN_ = list(children)
        for child in self._CHILDREN_:
            child._PARENT_ = self
        self._CURRENT_ = None 
        self._global_handler_ = global_handler
        self.focused = 0
        self.focusable = []
        self.input_watcher = Listener(
            on_event=self.handler,
            on_interrupt=lambda: self.event_bus.put((Command.Quit, None), block=False),
        )
        self._update_ = update
        self.updater = Updater(self)
        self._quit_ = False

    def __enter__(self) -> ApplicationBuilder:
        return ApplicationBuilder(self)

    def __exit__(self, _et, ev, _etb): 
        if ev is None:
            self.run()
        else:
            self.input_watcher.stop()
            self.updater.stop()
            raise ev

    @property
    def current(self) -> TreeNode | None:
        return self._CURRENT_

    def set_current(self, new: TreeNode) -> Context | None:
        if self._CURRENT_ is not None:
            self._CURRENT_.focus('unfocus')
        self._CURRENT_ = new

    def app_handler(self, record: Record):
        if record.type == "KEY":
            key = record.key
            if key == "tab":
                prv = self.focusable[self.focused]
                prv.focus("unfocus")
                self.event(Command.Updated, prv)

                self.focused = (self.focused + 1) % len(self.focusable)
                nxt = self.focusable[self.focused]
                nxt.focus("focus")
                return (Command.Updated, nxt)
            elif key == "shift+tab":
                self.focusable[self.focused].focus("unfocus")
                self.event(Command.Updated, self.focusable[self.focused])
                self.focused = (self.focused - 1) % len(self.focusable)
                self.focusable[self.focused].focus("focus")
                return (Command.Updated, self.focusable[self.focused])
            elif key == "enter":
                return (Command.Select, self.focusable[self.focused])

    def handler(self, record: Record, _: dict) -> bool:
        if self.current is None:
            data = self.app_handler(record)
        elif self.current.handler is None:
            data = default_handler(self.current, record)
        else:
            data = self.current.handler(self.current, record)

        if data is None:
            current = self.current or Context(Node())
            data = self._global_handler_(current, record)

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

    def event(self, command: Command, context: TreeNode | None = None):
        try:
            self.event_bus.put((command, context), block=False)
        except Full:
            pass

    def layout(self):
        pass
    
    def init(self):
        self.layout()
        for context in self._CHILDREN_:
            context.init(self.buffer)

        def extract_selectable(children: list[TreeNode]) -> list[TreeNode]:
            result = []
            for child in children:
                if isinstance(child, TreeParent):
                    result.extend(extract_selectable(child._CHILDREN_))
                elif isinstance(child, TreeNode) and child.get('focus') != 'static':
                    result.append(child)
            return result

        self.focusable = extract_selectable(self._CHILDREN_)
        for focusable in self.focusable:
            focusable.focus('unfocus')

        if self._CURRENT_ is None:
            if len(self.focusable) == 1:
                self.focused = 0 
                self.set_current(self.focusable[0])
                self._CURRENT_.focus('focus')
            elif len(self.focusable) > 1:
                self.focusable[0].focus('focus')

    def render(self):
        for child in self._CHILDREN_:
            child.render()
        self.buffer.write()

    def run(self):
        self.init()
        self.render()

        self.input_watcher.start()
        self.updater.start()
        self.input_watcher.join()
        self.updater.join()

@runtime_checkable
class TreeNode(Protocol):
    _PARENT_: TreeParent | Application | None
    def __init__(self, parent: TreeParent | None = None) -> None:
        self._PARENT_ = parent

    def event(self, command: Command, context: TreeNode | None):
        if self._PARENT_ is not None:
            self._PARENT_.event(command, context)

    @property
    def handler(self) -> EventHandler:
        raise NotImplementedError

    @staticmethod
    def compare(actual, expected) -> bool:
        if isinstance(expected, dict):
            for key, value in expected.items():
                if not hasattr(actual, key):
                    return False
                attr = getattr(actual, key)
                if not TreeNode.compare(attr, value):
                    return False
        else:
            return actual == expected
        return True

    def get_scroll(self) -> tuple[int, int]:
        return (0, 0)
    def set(self, key: str, value: Any):
        return
    def get(self, key: str, default: Any | None = None):
        return default
    def scroll(self, direction: Literal['up', 'down', 'left', 'right']):
        return

    @overload
    def sibling(self, compare: dict | None = None, *_, node: Literal['context'] = 'context') -> Context  | None:
        ...
    @overload
    def sibling(self, compare: dict | None = None, *_, node: Literal['section'] = 'section') -> Section | None:
        ...
    @overload
    def sibling(self, compare: dict | None = None, *_, node: Literal[''] = '') -> Section | Context | None:
        ...
    def sibling(
        self,
        compare: dict | None = None,
        *_,
        node: Literal['context', 'section', ''] = ''
    ) -> Context | Section | None:
        _type = (Section, Context)
        if node != '':
            _type = Context if node == 'context' else Section

        if self._PARENT_ is not None and isinstance(self._PARENT_, (Section, Application)):
            index = self._PARENT_._CHILDREN_.index(self)
            if compare is None:
                children = [child for child in self._PARENT_._CHILDREN_[index+1:] if isinstance(child, _type)]
                return children[0] if len(children) > 0 else None
            else:
                children = [
                    child for child in self._PARENT_._CHILDREN_[:index] + self._PARENT_._CHILDREN_[index+1:]
                    if isinstance(child, _type)
                ]
                for child in children:
                    if child.is_match(compare):
                        return child
                return None
        return None
    def __exit__(self, _et, ev, _etb):
        if ev is not None:
            raise ev

    @property
    def parent(self) -> TreeParent | None:
        return self._PARENT_ if not isinstance(self._PARENT_, Application) else None
    @abstractmethod
    def focus(self, focus: Literal['normal', 'unfocus', 'focus', 'selected'], depth: int = 1):
        raise NotImplementedError
    @abstractmethod
    def is_match(self, compare: dict) -> bool:
        raise NotImplementedError
    @abstractmethod
    def set_buffer(self, buffer: Buffer | None):
        raise NotImplementedError
    @abstractmethod
    def render(self):
        raise NotImplementedError
    @abstractmethod
    def init(self, buffer: Buffer):
        raise NotImplementedError
    def __enter__(self):
        ...

@runtime_checkable
class TreeParent(TreeNode, Protocol):
    _CHILDREN_: list[TreeNode]

    def __init__(self, *children: TreeNode, parent: TreeParent | None = None) -> None:
        super().__init__(parent)
        self._CHILDREN_ = list(children)
        for child in self._CHILDREN_:
            child._PARENT_ = self

    @overload
    def child(self, compare: dict | None = None, *_, node: Literal['context'] = 'context') -> Context | None:
        ...
    @overload
    def child(self, compare: dict | None = None, *_, node: Literal['section'] = 'section') -> Section | None:
        ...
    @overload
    def child(self, compare: dict | None = None, *_, node: Literal[''] = '') -> Section | Context | None:
        ...
    def child(
        self,
        compare: dict | None = None,
        *_,
        node: Literal['context', 'section', ''] = '',
    ) -> Context | Section | None:
        _type = (Section, Context)
        if node != '':
            _type = Context if node == 'context' else Section
        children = [child for child in self._CHILDREN_ if isinstance(child, _type)]

        if compare is None:
            return None if len(children) == 0 else children[0]

        for child in children:
            if isinstance(child, Section) and TreeNode.compare(child, compare):
                return child 
            elif isinstance(child, Context) and TreeNode.compare(child.node, compare):
                return child
        return None

    def __len__(self) -> int:
        return  len(self._CHILDREN_)

class Context(TreeNode):
    _NODE_: Node

    def __init__(self, node: Node, parent: TreeParent | None = None) -> None:
       super().__init__(parent=parent)
       self._NODE_ = node
       self.mutex = threading.Lock()

    def handler(self, context: TreeNode, record: Record) -> tuple | None:
        if self.node.style.overflow[0] == 'scroll' or self.node.style.overflow[1] == 'scroll':
            scroll_node(context, record)
        if self.node.event_handler is None:
            return default_handler(context, record)
        return self.node.event_handler(context, record)

    @property
    def width(self) -> int:
        with self.mutex:
            return self.node.width

    @property
    def height(self) -> int:
        with self.mutex:
            return self.node.height

    def write(self, *text: str, sep: str = " "):
        with self.mutex:
            self.node.write(*text, sep=sep)

    def format(self, *text: str, sep: str = " ", mar: bool = True):
        with self.mutex:
            self.node.format(*text, sep=sep, mar=mar)

    def clear(self):
        with self.mutex:
            self.node.clear()

    @property
    def node(self) -> Node:
        return self._NODE_

    def get_scroll(self) -> tuple[int, int]:
        with self.mutex:
            return self.node.scroll_x, self.node.scroll_y

    def set(self, key: str, value: Any):
        # Gatekeep what values can be set
        if key not in ['title', 'style']:
            return

        if hasattr(self.node, key):
            setattr(self.node, key, value)

    def get(self, key: str, default: Any | None = None):
        if key not in ['title', 'style', 'focus', 'selected']:
            return default
        if hasattr(self.node, key):
            with self.mutex:
                return getattr(self.node, key)
        return default
        
    def scroll(self, direction: Literal['up', 'down', 'left', 'right']):
        with self.mutex:
            if direction == "up":
                self.node.scroll_up()
            elif direction == "down":
                self.node.scroll_down()
            elif direction == "left":
                self.node.scroll_left()
            elif direction == "right":
                self.node.scroll_right()

    def focus(self, focus: Literal['normal', 'unfocus', 'focus', 'selected'], _: int = 1):
        with self.mutex:
            if self.node.focus != 'static':
                self.node.focus = focus

    def set_buffer(self, buffer: Buffer | None):
        with self.mutex:
            self.node._BUFFER_ = buffer

    def render(self):
        with self.mutex:
            self.node.render()

    def init(self, buffer: Buffer):
        self.set_buffer(buffer)

    def is_match(self, compare: dict) -> bool:
        with self.mutex:
            return TreeNode.compare(self.node, compare)

    def __enter__(self) -> ContextBuilder:
        return ContextBuilder(self)

class ContextBuilder:
    def __init__(self, context: Context):
        self._context_ = context

    @property
    def node(self) -> Node:
        return self._context_.node

    @property
    def handler(self) -> EventHandler | None:
        return self._context_.node.event_handler

    @handler.setter
    def handler(self, new: EventHandler | None):
        self._context_.node.event_handler = new

    def write(self, *text: str, sep: str = " "):
        self._context_.node.write(*text, sep=sep)

    def format(self, *text: str, sep: str = " ", mar: bool = True):
        self._context_.node.format(*text, sep=sep, mar=mar)

    def clear(self):
        self._context_.node.clear()

    @property
    def width(self) -> int:
        return self._context_.width

    @property
    def height(self) -> int:
        return self._context_.height

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
    padding: SizeType 


class Style:
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

    def __init__(self, **styles: Unpack[Styles]):
        self.border = styles.get("border", True)
        self.border_color = styles.get("border_color", "yellow")
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

    def copy(self) -> Style:
        """Copyt the current styles."""
        return deepcopy(self)

    def __repr__(self) -> str:
        values = ", ".join(f'{key}={getattr(self, key)}' for key in Styles.__annotations__.keys())
        return f"{{{values}}}"


def calc_size(val: int | float | Callable[[int], int], total: int) -> int:
    if callable(val):
        val = val(total)
    elif isinstance(val, float):
        val = round(val * total)
    return val


ANSI = re.compile(r"\x1b\[[\d;]+m")


class Rect:
    __slots__ = ("left", "right", "top", "bottom")

    def __init__(
        self,
        x: int | float | Callable[[int], int],
        y: int | float | Callable[[int], int],
        w: int | float | Callable[[int], int],
        h: int | float | Callable[[int], int],
        mw: int,
        mh: int
    ):
        self.left = min(calc_size(x, mw), mw - 1)
        self.right = min(self.left + calc_size(w, mw), mw)
        self.top = min(calc_size(y, mh), mh - 1)
        self.bottom = min(self.top + calc_size(h, mh), mh)

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
    sizing: SizeType 
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
    id: str
    pos: tuple[int | float, int | float | Callable[[int], int]]
    size: tuple[int | float, int | float | Callable[[int], int]]
    title: str
    style: Style
    event_handler: EventHandler
    state: dict
    contains: Literal['text', 'list']

class Node:
    def __init__(
        self,
        buffer: Buffer | None = None,
        *_,
        **kwargs: Unpack[NodeArgs],
    ):
        self.id = kwargs.get("id", None)
        self.style = kwargs.get('style', Style())
        self.title = kwargs.get('title', "")

        self.size = kwargs.get('size', (1.0, 1.0))
        self.pos = kwargs.get('pos', (0, 0))

        self.event_handler: EventHandler | None = kwargs.get('event_handler', None)
        self.contains: Literal['text', 'list'] = kwargs.get('contains', 'text')
        
        self.state = kwargs.get('state', {}) or {}

        self._BUFFER_ = buffer
        self.focus: Literal['static', 'normal', 'unfocus', 'focus', 'selected'] = "normal"
        if self.style.overflow[0] != "scroll" and self.style.overflow[1] != "scroll":
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
            if self.focus == 'selected':
                style.style |= S.Bold.value
            if self.focus == 'unfocus':
                style.fg = f';3{Color.new(243)}'
                style.style |= S.Bold.value
            elif self.focus == "focus":
                style.fg = f';3{Color.new(self.style.border_color)}'
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
                buffer[rect.bottom-1][rect.right-1].set('⮟')
                buffer[rect.top][rect.right-1].set('⮝')

        lines = []
        if len(text) == 0:
            return []
        elif self.style.overflow[1] == 'hidden':
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
        rect = self.rect()
        if self.style.border:
            rect.left += 1
            rect.top += 1
            rect.right -= 1
            rect.bottom -= 1
        (pl, pt, pr, pb) = self.style.padding
        rect.left += pl
        rect.right -= pr
        rect.top += pt
        rect.bottom -= pb

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

class Section(TreeParent):
    """A smaller organized section of the total application buffer. This object can be nested
    to have smaller sections of the given section. All nested Nodes reference their sizing from
    this section.
    """

    def __init__(
        self,
        *children: TreeNode,
        pos: tuple[int, int] = (0, 0),
        size: tuple[int, int] = (0, 0),
        padding: SizeType,
        buffer: Buffer | None = None,
        parent: TreeParent | None = None,
    ) -> None:
        self._BUFFER_ = buffer
        self.padding = _norm_sizing(padding)
        self.size = size
        self.pos = pos
        self.focused = 0
        self.focusable = []
        super().__init__(*children, parent=parent)

    def handler(self, context: TreeNode, record: Record) -> tuple | None:
        return
        # if record.type == "KEY" and len(self.focusable) > 0:
        #     key = record.key
        #     if key == "tab":
        #         prv = self.focusable[self.focused]
        #         prv.focus("unfocus")
        #         self.event(Command.Updated, prv)
        #
        #         self.focused = (self.focused + 1) % len(self.focusable)
        #         nxt = self.focusable[self.focused]
        #         nxt.focus("focus")
        #         return (Command.Updated, nxt)
        #     elif key == "shift+tab":
        #         self.focusable[self.focused].focus("unfocus")
        #         self.event(Command.Updated, self.focusable[self.focused])
        #         self.focused = (self.focused - 1) % len(self.focusable)
        #         self.focusable[self.focused].focus("focus")
        #         return (Command.Updated, self.focusable[self.focused])
        #     elif key == "enter":
        #         self.focusable[self.focused].focus("selected")
        #         return (Command.Select, context)

    def focus(self, focus: Literal['normal', 'unfocus', 'focus', 'selected'], depth: int = 1):
        if depth <= 0:
            return

        for child in self.focusable:
           child.focus(focus, depth-1)

    def is_match(self, compare: dict) -> bool:
        return TreeNode.compare(self, compare)

    def set_buffer(self, buffer: Buffer | None):
        # PERF: Set buffer size based on padding, size, and position
        if buffer is not None:
            rect = Rect(*self.pos, *self.size, buffer.width, buffer.height)
            self._BUFFER_ = buffer.sub(rect.left, rect.top, *rect.dims())
        else:
            self._BUFFER_ = None
            for child in self._CHILDREN_:
                child.set_buffer(self._BUFFER_)

    def render(self):
        for child in self._CHILDREN_:
            child.render()

    def init(self, buffer: Buffer):
        self.focusable.clear()
        for child in self._CHILDREN_:
            if child.get('focus') != 'static':
                self.focusable.append(child)
        self.set_buffer(buffer)

    def __enter__(self):
        return SectionBuilder(self) 

class SectionBuilder:
    def __init__(self, section: Section):
        self._section_ = section 

    def context(self, *_, **kwargs: Unpack[NodeArgs]) -> Context:
        new = Context(Node(**kwargs))
        new.set_buffer(self._section_._BUFFER_)
        self._section_._CHILDREN_.append(new)
        new._PARENT_ = self._section_
        return new

    def section(self, *_, pos=(0, 0), size=(1.0, 1.0), padding: SizeType = 0) -> Section:
        new = Section(pos=pos, size=size, padding=padding)
        new.set_buffer(self._section_._BUFFER_)
        self._section_._CHILDREN_.append(new)
        new._PARENT_ = self._section_
        return new

def __over_time__():
    buffer = Buffer()

    style = Style(border=True, border_color="cyan", text_align="end", align_items="end")
    node = Node(buffer=buffer, pos=(0.25, 0.25), size=(0.5, 0.5), style=style)

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
    node = Node(buffer=buffer, size=(1.0, 1.0), style=style, title="Test Node")
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

    node1 = Node(buffer=buffer, size=(0.33, 0.25), style=style1, title="Node 1")
    node1.write("Hello, node 1!")
    node2 = Node(buffer=buffer, pos=(0.33, 0), size=(0.66, 1.0), style=style2, title="Node 2")
    node2.write("Hello, node 2!")
    node3 = Node(buffer=buffer, pos=(0, 0.25), size=(0.33, 0.75), style=style3, title="Node 3")
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
        with app.context(
            id="selector",
            size=(20, 10),
            style=Style(
                border= True,
                overflow =  ('scroll', 'scroll')
            ),
            title="Scrolling Node",
            contains="list"
        ) as selector:
            def handler(context: TreeNode, event: Record):
                if event.type == "KEY":
                    key = event.key
                    if key == "j" or key == "down":
                        context.set("title", "down")
                    elif key == "k" or key == "up":
                        context.set("title", "up")
                    if key == "h" or key == "left":
                        context.set("title", "left")
                    elif key == "l" or key == "right":
                        context.set("title", "right")
                    elif key == "enter":
                        message = context.sibling({"id": "message"})
                        if message is not None:
                            message.node.clear()
                            message.node.write(f"{context.get_scroll()[1]}: selected")
                            return (Command.Updated, message)
                scroll_node(context, event)

            selector.handler = handler
            for i in range(20):
                selector.node.write(f"{i}: Sample text {'-' * 5}\n  preserve newline")

        app.context(
            id="message",
            pos=(0, 10),
            size=(20, 3),
            style=Style(border = True)
        )

class AppState:
    def __init__(self, app: Application) -> None:
       self._state_ = {}
       self._app_ = app

    def get(self, key: str, default: Any | None = None):
        return self._state_.get(key, default)

    def set(self, key: str, value: Any):
        self._state_[key] = value

    def find(self, compare: dict[Literal['id'], str]) -> Context | None:
        def flatten_context(children: list[TreeNode]) -> list[Context]:
            result = []
            for child in children:
                if isinstance(child, TreeParent):
                    result.extend(flatten_context(child._CHILDREN_))
                elif isinstance(child, TreeNode):
                    result.append(child)
            return result

        contexts = flatten_context(self._app_._CHILDREN_)
        for context in contexts:
            if context.is_match(compare):
                return context
        return None

def __applicaiton__():
    def update(dt: float, app: AppState):
        total = app.get('total', float((8*60)+35))
        prgs = app.get('progress', 0.0)
        if floor(prgs) >= floor(prgs + dt):
            if (playing := app.find({'id': 'playing'})) is not None:
                message = f'Hi Ren ~ Ren ({int(prgs)//60}:{str(int(prgs)%60).rjust(2, "0")}/{int(total)//60}:{str(int(total)%60).rjust(2, "0")})'
                
                playing.node.clear()
                step = playing.width / total
                progress = min(round((prgs+dt) * step), playing.width)
                missing = playing.width - progress

                playing.write(message)
                playing.format(f"[green]{'█'*progress}[/]{'░'*missing}")
                playing.event(Command.Updated, playing)
        app.set('progress', (prgs + dt) % total)

    with Application(update=update) as app:
        with app.section(size=(1.0, lambda mx: mx-4)) as top:
            with top.section(size=(0.3, 1.0)) as left:
                with left.context(
                    id="titlebar",
                    size=(1.0, 0.3),
                    style=Style(text_align='center', align_items='center', overflow=('wrap', 'hidden'), border_color="red"),
                ) as titlebar:
                    titlebar.write("Hello World")

                with left.context(
                    id="playlists",
                    title="Playlists",
                    pos=(0, 0.3),
                    size=(1.0, 0.9),
                    style=Style(overflow="scroll", padding=(1, 0)),
                    contains='list'
                ) as titlebar:
                    for i in range(20):
                        titlebar.write(f"playlist {i}")

            top.context(
                id="main",
                pos=(0.3,0),
                size=(.7, 1.0),
                title="Main",
            )
        with app.context(
            id="playing",
            title="Now Playing",
            pos=(0, lambda mx: mx-4),
            size=(1.0, 4),
            style=Style(align_items="center", overflow='hidden', padding=(1, 0)),
        ) as playing:
            message = 'Hi Ren ~ Ren (0:00/8:35)'
            playing.write(message)
            playing.write('░'*(playing.width))

if __name__ == "__main__":
    # __over_time__()
    # __standard__()
    # input()
    # __multiple__()
    # input()
    #__scrolling__()
    try:
        # log = open("log.txt", "+w", encoding="utf-8")
        __applicaiton__()
        # ctx = Context(Node(id='playing'))
        # print(ctx.is_match({'id': 'playing'}))
    finally:
        pass
        # log.close()


SingleDouble = Literal["single", "double"]
CornerType = Literal["single", "double", "rounded"]
EdgeType = Literal["single", "dashed", "dotted", "double"]
HOverflowType = Literal["wrap", "hidden", "scroll"]
VOverflowType = Literal["hidden", "scroll"]
AlignType = Literal['start', 'center', 'end']
EventHandler = Callable[[TreeNode, Record], tuple | None]
SizeType = int | tuple[int, int] | tuple[int, int, int, int]
TreeType = Context | Application | Section
