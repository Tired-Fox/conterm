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

    pprint(
        "[b]List:",
        ["Hello", 3, 123.456, ["data"], None],
        sep="\n",
        end="\n\n",
    )
    pprint(
        "[b]Dict:",
        {"key": Something, "second": 3, "third": set([something, Something])},
        sep="\n",
        theme=NORD
    )
    pprint(
        {"key": Something, "second": 3, "third": set([something, Something])},
        sep="\n",
        theme=DRACULA
    )
    pprint(
        {"key": Something, "second": 3, "third": set([something, Something])},
        sep="\n",
        end="\n\n",
        theme=GRUVBOX
    )
    pprint(
        {"key": Something, "second": 3, "third": set([something, Something])},
        sep="\n",
        end="\n\n",
        theme=Catpuccin.MOCHA
    )
