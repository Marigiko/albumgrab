"""Album selection parsing (Slice 2 pure module).

Parses one line of numbered multi-select input (``"1,3-5"``, ``"all"``) into
the sorted, de-duplicated union of 1-based album indices. Invalid input
raises :class:`InvalidSelection` naming the offending token; ``cli.py`` owns
the catch/re-prompt loop (design: selection re-prompt loop owner).
"""

from __future__ import annotations


class InvalidSelection(Exception):
    """Raised when selection input contains an invalid token."""

    def __init__(self, token: str) -> None:
        self.token = token
        super().__init__(f"invalid selection token: {token!r}")


def parse_selection(raw: str, count: int) -> list[int]:
    """Parse ``raw`` into the sorted union of selected indices in ``1..count``.

    Accepts comma-separated single numbers and inclusive ranges (``"2-5"``);
    the ``"all"`` keyword (case-insensitive) selects every album. Duplicates
    collapse to a single selection. Any malformed, out-of-range, or inverted
    token raises :class:`InvalidSelection`.
    """
    stripped = raw.strip()
    if not stripped:
        raise InvalidSelection(raw)
    if stripped.lower() == "all":
        return list(range(1, count + 1))
    selected: set[int] = set()
    for part in stripped.split(","):
        token = part.strip()
        if "-" in token:
            selected.update(_parse_range(token, count))
        else:
            selected.add(_bounded_number(token, token, count))
    return sorted(selected)


def _parse_range(token: str, count: int) -> range:
    """Parse one inclusive ``"start-end"`` token; bounds validated."""
    start_text, _, end_text = token.partition("-")
    start = _number(start_text, token)
    end = _number(end_text, token)
    if not 1 <= start <= end <= count:
        raise InvalidSelection(token)
    return range(start, end + 1)


def _bounded_number(token: str, context: str, count: int) -> int:
    """Parse one plain number token; must be within ``1..count``."""
    number = _number(token, context)
    if not 1 <= number <= count:
        raise InvalidSelection(context)
    return number


def _number(text: str, context: str) -> int:
    """Parse a non-negative integer token; anything else is invalid."""
    if not text.isdigit():
        raise InvalidSelection(context)
    return int(text)
