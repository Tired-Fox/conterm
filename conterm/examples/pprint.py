from conterm.control.ansi.actions import set_title
from conterm.pretty import pprint
from conterm.pretty.themes import DRACULA, GRUVBOX, NORD, Catpuccin

class Something:
    pass

def something():
    pass

if __name__ == "__main__":
    set_title("Pretty Print Example")

    # Themes can also be manually created.
    # They use a dict of the format:
    # class Theme(TypedDict):
    #     keyword: str
    #     object: str
    #     string: str
    #     number: str
    #     comment: str
    pprint("[b]Regular [/b u]Strings[/] [s]are[/s i] treated as [red]Markup",)

    pprint(
        "[b cyan]Pretty print collection types: list, tuple, set, etc...",
        ["Hello", 3, 123.456, ("tuple",), None, {"set"}],
        sep="\n",
        end="\n\n",
    )
    pprint(
        "[b cyan]Pretty print dict:",
        {"key": Something, "second": 3, "third": set([something, Something])},
        sep="\n",
    )

    pprint("[b cyan]Pretty print with themes")
    pprint(
        "[b]OneDark (default):",
        {"key": Something, "second": 3, "third": set([something, Something])},
        sep="\n",
    )
    pprint(
        "[b]Nord:",
        {"key": Something, "second": 3, "third": set([something, Something])},
        sep="\n",
        theme=NORD,
    )
    pprint(
        "[b]Dracula:",
        {"key": Something, "second": 3, "third": set([something, Something])},
        sep="\n",
        theme=DRACULA
    )
    pprint(
        "[b]Gruvbox:",
        {"key": Something, "second": 3, "third": set([something, Something])},
        sep="\n",
        end="\n\n",
        theme=GRUVBOX
    )
    pprint(
        "[b]Catpuccin (Mocha):",
        {"key": Something, "second": 3, "third": set([something, Something])},
        sep="\n",
        end="\n\n",
        theme=Catpuccin.MOCHA
    )

    pprint(
        "[b]Create your own (Monokai):",
        {"key": Something, "second": 3, "third": set([something, Something])},
        sep="\n",
        end="\n\n",
        theme={
            "keyword": "120,220,232",
            "object": "169,220,118",
            "string": "255,216,102",
            "number": "171,157,242",
            "comment": "88,86,91",
        }
    )
