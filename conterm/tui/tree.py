from __future__ import annotations
from abc import abstractmethod
from typing import Any, Callable, Literal, Protocol, overload, runtime_checkable
from conterm.control.event import Record
from conterm.tui.buffer import Buffer

from conterm.tui.util import Command

@runtime_checkable
class _Base_(Protocol):
    @abstractmethod
    def event(self, command: Command, context: TreeNode | None):
        raise NotImplementedError
    @abstractmethod
    def init(self, buffer: Buffer):
        raise NotImplementedError
    @abstractmethod
    def render(self):
        raise NotImplementedError
    def is_match(self, compare: dict) -> bool:
        raise NotImplementedError
    def focus(self, focus: Literal['normal', 'unfocus', 'focus', 'selected'], depth: int = 1):
        raise NotImplementedError
    def set_buffer(self, buffer: Buffer | None):
        raise NotImplementedError

@runtime_checkable
class TreeNode(_Base_, Protocol):
    _PARENT_: TreeParent | None
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
    def sibling(self, compare: dict | None = None, *_, node: Literal['node'] = 'node') -> TreeNode | None:
        ...
    @overload
    def sibling(self, compare: dict | None = None, *_, node: Literal['parent'] = 'parent') -> TreeParent | None:
        ...
    @overload
    def sibling(self, compare: dict | None = None, *_, node: Literal[''] = '') -> TreeParent | TreeNode | None:
        ...
    def sibling(
        self,
        compare: dict | None = None,
        *_,
        node: Literal['parent', 'node', ''] = ''
    ) -> TreeParent | TreeNode | None:
        _type = (TreeParent, TreeNode)
        if node != '':
            _type = TreeNode if node == 'node' else TreeParent 

        if self._PARENT_ is not None and isinstance(self._PARENT_, TreeParent):
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
        return self._PARENT_
    def __enter__(self):
        ...

@runtime_checkable
class TreeParent(_Base_, Protocol):
    _CHILDREN_: list[TreeNode | TreeParent]

    def __init__(self, *children: TreeNode | TreeParent) -> None:
        self._CHILDREN_ = list(children)
        for child in self._CHILDREN_:
            if isinstance(child, TreeNode):
                child._PARENT_ = self

    @overload
    def child(self, compare: dict | None = None, *_, node: Literal['node'] = 'node') -> TreeNode | None:
        ...
    @overload
    def child(self, compare: dict | None = None, *_, node: Literal['parent'] = 'parent') -> TreeParent | None:
        ...
    @overload
    def child(self, compare: dict | None = None, *_, node: Literal[''] = '') -> TreeParent | TreeNode | None:
        ...
    def child(
        self,
        compare: dict | None = None,
        *_,
        node: Literal['parent', 'node', ''] = '',
    ) -> TreeParent | TreeNode | None:
        _type = (TreeParent, TreeNode)
        if node != '':
            _type = TreeNode if node == 'node' else TreeParent
        children = [child for child in self._CHILDREN_ if isinstance(child, _type)]

        if compare is None:
            return None if len(children) == 0 else children[0]

        for child in children:
            if child.is_match(compare):
                return child
        return None

    def __len__(self) -> int:
        return  len(self._CHILDREN_)

def do_scroll(context: TreeNode, record: Record):
    if record.type == "KEY":
        key = record.key
        if key == "j" or key == "down":
            context.scroll("down")
        elif key == "k" or key == "up":
            context.scroll("up")
        elif key == "h" or key == "left":
            context.scroll("left")
        elif key == "l" or key == "right":
            context.scroll("right")

EventHandler = Callable[[TreeNode, Record], None]
