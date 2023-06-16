from winipy.win_api.console import GetConsoleInfo, GetConsoleMode, GetConsoleSize, GetCursorPos, SetConsoleMode, stdout, stdin
from winipy.win_api.input import ReadConsoleInput
from winipy.win_api.structs import KEY_EVENT, ControlKeyState, EventType

if __name__ == "__main__":
    print(GetConsoleInfo(stdout))
    print(GetConsoleSize(stdout))
    print(GetCursorPos(stdout))
# Ctrl
# 1000 
# 0100 

    ENABLE_WINDOW_INPUT = 0x0008
    ENABLE_MOUSE_INPUT = 0x0010
    ENABLE_EXTENDED_FLAGS = 0x0080
    oldMode = GetConsoleMode(stdin)

    if not SetConsoleMode(stdin, ENABLE_EXTENDED_FLAGS | ENABLE_WINDOW_INPUT | ENABLE_MOUSE_INPUT):
        raise Exception("Failed to set console mode")

    for _ in range(10):
        records = ReadConsoleInput()
        if records:
            for record in records:
                print(record.event_type.value)
                key_event = record.event.key_event
                match record.event_type:
                    case EventType.Key:
                        print(f"{key_event}: {key_event.char!r} {key_event.key == 67}")
                        # TODO: Better way of checking key
                        if key_event.char == 'c' and ControlKeyState.is_control(key_event.modifiers):
                            print("LCTRL + C")
                            raise KeyboardInterrupt("user interupt")
                    case EventType.Focus:
                        print(f"Focus Event: {record.event.focus_event}")
                    case EventType.Menu:
                        print("Menu Event")
                    case EventType.Mouse:
                        print(f"{record.event.mouse_event}")
                    case EventType.Resize:
                        print("Window Buffer Size Event")

    if not SetConsoleMode(stdin, oldMode.value):
        raise Exception("Failed to reset console mode")
