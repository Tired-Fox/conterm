import click
from conterm.wrapper import run_click

@click.group()
def cli():
    """A test cli tool."""

@cli.group("set")
def set_env():
    """Set program environment variables."""

@set_env.command()
def client():
    """Set the programs client."""
    print("set client")

@set_env.command()
def database():
    """Set the programs database."""
    print("set database")

if __name__ == "__main__":
    output = run_click(cli, "set")
    if len(output) > 0:
        # Should capture the help command for set
        print("[\x1b[33mOUTPUT\x1b[39m]", output)

    output = run_click(cli, "set client")
    if len(output) > 0:
        # Should capture the print statement in the client method
        print("[\x1b[33mOUTPUT\x1b[39m]", output)
