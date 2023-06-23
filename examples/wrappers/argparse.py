"""This example shows that you can manually run the click cli with custom cmd."""
from cli import cli
from conterm.wrapper import run_click

if __name__ == "__main__":
    output = run_click(cli, "set")
    if len(output) > 0:
        # Should capture the help command for set
        print("[\x1b[33mOUTPUT\x1b[39m]", output)

    output = run_click(cli, "set client")
    if len(output) > 0:
        # Should capture the print statement in the client method
        print("[\x1b[33mOUTPUT\x1b[39m]", output)
