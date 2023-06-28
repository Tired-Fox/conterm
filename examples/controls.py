from conterm.control import Key, Mouse, Event, Button, Listener, eprint, keys
from conterm.control.ansi.actions import set_title

def on_key(event: Key, _) -> bool | None:
    """Handler for key events."""
    match event:
        case "ctrl+alt+d":
            return False
    eprint(event)

def on_mouse(event: Mouse, _) -> bool | None:
    """Handler for mouse events."""
    if Event.DRAG_MIDDLE_CLICK:
        eprint(event)
    elif (
        event.event_of(Event.CLICK, Event.RELEASE)
        and event.button == Button.RIGHT
    ):
        eprint(event)

if __name__ == "__main__":
    set_title("Controls Example")

    # Can build a key code from a chord.
    # The code is only valid key codes returns none if it can't
    # generate a valid code.
    print(repr(keys.by_chord("alt+S")))

    # Can start an event loop
    with Listener(on_key, on_mouse) as listener:
        listener.join()
