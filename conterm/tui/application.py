from __future__ import annotations
from queue import Full, Queue
from threading import Event, Thread
from time import sleep, time
from typing import Any, Callable, Iterable, Literal, Unpack
from conterm.control import Listener
from conterm.control.event import Record
from conterm.tui.buffer import Buffer
from conterm.tui.node import Node, NodeArgs
from conterm.tui.tree import EventHandler, TreeNode, TreeParent

from conterm.tui.util import Command, Locker, Rect, SizeType, State, norm_sizing


def _void_(*_):
    return

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
            if isinstance(child, TreeNode):
                child._PARENT_ = self._application_

    def set_update(self, new: Callable[[float, Application], None] | None):
        self._application_._update_ = new

    def set_current(self, new: Context | ContextBuilder | Section | SectionBuilder) -> Context | None:
        if isinstance(new, ContextBuilder):
            self._application_.set_current(new._context_)
        elif isinstance(new, SectionBuilder):
            self._application_.set_current(new._section_)
        else:
            self._application_.set_current(new)

def default_global_handler(context: TreeNode, record: Record):
    if record.type == "KEY":
        key = record.key
        if key == "q" or key == "Q":
            context.event(Command.Quit, context)
        elif key == "backspace":
            context.event(Command.Deselect, context)

class Application(TreeParent):
    _CURRENT_: TreeNode | None

    def __init__(
        self, 
        *children: TreeNode | TreeParent,
        update: Callable[[float, Application], None] | None = None,
        global_handler: EventHandler = default_global_handler,
    ) -> None:
        super().__init__(*children)

        self.event_bus = Queue()
        self.buffer = Buffer()
        self.state: State = State()

        self.focused = 0
        self.focusable = []

        self._CURRENT_ = None 
        self._global_handler_ = global_handler
        self._update_ = update

    def __enter__(self) -> ApplicationBuilder:
        return ApplicationBuilder(self)

    def __exit__(self, _et, ev, _etb): 
        if ev is None:
            self.init()
            self.run()
        else:
            raise ev

    @property
    def current(self) -> TreeNode | None:
        return self._CURRENT_

    def set_current(
        self,
        new: TreeNode,
        focus: Literal['normal', 'focus', 'unfocus', 'selected'] | None = None,
        unset: Literal['normal', 'focus', 'unfocus', 'selected'] | None = None,
    ) -> Context | None:
        if focus is not None:
            new.focus(focus)
        if unset is not None and self._CURRENT_ is not None:
            self._CURRENT_.focus(unset)

        self._CURRENT_ = new

    def find(self, compare: dict) -> Context | None:
        def flatten_nodes(children: list[TreeNode | TreeParent]) -> list[Context]:
            result = []
            for child in children:
                if isinstance(child, TreeParent):
                    result.extend(flatten_nodes(child._CHILDREN_))
                elif isinstance(child, Context):
                    result.append(child)
            return result

        contexts: list[Context] = flatten_nodes(self._CHILDREN_)
        for context in contexts:
            if context.is_match(compare):
                return context
        return None

    def handler(self, record: Record):
        self._global_handler_(self.current or Context(Node(), self), record)
        if self.current is None:
            if record.type == "KEY":
                key = record.key
                if key == "tab":
                    prv = self.focusable[self.focused]
                    prv.focus("unfocus")

                    self.focused = (self.focused + 1) % len(self.focusable)
                    nxt = self.focusable[self.focused]
                    nxt.focus("focus")
                elif key == "shift+tab":
                    self.focusable[self.focused].focus("unfocus")
                    self.focused = (self.focused - 1) % len(self.focusable)
                    self.focusable[self.focused].focus("focus")
                elif key == "enter":
                    self.event(Command.Select)
        else:
            self.current.handler(self.current, record)

    def event(self, command: Command, context: TreeNode | None = None):
        try:
            self.event_bus.put((command, context), block=False)
        except Full:
            pass

    def layout(self):
        # TODO: Auto calculate and move objects around
        pass
    
    def init(self):
        self.layout()
        for context in self._CHILDREN_:
            context.init(self.buffer)

        def extract_selectable(children: list[TreeNode | TreeParent]) -> list[TreeNode]:
            result = []
            for child in children:
                if isinstance(child, TreeParent):
                    result.extend(extract_selectable(child._CHILDREN_))
                elif isinstance(child, TreeNode) and child.get('focus') != 'static':
                    result.append(child)
            return result

        self.focusable = extract_selectable(self._CHILDREN_)

        if self._CURRENT_ is None:
            if len(self.focusable) == 1:
                self.focused = 0 
                self.set_current(self.focusable[0])
                self._CURRENT_.focus('selected')
            elif len(self.focusable) > 1:
                for focusable in self.focusable:
                    focusable.focus('unfocus')
                self.focusable[0].focus('focus')

        self.render()

    def render(self):
        for child in self._CHILDREN_:
            child.render()
        self.buffer.write()

    def update(self, dt: float):
        if self._update_ is not None:
            self._update_(dt, self)

    def run(self):
        iqueue = Queue()
        app = Locker(self)

        def on_interrupt():
            self.event_bus.put((Command.Quit, None))
            for thread in threads:
                thread.stop()

        update = Update(self.event_bus, app=app)
        render = Render(self.event_bus, iqueue, app=app, on_quit=on_interrupt)
        ilistener = Listener(
            on_event=on_event,
            on_interrupt=on_interrupt,
            state={'events': iqueue}
        )

        threads = [render, update, ilistener]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

class Context(TreeNode):
    _NODE_: Node

    def __init__(self, node: Node, parent: TreeParent | None = None) -> None:
       super().__init__(parent=parent)
       self._NODE_ = node

    def handler(self, context: TreeNode, record: Record) -> tuple | None:
        if self.node.event_handler is None:
            return _void_(context, record)
        return self.node.event_handler(context, record)

    @property
    def width(self) -> int:
        return self.node.width

    @property
    def height(self) -> int:
        return self.node.height

    def write(self, *text: str, sep: str = " "):
        self.node.write(*text, sep=sep)

    def format(self, *text: str, sep: str = " ", mar: bool = True):
        self.node.format(*text, sep=sep, mar=mar)

    def clear(self):
        self.node.clear()

    @property
    def node(self) -> Node:
        return self._NODE_

    def get_scroll(self) -> tuple[int, int]:
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
            return getattr(self.node, key)
        return default
        
    def scroll(self, direction: Literal['up', 'down', 'left', 'right']):
        if direction == "up":
            self.node.scroll_up()
        elif direction == "down":
            self.node.scroll_down()
        elif direction == "left":
            self.node.scroll_left()
        elif direction == "right":
            self.node.scroll_right()

    def focus(self, focus: Literal['normal', 'unfocus', 'focus', 'selected'], _: int = 1):
        if self.node.focus != 'static':
            self.node.focus = focus

    def set_buffer(self, buffer: Buffer | None):
        self.node._BUFFER_ = buffer

    def render(self):
        self.node.render()

    def init(self, buffer: Buffer):
        self.set_buffer(buffer)

    def is_match(self, compare: dict) -> bool:
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

class Section(TreeNode, TreeParent):
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
        self.padding = norm_sizing(padding)
        self.size = size
        self.pos = pos
        self.focused = 0
        self.focusable = []
        TreeNode.__init__(self, parent=parent)
        TreeParent.__init__(self, *children)

    def handler(self, context: TreeNode, record: Record) -> tuple | None:
        return

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
            if isinstance(child, TreeNode) and child.get('focus') != 'static':
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

class StoppableThread(Thread):
    def __init__(self, *args, **kwargs) -> None:
        kwargs.pop('daemon', None)
        super().__init__(*args, daemon=True, **kwargs)
        self._stop_ = Event()
        self._exc_: Exception | None = None

    def stop(self):
        self._stop_.set()

    def join(self):
        Thread.join(self)
        if self._exc_ is not None:
            raise self._exc_

class Update(StoppableThread):
    def __init__(
        self,
        cqueue: Queue,
        *args,
        app: Locker[Application],
        rate: float = 1/60,
        **kwargs
    ) -> None:
        kwargs['name'] = 'conterm_tui_update'
        super().__init__(*args, **kwargs)

        self.cqueue = cqueue
        self.rate = rate

        self.app = app

    def run(self):
        last_time = 0
        try:
            while not self._stop_.is_set():
                if (dt := time() - last_time) >= self.rate:
                    last_time=time()
                    with self.app as application:
                        application.update(dt)
        except Exception as error:
            self._exc_ = error

class Render(StoppableThread):
    def __init__(
        self,
        cqueue: Queue,
        iqueue: Queue,
        *args,
        app: Locker[Application],
        rate: float = 1/60,
        on_quit: Callable | None = None,
        **kwargs
    ) -> None:
        kwargs['name'] = 'conterm_tui_render'
        super().__init__(*args, **kwargs)

        self.cqueue = cqueue
        self.iqueue = iqueue
        self.rate = rate

        self.app = app
        self.on_quit = on_quit
        self.log = open("app.txt", "+w", encoding="utf-8")

    def __del__(self):
        self.log.close()

    def _process_inputs_(self):
        with self.app as application:
            inputs: list[Record] = []
            try:
                while True:
                    inputs.append(self.iqueue.get(block=False))
            except: pass

            for i in inputs:
                self.log.write(repr(i) + "\n")
                application.handler(i)
            self.log.flush()

    def _process_commands_(self):
        with self.app as application:
            commands: list[tuple[Command, TreeNode]] = []
            try:
                while True:
                    commands.append(self.cqueue.get(block=False))
            except: pass

            for command, _ in commands:
                if command == Command.Quit and self.on_quit is not None:
                    self.on_quit()
                elif command == Command.Deselect:
                    for focusable in application.focusable:
                        focusable.focus('unfocus')
                    application._CURRENT_ = None
                    application.focusable[application.focused].focus('focus')
                elif command == Command.Select:
                    for focusable in application.focusable:
                        focusable.focus('normal')
                    application.set_current(application.focusable[application.focused], 'selected')

    def run(self):
        """
            :Process Input:
            :Process Commands:
            :Render:
        """
        try:
            while not self._stop_.is_set():
                self._process_inputs_()
                self._process_commands_()
                with self.app as application:
                    application.render()
                sleep(self.rate)
        except Exception as error:
            self._exc_ = error


def on_event(record: Record, state: dict):
    state['events'].put(record)
