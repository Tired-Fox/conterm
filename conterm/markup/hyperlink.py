class Hyperlink:
    """Helper class for building hyperlink in terminal terminals."""

    close = "\x1b]8;;\x1b\\"
    """Get the closer for a hypertext link."""

    @staticmethod
    def open(link: str) -> str:
        """Create the opening to a hypertext link."""
        return f"\x1b]8;;{link}\x1b\\"
