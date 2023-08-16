from conterm.control import Event, Key, Listener, Mouse, eprint
from conterm.control.actions import set_title


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

    # How to filter
    # Checks if specific event did/didn't occured (__contains__)
    if Event.MOVE not in event:
        eprint(event)


    # Can check if one of many events occured in the mouse event
    # Can also check for a specific mouse button
    # (__eq__)

    # String matching works for events. Event can be in one of many split by `:`
    # d: drag, dl: drag left, dm: drag middle, dr: drag right, m: move, r: release, c: click
    # `c:r:m:d:dl:dr:dm`

    # String matching also works for mouse buttons. The events button must be one of many split by `:`.
    # l: left, m: middle, r: right
    # Ex. `l:m:r`

    # if event == "c:r" and event.button == "l:r":
    #     eprint(event)
    #
    #   Is equal too
    #
    # if event.event_of(Event.CLICK, Event.RELEASE) and event.button in [Button.LEFT, Button.RIGHT]:
    #     eprint(event)


if __name__ == "__main__":
    set_title("Controls Example")

    print("Enter any keyboard or mouse event to see it below:")

    # Can start an event loop and listen until keyboard interrupt / exit
    with Listener(on_key, on_mouse) as listener:
        listener.join()

    # Can also just start the listener and do other tasks in the main thread
    #     input_listener = Listener(on_key, on_mouse)
    #     input_listener.start()

    # Don't forget to stop the thread when you don't need input.
    # The thread is a daemon thread so if the program exits so will the thread
    #     input_listener.stop()
