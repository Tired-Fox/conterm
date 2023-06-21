from conterm.input import InputManager, Mouse, KEY, eprint
from conterm.input.keys import sys

Event = Mouse.Event
Button = Mouse.Button

if __name__ == "__main__":
    # Can build a key code from a chord.
    # The code is only valid key codes returns none if it can't
    # generate a valid code.
    print(repr(KEY.by_chord("alt+S")))

    for record in InputManager().watch(False, True):
        if record == "KEY":
            # Can compare key events with strings
            if record.key == "ctrl+alt+d":
                print("Exit")
                sys.exit(3)
            eprint(record.key)
        elif record == "MOUSE":
            mouse = record.mouse
            if Event.DRAG_MIDDLE_CLICK in mouse:
                eprint(mouse)
            elif (
                mouse.event_of(Event.CLICK, Event.RELEASE)
                and mouse.button == Button.RIGHT
            ):
                eprint(record.mouse)
