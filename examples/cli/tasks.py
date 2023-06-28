"""
This example shows how a TaskManager can use spinners and progress bars to
display the progress of different tasks. The TaskManager is a Thread object
and all calls to methods on Spinners, Progress, and TaskManager are thread safe.

To display how it is thread safe the progress bars are updated in seperate threads
independant of all other tasks.

Sleep is used to act as if something that tasks time is occuring
"""
from threading import Thread
from conterm.cli import TaskManager, Spinner, Progress, Icons
from time import sleep

def increment(progress: Progress, duration: float):
    while not progress.complete:
        progress.increment()
        sleep(duration)

if __name__ == "__main__":
    tman = TaskManager(Spinner(prompt="Some Prompt", rate=0.25))
    tman.start()

    sleep(1)

    # Add a subtask to the Spinner in TaskManager
    tman[0].add("Making new directory")

    sleep(1)

    # Add a subtask to the Spinner in TaskManager
    tman[0].add("Copying files")

    sleep(1)

    # Create a spinner that contains a progress count with 3 progress bar subtasks
    progress = Spinner(
        Progress(prompt="Making directories", target=5),
        Progress(prompt="Copying files", target=3),
        Progress(prompt="Cleaning up", target=7),
        prompt="Setting up file system",
        # Target finish total for the spinners progress. This is used with `increment`
        target=3,
        icons=Icons.STACK
    )

    # Add the new spinner to the first spinner in TaskManager as a subtask
    tman[0].add(progress)

    # Create and start threads that increment the 3 progress bars by different durations
    threads = [
        Thread(target=increment, args=(progress.task(0), 0.5), daemon=True),
        Thread(target=increment, args=(progress.task(1), 1), daemon=True),
        Thread(target=increment, args=(progress.task(2), 1.5), daemon=True),
    ]
    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # Manually set a task, spinners without progress, to be complete.
    # This is entirely cosmetic but will stop annimating the spinner icon and
    # will color the icon green
    tman[0].complete = True

    # Thread is now stopped and TaskManager can no longer be used
    tman.stop()
