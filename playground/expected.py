
from conterm.win import Controller
from conterm.win.input import Event
from conterm.win_api.structs import EventType


if __name__ == "__main__":
    controller = Controller()
    for input in controller.input():
        match controller.input():
            case Event(EventType.Mouse, event):
                print(event)
            case Event(EventType.Key, event):
                print(event)
