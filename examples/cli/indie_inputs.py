from time import sleep

from conterm.cli.select import *
from conterm.cli.spinner import Spinner

if __name__ == "__main__":
    name = prompt("project name:")
    preset = ""
    if prompt("use preset?", yes_no=True, keep=False):
        preset = select(["basic", "blog", "docs"], prompt="Preset:")

    loading = Spinner.dots(Markup.parse(f"Generating project [cyan b]{name}"))
    loading.start()

    # # Do tasks
    for task in ["Making directory", "Making folders", "Copying Files"]:
        loading.print(f"  {task}")
        sleep(2)
    loading.print("  Final preperations")

    loading.stop()
    loading2 = Spinner.arrow(Markup.parse(f"Generating project [cyan b]{name}"))
    loading2.start()
    sleep(6)
    loading2.stop()
    print("\nSuccessfully made the project!")



