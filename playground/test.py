from conterm.input import watch
from conterm.input.keys import KEY

if __name__ == "__main__":

    # Can build a key code from a chord.
    # The code is only valid key codes returns none if it can't
    # generate a valid code.
    print(repr(KEY.by_chord("alt+S")))

    for record in watch(False):
        print(repr(record))
        if record == "KEY":
            # Can compare key events with strings
            if record.event == "ctrl+alt+d":
                print("Exit")
                exit(3)
