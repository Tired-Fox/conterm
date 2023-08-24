"""
Mini module for creating tui applications. This library is fairly simple.
If more complex features are desired please see other Tui libraries.
"""
from __future__ import annotations
from math import floor
from random import randrange
from time import sleep
from conterm.control.event import Record
from conterm.tui.application import Application, TreeNode

from conterm.tui.buffer import Buffer
from conterm.tui.node import Node, Settings

def void(*_, **__):
    """Void method that takes anything and returns nothing."""
    pass

def __over_time__():
    buffer = Buffer()

    settings = Settings(border=True, border_color="cyan", text_align="end", align_items="end")
    node = Node(buffer=buffer, pos=(0.25, 0.25), size=(0.5, 0.5), settings=settings)

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
        node.settings.border_color = randrange(0, 256)

        # Render the node into the buffer
        node.render()

        # Write the buffer to stdout
        buffer.write()
        sleep(0.25)


def __standard__():
    buffer = Buffer()

    settings = Settings(
        border=True, border_color="cyan", text_align="center", align_items="center"
    )
    node = Node(buffer=buffer, size=(1.0, 1.0), settings=settings, title="Test Node")
    node.write("[red]Hello, [green]world[/]!")
    node.render()
    buffer.write()


def __multiple__():
    buffer = Buffer()

    settings1 = Settings(
        border=True,
        border_color="cyan",
        # top, left, bottom, right
        border_edges=("dashed", "dotted", "single", "single"),
        # tl, tr, br, bl
        border_corners=("single", "rounded", "single", "rounded"),
        text_align="end",
        align_items="end",
    )

    settings2 = settings1.copy()
    settings2.border_color = "yellow"
    settings2.border_edges = ("dashed", "dotted", "double", "single")
    settings2.border_corners = ("single", "rounded", "double", "double")
    settings2.text_align = "center"
    settings2.align_items = "center"

    settings3 = settings2.copy()
    settings3.border_color = "green"
    settings3.text_align = "start"
    settings3.align_items = "start"

    node1 = Node(buffer=buffer, size=(0.33, 0.25), settings=settings1, title="Node 1")
    node1.write("Hello, node 1!")
    node2 = Node(buffer=buffer, pos=(0.33, 0), size=(0.66, 1.0), settings=settings2, title="Node 2")
    node2.write("Hello, node 2!")
    node3 = Node(buffer=buffer, pos=(0, 0.25), size=(0.33, 0.75), settings=settings3, title="Node 3")
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
            settings=Settings(
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
                        context.scroll("down")
                    elif key == "k" or key == "up":
                        context.set("title", "up")
                        context.scroll("up")
                    if key == "h" or key == "left":
                        context.set("title", "left")
                        context.scroll("left")
                    elif key == "l" or key == "right":
                        context.set("title", "right")
                        context.scroll("right")
                    elif key == "enter":
                        message = context.sibling({"id": "message"})
                        if message is not None:
                            message.clear()
                            message.write(f"{context.get_scroll()[1]}: selected")

            selector.handler = handler
            for i in range(20):
                selector.write(f"{i}: Sample text {'-' * 5}\n  preserve newline")

        app.context(
            id="message",
            pos=(0, 10),
            size=(20, 3),
            settings=Settings(border = True)
        )

def __applicaiton__():
    def update(dt: float, app: Application):
        total = app.state.get('total', float((8*60)+35))
        prgs = app.state.get('progress', 0.0)
        if (playing := app.find({'id': 'playing'})) is not None:
            message = f'Hi Ren ~ Ren ({int(prgs)//60}:{str(int(prgs)%60).rjust(2, "0")}/{int(total)//60}:{str(int(total)%60).rjust(2, "0")})'
            
            playing.clear()
            step = playing.width / total
            progress = min(round((prgs+dt) * step), playing.width)
            missing = playing.width - progress

            playing.write(message)
            playing.format(f"[green]{'█'*progress}[/]{'░'*missing}")
        app.state.set('progress', (prgs + dt) % total)

    with Application() as app:
        app.set_update(update)
        with app.section(size=(1.0, lambda mx: mx-4)) as top:
            with top.section(size=(0.3, 1.0)) as left:
                with left.context(
                    id="titlebar",
                    size=(1.0, 0.3),
                    settings=Settings(
                        text_align='center',
                        align_items='center',
                        overflow=('wrap', 'hidden'),
                        border_color="red"
                    ),
                ) as titlebar:
                    titlebar.write("Hello World")

                with left.context(
                    id="playlists",
                    title="Playlists",
                    pos=(0, 0.3),
                    size=(1.0, 0.9),
                    settings=Settings(overflow="scroll", padding=(1, 0)),
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
            settings=Settings(align_items="center", overflow='hidden', padding=(1, 0)),
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
    with open("log.txt", "+w", encoding="utf-8") as log:
        try:
            __applicaiton__()
            # ctx = Context(Node(id='playing'))
            # print(ctx.is_match({'id': 'playing'}))
        finally:
            pass

