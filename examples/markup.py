from conterm.markup import *
from conterm.markup.preview import rgb_colors, system_colors, xterm_colors

if __name__ == "__main__":
    output = f"""\
[b]System Colors:[/b]
{system_colors(True)}

[b]Xterm Colors:[/b]
{xterm_colors(True)}

[b]RGB Colors:[/b]
{rgb_colors(True)}

[b]Formatting:[/b]
    [i]Styling:[/i]
[b ^full]Bold[/b] [u]underline[/u] [s]strikethrough[/s] [i]italic[/i] \
[bl]blink[/bl] [r]reverse[/r] [~https://exaple.com]Url[/~ /^]

[b u ^full]mix[/b /u i bl] and [/bl /u /i s]match[/ /^]

    [i]Alignment:[/i]
        [<16 red]left just[/<]|[^16 green]center[/^]|[>16 blue]right just[/> /fg]

        Alignment can be based on characters/pixels, percent, or full; Ex:

[^30% magenta]30% centered[>70% cyan]70% right aligned[/fg]

[^100% i b] Everything can be mixed and matched to style how you like
"""

    Markup.print(output)
