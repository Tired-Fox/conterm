from conterm.keys import KeyCode
from conterm.win import Controller
from conterm.win.console import GetConsoleInfo, GetConsoleSize, GetCursorPos, stdout
from conterm.win.input import Key, Modifiers, Mouse, ReadInput
from conterm.win.structs import KEY_EVENT, EventType

if __name__ == "__main__":
    print(GetConsoleInfo(stdout))
    print(GetConsoleSize(stdout))
    print(GetCursorPos(stdout))

    modifiers: Modifiers = {"shift": False, "ctrl" : False, "alt": False}

    with Controller() as input:
        for key in input:
            pass

    for event in ReadInput():
        match event.event_type:
            case EventType.Key:
                if event.key.is_ascii:
                    print(event.key)

                # ctrl+c or ctrl+C
                if event.key.ctrl and event.key.char.lower() == "c":
                    raise KeyboardInterrupt("user interupt")

            case EventType.Mouse:
                if not event.mouse.is_event(Mouse.Event.Moved) and event.mouse.pressed(Mouse.Button.Left):
                    print(f"Left Mouse Click: {event.mouse}")
            # case EventType.Menu:
            #     print("Menu Event")
            # case EventType.Focus:
            #     print(f"{event.Focus}")
            # case EventType.Resize:
            #     print("Window Buffer Size Event")
