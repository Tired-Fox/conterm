"""This is a click cli script. Can be run by itself for command line interface.
Can also call the entry point `cli` with `run_click` passing `cli` and a custom
command to manually run the click command line.
"""

import click

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
    cli()
