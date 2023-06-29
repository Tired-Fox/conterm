# Conterm

<!-- Header Badges -->

<div align="center">
  
<img src="assets/badges/version.svg" alt="Version"/>
<a href="https://github.com/Tired-Fox/conterm/releases" alt="Release"><img src="https://img.shields.io/github/v/release/tired-fox/conterm.svg?style=flat-square&color=9cf"/></a>
<a href="https://github.com/Tired-Fox/conterm/blob/main/LICENSE" alt="License"><img src="assets/badges/license.svg"/></a>
<img src="assets/badges/maintained.svg" alt="Maintained"/>
<br>
<img src="assets/badges/tests.svg" alt="Tests"/>
<img src="assets/badges/coverage.svg" alt="Coverage"/>
  
</div>

<!-- End Header -->

Conterm is a simple to use terminal interaction library.
This includes:

- `conterm.control`
  - Keyboard input
  - Mouse input
  - Terminal actions like moving the cursor, deleting lines, etc...
- `conterm.pretty`
  - Pretty printing python objects
  - Simple inline markup for strings
  - Ansi sequence stripping
- `conterm.logging`
  - Simple thread safe logging
- `conterm.cli`
  - Prompts: includes yes/no prompts, hidden password prompts, and normal input prompts
  - Radio Select: List of options are displayed and the user can select one of many options.
  - Multi Select: List of options are displayed and the user can select multiple of many options.
  - Task Manager: This is a thread safe object that prints and updates a region in the terminal over time. When it is active no other printing to stdout should occur. The task manager lets you add messages, spinners, and progress bars with intuitive ways of updating progress over time.

With all the above features in mind, make sure to check out the [examples](./examples/) to see the different
features in action.

> note: This library is experimental and a work in progress. Any and all feedback is welcome.

<!-- Footer Badges --!>

<br>
<div align="center">
  <img src="assets/badges/made_with_python.svg" alt="Made with python"/>
  <img src="assets/badges/built_with_love.svg" alt="Built with love"/>
</div>

<!-- End Footer -->
