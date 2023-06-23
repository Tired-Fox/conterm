import click
from conterm.wrapper import run_cli

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
    output = run_cli("set")
    if len(output) > 0:
        print("OUTPUT:", output)
    output = run_cli("set client")
    if len(output) > 0:
        print("OUTPUT:", output)
