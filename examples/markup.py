from conterm.printing import Markup
from conterm.printing.markup.preview import rgb_colors, system_colors, xterm_colors


if __name__ == "__main__":
    Markup.print(f"""\
[b]System Colors:[/b]
{system_colors(True)}

[b]Xterm Colors:[/b]
{xterm_colors(True)}

[b]RGB/Hex Colors:[/b]
{rgb_colors(True)}

[b]Formatting:[/b] [i]italic[/i] [b]bold[/b] [u]underline[/u] [s]strikethrough[/s] \
[bl]blink[/bl] [r]reversed[/r] [~https://example.com]url[/]

[b]Alignment:[/b]
    [i]- <,^,> specifies alignment. Must include width for it to align[/i]
        [<16 red]Left[/]|[^16 green]centered[/]|[>16 blue]Right[/]


    [i]- pixel/char width, full width, or % width[/i]
[^30% magenta]center aligned 30%[^70% cyan]Center aligned 70%[/]

[^full red]Full width[/]
""")
