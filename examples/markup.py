from conterm.control.ansi.actions import set_title
from conterm.pretty import Markup
from conterm.pretty.markup.preview import rgb_colors, system_colors, xterm_colors


if __name__ == "__main__":
    set_title("Markup Example")

    Markup.print(f"""\
[b]System Colors:[/b]
{system_colors()}

[b]Xterm Colors:[/b]
{xterm_colors()}

[b]RGB/Hex Colors:[/b]
{rgb_colors()}

[b]Formatting:[/b] [i]italic[/i] [b]bold[/b] [u]underline[/u] [s]strikethrough[/s] \
[bl]blink[/bl] [r]reversed[/r] [~https://example.com]url[/]

[b]Alignment:[/b]
    [i]- <,^,> specifies alignment. Must include width for it to align[/i]
        [<16 red]Left[/]|[^16 green]centered[/]|[>16 blue]Right[/]


    [i]- pixel/char width, full width, or % width[/i]
[^30% magenta]center aligned 30%[^70% cyan]Center aligned 70%[/]

[^full red]Full width[/]
""")
