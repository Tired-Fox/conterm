from conterm.win_api.console import GetConsoleInfo, GetConsoleSize, GetCursorPos, stdout
from conterm.win_api.input import Key, Modifiers, ReadInput
from conterm.win_api.structs import KEY_EVENT, ControlKeyState, EventType

if __name__ == "__main__":
    print(GetConsoleInfo(stdout))
    print(GetConsoleSize(stdout))
    print(GetCursorPos(stdout))

    modifiers: Modifiers = {"shift": False, "ctrl" : False, "alt": False}

    for event in ReadInput():
        match event.event_type:
            case EventType.Key:
                key = Key(event.event.key_event, modifiers)
                if key.is_ascii:
                    print(key)

                if key.ctrl and key.char.lower() == "c":
                    raise KeyboardInterrupt("user interupt")

            case EventType.Focus:
                print(f"Focus Event: {event.event.focus_event}")
            case EventType.Menu:
                print("Menu Event")
            case EventType.Mouse:
                print(f"{event.event.mouse_event}")
            case EventType.Resize:
                print("Window Buffer Size Event")
