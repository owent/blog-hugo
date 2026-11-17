"""Sample source file for testing external code file embedding."""

ESCAPES = "<div class=\"demo\">&ampersand;</div>"


def render(tag: str) -> str:
    """Wrap the demo text in an HTML tag."""
    return f"<{tag}>{ESCAPES}</{tag}>"


if __name__ == "__main__":
    for i in range(3):
        print(i, render("em"))
