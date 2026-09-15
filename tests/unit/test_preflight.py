"""Tests for albumgrab.preflight (cli-runtime preflight scenarios).

`shutil.which` is monkeypatched — no real binary lookup happens here.
"""

import pytest

from albumgrab.preflight import PreflightError, run_preflight


def patch_which(monkeypatch: pytest.MonkeyPatch, found: dict[str, str]) -> None:
    monkeypatch.setattr("shutil.which", lambda name: found.get(name))


def test_missing_ffmpeg_hard_fails_with_actionable_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_which(monkeypatch, {})  # nothing on PATH
    with pytest.raises(PreflightError) as excinfo:
        run_preflight()
    message = str(excinfo.value)
    assert "ffmpeg" in message
    assert "install" in message.lower()  # actionable: says what to do


def test_missing_ffprobe_hard_fails_naming_ffprobe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_which(monkeypatch, {"ffmpeg": "/usr/bin/ffmpeg"})  # ffprobe absent
    with pytest.raises(PreflightError) as excinfo:
        run_preflight()
    assert "ffprobe" in str(excinfo.value)


def test_missing_deno_warns_but_run_continues(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_which(
        monkeypatch,
        {"ffmpeg": "/usr/bin/ffmpeg", "ffprobe": "/usr/bin/ffprobe"},
    )
    warnings = run_preflight()  # must NOT raise
    assert len(warnings) == 1
    assert "Deno" in warnings[0]
    assert "throttle" in warnings[0]  # spec: warns downloads may throttle or fail


def test_all_binaries_present_yields_no_warnings(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_which(
        monkeypatch,
        {
            "ffmpeg": "/usr/bin/ffmpeg",
            "ffprobe": "/usr/bin/ffprobe",
            "deno": "/usr/local/bin/deno",
        },
    )
    assert run_preflight() == []
