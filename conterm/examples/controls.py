from conterm.control import Button, Event, Key, Listener, Mouse, eprint, keys
from conterm.control.ansi.actions import set_title


def on_key(event: Key, _) -> bool | None:
    """Handler for key events."""
    if event == "ctrl+alt+d":
        # Return false to exit event listener
        return False
    eprint(event)

    # Can use match statments with string chord comparison
    # match event:
    #     case "ctrl+alt+d":
    #         return False


def on_mouse(event: Mouse, _) -> bool | None:
    """Handler for mouse events."""
    # Can check if an event occured in the mouse event
    # note: Event.Drag is in the mouse event if any of the specific drag events are specified 
    if Event.DRAG_MIDDLE_CLICK in event:
        eprint(event)
    # Can check if one of many events occured in the mouse event
    # Can also check for a specific mouse button
    elif event.event_of(Event.CLICK, Event.RELEASE) and event.button == Button.RIGHT:
        eprint(event)


if __name__ == "__main__":
    set_title("Controls Example")

    print("Enter any keyboard or right click/middle drag event to see it below:")

    # Can start an event loop and listen until keyboard interrupt / exit
    with Listener(on_key, on_mouse) as listener:
        listener.join()

    # Can also just start the listener and do other tasks in the main thread
    #     input_listener = Listener(on_key, on_mouse)
    #     input_listener.start()

    # Don't forget to stop the thread when you don't need input.
    # The thread is a daemon thread so if the program exits so will the thread
    #     input_listener.stop()
