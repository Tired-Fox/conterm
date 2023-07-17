from pathlib import Path
from subprocess import run
import sys
import click

from conterm.pretty.markup import Markup

@click.group()
def cli():
    """Mini cli helper for examples and the playground."""

@click.argument(
    "example",
    default=None,
)
@cli.command(help="""\
Run a specific conterm functionality example.

\x1b[1mExample Options:\x1b[22m

- \x1b[1;36mmarkup\x1b[39;22m   :Prints examples of using the markup module to the terminal\n
- \x1b[1;36mpprint\x1b[39;22m   :Pretty prints structures to the terminal with different themes\n
- \x1b[1;36mtasks\x1b[39;22m    :Simulates running tasks and updating the terminal with the progress. This example takes time as it simulates running tasks.\n
- \x1b[1;36mselect\x1b[39;22m   :Simulates getting user input with specifal input objects.\n
- \x1b[1;36mlogging\x1b[39;22m  :Simulates using a logger. This isn't meant to be complex. Just a simple and easy to use logging object.\n
- \x1b[1;36mcontrols\x1b[39;22m :Collects user input and prints the results to the screen. This includes mouse input.
""")
def examples(example: str | None = None):
    """Run a specific conterm functionality example.

    """

    examples_root = Path(__file__).parent.joinpath("examples")
    name =  ""

    if example == "list":
        print("""\
\x1b[1mExample Optioins:\x1b[22m
    \x1b[1;36mmarkup\x1b[39;22m   :Prints examples of using the markup module to the terminal
    \x1b[1;36mpprint\x1b[39;22m   :Pretty prints structures to the terminal with different themes
    \x1b[1;36mtasks\x1b[39;22m    :Simulates running tasks and updating the terminal with the progress. This example takes time as it simulates running tasks.
    \x1b[1;36mselect\x1b[39;22m   :Simulates getting user input with specifal input objects.
    \x1b[1;36mlogging\x1b[39;22m  :Simulates using a logger. This isn't meant to be complex. Just a simple and easy to use logging object.
    \x1b[1;36mcontrols\x1b[39;22m :Collects user input and prints the results to the screen. This includes mouse input.
""")
        sys.exit(0)
    elif example == "markup":
        name = "markup.py"
    elif example == "pprint":
        name = "pprint.py"
    elif example == "tasks":
        name = "cli/tasks.py"
    elif example == "select":
        name = "cli/select.py"
    elif example == "logging":
        name = "logging.py"
    elif example == "controls":
        name = "controls.py"

    if name == "":
        print(f"Unkown example {example!r}")
        sys.exit(1)

    run(f"python {(examples_root / name).resolve()}")

@cli.command
def markup():
    """Markup shell that takes markup as input and ouputs the result."""
    try:
        while True:
            Markup.print(input("{conterm.markup} "))
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    cli()
