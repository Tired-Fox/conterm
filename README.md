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

### Markup

This should be an easy to use familiar syntax. `b`, `i`, `u`, `s` equal bold, italic, underline and strikethrough respectively. `~<url>` represents a hyperlink. `<`, `^`, `>` represent left, center and right align respectively as long as a total width is also provided. Additionally, conterm allows the user to define their own macros that can either generate text or modify text. The custom macros are called outright like builtin macros which allows for macro overloading. There can be multiple macros per block seperated by a space and each macro is persistant until they are closed with a `/`. All system colors are supported by name. There is also hex, xterm, and rgb support. By default the color is for the foreground, but if it is prefixed with `@` it will be applied to the background.

**Examples**

```
[b i]Bold italic[/b] just italic [/i] normal text
```
```
[u s]Underlined and strikethrough[/] normal text
```
```
[^30]30 char center aligned[<70%]Closes previous alignment and starts this one
[^full]Can use percentages and full keyword; full == 100%
```
```
[~http://example.com]Example Url [~http://example.com]Another url[/~]
```
```
[red]Red text [@white] now with white background[/fg /bg]

[#f32]Red text [@243] grey background[/]

[100,15,100]RGB colored text[/]
```

<!-- Footer Badges --!>

<br>
<div align="center">
  <img src="assets/badges/made_with_python.svg" alt="Made with python"/>
  <img src="assets/badges/built_with_love.svg" alt="Built with love"/>
</div>

<!-- End Footer -->
