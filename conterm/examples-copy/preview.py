def xterm_colors() -> str:
    """Generate a xterm color table using the markup module.

    Returns:
        Markup of xterm colors
    """

    output = "[^full]"
    for i in range(8):
        output += f"[{i}]▀"
    output += "    " 
    for i in range(8, 16):
        output += f"[{i}]▀"

    output += "[^full]"
    for color in range(23):
        output += f"[{232 + color} @{min(232 + color + 1, 255)}]▀"
    output += "[/]\n\n"

    cursor = 16
    output += "[^full]"
    for _ in range(1, 4):
        for column in range(37):
            if column == 36:
                continue
            output += f"[{cursor + column} @{cursor + column + 36}]▀"
        output += "[/]\n[^full]"
        cursor += 72
        if cursor > 232:
            break
    output += "[/]"

    return output

def system_colors() -> str:
    """Generate a system color table using the markup module.

    Returns:
        Markup of system colors
    """
    output = ("[^full black @white]black[red /bg] red [green]green [yellow]yellow[/^]\n"
    + "[^full blue]blue [magenta]magenta [cyan]cyan [white]white[/]")

    return output

def rgb_colors() -> str:
    """Generate a rgb color table using the markup module.
    Returns:
        Markup of rgb color
    """
    #     g
    # r < ^ > b
    red = 255
    blue = 0
    green = 0

    width = 45 
    height = width // 2

    step = 255 // width
    output = "[^full]"

    for _ in range(height):
        for _ in range(width):
            red -= step
            blue += step
            output += f"[{red},{green},{blue} @{red},{green+step},{blue}]▀"
        output += "[/]\n[^full]"
        red = 255
        blue = 0
        green += step * 2
    output += "[/]"

    return output
