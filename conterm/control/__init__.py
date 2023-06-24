"""Python terminal input.

Right now the input is focused around ansi codes. In the future a more low level
approach may be implemented for more fine tuned control. The idea around this would
be something similar to [pynput](https://github.com/moses-palmer/pynput). Pynput
uses platform specific API's to read keyboard and mouse input for the console. Ex: Win32's
`ReadConsoleInput`.

When the above portion is implemented the input module will be split into the new `raw` module
and the current 'ansi' module.
"""

# TODO: Detect ansi support with \x1b[6n and getting back \x1b[\d;\dR

# Import ansi module as base logic for input
# This is only until raw input is implemented 
from .ansi import *
