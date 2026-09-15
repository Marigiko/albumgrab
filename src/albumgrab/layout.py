"""Path layout and cross-platform filename sanitization (Slice 1 pure module).

``sanitize_segment`` is invariant-pinned (see tests/unit/test_layout.py): no
invalid/control chars, non-reserved, <= MAX_SEGMENT_LENGTH, no trailing
dot/space, never empty. ``ensure_album_dir`` is the module's only I/O.
"""

from __future__ import annotations

from pathlib import Path

MAX_SEGMENT_LENGTH = 120

# Windows-forbidden characters plus the DOS reserved device names.
_INVALID_CHARS = set('<>:"/\\|?*')
_RESERVED_NAMES = (
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)


def sanitize_segment(name: str) -> str:
    """Make one path segment (artist, album, or track) cross-platform safe."""
    segment = "".join(
        "_" if char in _INVALID_CHARS or ord(char) < 32 or ord(char) == 127 else char
        for char in name
    )
    segment = segment[:MAX_SEGMENT_LENGTH].rstrip(" .")
    if segment.upper() in _RESERVED_NAMES:
        segment = segment[: MAX_SEGMENT_LENGTH - 1] + "_"
    return segment or "untitled"


def build_track_path(
    root: Path, artist: str, album: str, track_number: int, title: str
) -> Path:
    """Build ``{root}/{artist}/{album}/{NN - track}.mp3``.

    Only the artist/album/title text is sanitized; the zero-padded ``NN``
    prefix and the ``.mp3`` extension are constructed here and never altered.
    """
    filename = f"{track_number:02d} - {sanitize_segment(title)}.mp3"
    return root / sanitize_segment(artist) / sanitize_segment(album) / filename


def ensure_album_dir(album_dir: Path) -> Path:
    """Create the album directory (and parents) on demand; idempotent."""
    album_dir.mkdir(parents=True, exist_ok=True)
    return album_dir
