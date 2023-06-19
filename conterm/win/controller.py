from conterm.win.input import Event


class Controller:
    def __init__(self):
        alive = True

    def input(self) -> Iterator[Event]:
        while True:
            records = _ReadInput()
            if records:
                for record in records:
                    yield Event(record)

    def __enter__(self):
        print("Enter context")

    def __exit__(self, *args, **kwargs):
        print("Exit context:", args, kwargs)
