"""Tests for albumgrab.selection (album-selection scenarios 1-7).

Acceptance: parse_selection returns the sorted, de-duplicated union of
1-based album indices; every invalid input raises InvalidSelection naming
the offending token.
"""

import pytest

from albumgrab.selection import InvalidSelection, parse_selection


def test_single_number_selects_only_that_album() -> None:
    assert parse_selection("3", 6) == [3]


def test_inclusive_range_selects_bounds() -> None:
    assert parse_selection("2-5", 6) == [2, 3, 4, 5]


def test_mixed_list_deduplicates_each_album_once() -> None:
    assert parse_selection("1,3-5,5,7", 7) == [1, 3, 4, 5, 7]


def test_all_keyword_selects_every_album_case_insensitively() -> None:
    assert parse_selection("all", 4) == [1, 2, 3, 4]
    assert parse_selection("ALL", 4) == [1, 2, 3, 4]
    assert parse_selection("All", 4) == [1, 2, 3, 4]


def test_out_of_range_number_rejected_naming_token() -> None:
    with pytest.raises(InvalidSelection) as excinfo:
        parse_selection("9", 4)
    assert excinfo.value.token == "9"


def test_garbage_token_rejected_naming_token_and_selecting_nothing() -> None:
    with pytest.raises(InvalidSelection) as excinfo:
        parse_selection("1,x,2", 4)
    assert excinfo.value.token == "x"


def test_range_with_out_of_bounds_end_rejected_naming_the_range() -> None:
    with pytest.raises(InvalidSelection) as excinfo:
        parse_selection("2-99", 4)
    assert excinfo.value.token == "2-99"


def test_inverted_range_rejected_naming_the_range() -> None:
    with pytest.raises(InvalidSelection) as excinfo:
        parse_selection("5-2", 7)
    assert excinfo.value.token == "5-2"


def test_empty_input_is_invalid() -> None:
    with pytest.raises(InvalidSelection) as excinfo:
        parse_selection("   ", 4)
    assert excinfo.value.token == "   "
