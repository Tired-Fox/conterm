import re


class Hyperlink:
    """Helper class for building hyperlink in terminal terminals."""

    close = "\x1b]8;;\x1b\\"
    """Get the closer for a hypertext link."""

    @staticmethod
    def open(link: str) -> str:
        """Create the opening to a hypertext link."""
        return f"\x1b]8;;{link}\x1b\\"

def strip_ansi(ansi: str = ""):
    """Strip ansi code from a string."""

    # First check for control sequences. This covers most sequences, but some may slip through
    # Then check for Link opening and closing tags: \x1b]8;;<link>\x1b\ or \x1b]8;;\x1b\
    # Finally check for any raw characters like \x04 == ctrl+d
    return re.sub(
        r"\x1b\[[<?]?(?:(?:\d{1,3};?)*)[a-zA-Z~]|\x1b]\d;;[^\x1b]*\x1b\\|[\x00-\x1B]",
        "",
        ansi,
    )
