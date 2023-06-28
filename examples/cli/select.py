"""
This example shows ways fo getting user input.

Current Options:
    - Prompt: get user input or (yes/no) answer.
        - (yes/no) prompts and with `?`
        - (yes/no) prompts default to yes
        - (yes/no) prompts return (True/False) respectively
        - Normal prompts end with `:` and return a string
    - select: User may select one of many options
        - Can provide a dict where the key is what is displayed and
            A tuple of the (key, value) that was selected is returned
        - Can provide a list of `str`, every item is displayed and the
            selected string is returned
    - multi select: User may select multiple of many options
        - Can provide a dict where the key is what is displayed and
            a dict of all selected options is returned
        - Can provde a list of `str` where every item is displayed and
            a list of selected `str` is returned
        - Multi select can be optional and user can select nothing

Make sure to run it a few times as there are multiple paths
"""
from conterm.cli.select import *

if __name__ == "__main__":
    name = prompt("password:", password=True)
    preset = ""
    theme = ""
    additional = []
    plugins = []
    
    if prompt("use preset?", keep=False):
        preset = select(["basic", "blog", "docs"], prompt="Select a preset:", title="Preset")

    if prompt("Do you want additional setup?", keep=False):
        additional = multi_select(["highlight", "markup"], prompt="Additional setup:", allow_empty=True, title="Setup")

    if "markup" in additional:
        # Cannot be empty. Error is displayed when attempting to submit nothing
        plugins = multi_select(
            ["fenced", "chilite", "fancy"],
            prompt="Select markdown plugins:",
            title="Markdown Plugins"
        )

    if "highlight" in additional:
        # Cannot be empty. Error is displayed when attempting to submit nothing
        theme = select(
            ["one_dark", "dracula", "nord", "gruvbox"],
            prompt="Select Pygmentz theme:",
            title="Pygmentz Theme"
        )

    print("\nSuccessfully made the project!")



