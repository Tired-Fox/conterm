from time import sleep
from conterm.cli.spinner import Spinner
from conterm.cli.select import *

if __name__ == "__main__":
    name = prompt("project name:")
    preset = ""
    if prompt("use preset?", yes_no=True, keep=False):
        preset = select(["basic", "blog", "docs"], prompt="Preset:")

    loading = Spinner.dots(Markup.parse(f"Generating project [cyan b]{name}"), static=True)
    loading.start()

    # Do tasks
    for task in ["Making directory", "Making folders", "Copying Files"]:
        print(f"  {task}")
        sleep(2)

    loading.stop()
    print("\nSuccessfully made the project!")



