"""Invariant-pinned tests for albumgrab.layout (library-layout scenarios L1-L5).

The sanitizer invariant from design.md is asserted as a property (segment
non-empty, no invalid/control chars, non-reserved, <= cap, no trailing
dot/space) rather than by exact literal output.
"""

from pathlib import Path

from albumgrab.layout import (
    MAX_SEGMENT_LENGTH,
    build_track_path,
    ensure_album_dir,
    sanitize_segment,
)

INVALID = set('<>:"/\\|?*')
RESERVED = (
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)


def assert_invariant(segment: str) -> None:
    assert segment, "segment must be non-empty"
    assert len(segment) <= MAX_SEGMENT_LENGTH
    assert not set(segment) & INVALID
    assert not any(ord(c) < 32 or ord(c) == 127 for c in segment)
    assert segment.upper() not in RESERVED
    assert not segment.endswith((" ", "."))


def test_invalid_chars_and_control_chars_replaced() -> None:
    assert sanitize_segment("a?b:c") == "a_b_c"
    assert sanitize_segment("AC/DC: Greatest\\Hits") == "AC_DC_ Greatest_Hits"
    assert sanitize_segment("Back\x07space\nNew") == "Back_space_New"


def test_non_ascii_letters_are_preserved() -> None:
    assert sanitize_segment("Café Tacvba") == "Café Tacvba"
    assert sanitize_segment("Sigur Rós") == "Sigur Rós"


def test_invalid_chars_result_is_writable(tmp_path: Path) -> None:
    path = build_track_path(tmp_path, "Artist", "Album", 1, "Who?Made:Who")
    ensure_album_dir(path.parent)
    path.write_bytes(b"")
    assert path.is_file()


def test_reserved_names_suffixed_case_insensitively() -> None:
    assert sanitize_segment("CON") == "CON_"
    assert sanitize_segment("con") == "con_"
    assert sanitize_segment("Lpt1") == "Lpt1_"


def test_overlong_segment_truncated_to_cap() -> None:
    segment = sanitize_segment("L" * 300)
    assert len(segment) == MAX_SEGMENT_LENGTH
    assert_invariant(segment)


def test_overlong_segment_still_writable(tmp_path: Path) -> None:
    path = build_track_path(tmp_path, "Artist", "Album", 1, "L" * 300)
    ensure_album_dir(path.parent)
    path.write_bytes(b"")
    assert path.is_file()


def test_reserved_name_after_truncation_still_safe() -> None:
    assert_invariant(sanitize_segment("A" * 117 + "CON"))


def test_trailing_dots_and_spaces_stripped() -> None:
    assert sanitize_segment("Song. ") == "Song"
    assert sanitize_segment("Song...") == "Song"


def test_empty_segment_becomes_untitled() -> None:
    assert sanitize_segment("") == "untitled"
    assert sanitize_segment("   ") == "untitled"


def test_build_track_path_applies_layout() -> None:
    path = build_track_path(Path("/music"), "Example Artist", "Example Album", 3, "Song")
    assert path == Path("/music/Example Artist/Example Album/03 - Song.mp3")


def test_build_track_path_sanitizes_but_never_nn_prefix_or_extension() -> None:
    path = build_track_path(Path("/music"), "AC/DC", "CON", 12, "Who?Made:Who")
    assert path.parts[-3:] == ("AC_DC", "CON_", "12 - Who_Made_Who.mp3")


def test_ensure_album_dir_creates_missing_directories(tmp_path: Path) -> None:
    album_dir = tmp_path / "Artist" / "Album"
    assert not album_dir.exists()
    assert ensure_album_dir(album_dir) == album_dir
    assert album_dir.is_dir()


def test_ensure_album_dir_is_idempotent(tmp_path: Path) -> None:
    album_dir = tmp_path / "Artist" / "Album"
    ensure_album_dir(album_dir)
    ensure_album_dir(album_dir)
    assert album_dir.is_dir()
