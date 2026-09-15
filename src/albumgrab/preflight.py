"""Preflight binary checks (Slice 2 thin module).

ffmpeg/ffprobe are hard requirements — a missing binary raises
:class:`PreflightError` so the run aborts before any network work or
download (cli-runtime "missing ffmpeg"). Deno is warn-only.
"""

from __future__ import annotations

import shutil

_REQUIRED = ("ffmpeg", "ffprobe")


class PreflightError(Exception):
    """Raised when a required binary is missing; aborts before downloads."""


def run_preflight() -> list[str]:
    """Check required binaries and return soft warnings.

    Raises :class:`PreflightError` naming the first missing required binary;
    a missing Deno yields a warning string and the run continues.
    """
    for binary in _REQUIRED:
        if shutil.which(binary) is None:
            raise PreflightError(
                f"{binary} is required but was not found on PATH. "
                f"Install it (e.g. 'ffmpeg' via your package manager) and re-run albumgrab."
            )
    warnings: list[str] = []
    if shutil.which("deno") is None:
        warnings.append(
            "Warning: Deno not found on PATH; YouTube downloads may throttle or fail."
        )
    return warnings
