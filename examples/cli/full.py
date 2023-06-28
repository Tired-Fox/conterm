"""
This example shows how the cli module can be utilized. This is mostly a combination
of the `select` and `tasks` examples. They are just merged with some added continuity.
"""
from time import sleep
from conterm.cli import *
import random

FILE_COUNT = {
    "basic": 5,
    "blog": 10,
    "docs": 15,
}

if __name__ == "__main__":
    name = prompt("project name:")
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

    # new directory
    # copy files
    tasks = TaskManager(
        Spinner(
            prompt=f"Generating project \x1b[36m{name}\x1b[39m",
            target=2
        )
    )
    
    tasks.start()

    # Create new directory
    tasks[0].add(f"Creating directory '{name}/'")
    sleep(1)
    tasks[0].increment()

    # Create Files
    if preset != "":
        tasks[0].add(Spinner(prompt=f"Copying files for preset '{preset}'"))
        sleep(1) # Copy files
        tasks[0].increment()
        tasks[0].task(0).complete = True
    else:
        tasks[0].add(Spinner(prompt=f"Creating blank project structure"))
        sleep(1) # Create sub folders
        tasks[0].increment()
        tasks[0].task(0).complete = True
    tasks[-1].complete = True

    tasks.add(Spinner(prompt="Generating project config"))
    # Create configuration and save to file
    # This mostly includes the additional setup options
    sleep(2)
    tasks[-1].complete = True

    if preset != "":
        # Replicate generating count files based on preset 
        # Random time between completion as files are different sizes
        tasks.add(Spinner(prompt="Building files", target=FILE_COUNT[preset]))
        # Create configuration and save to file
        # This mostly includes the additional setup options
        for _ in range(FILE_COUNT[preset]):
            tasks[-1].increment()
            sleep(random.uniform(0.15, 1.15))

    tasks.stop()
    print(f"\nSuccessfully made the project \x1b[36;1m{name}\x1b[0m!")




