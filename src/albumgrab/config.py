"""Configuration loading for albumgrab (Slice 1 pure module).

Reads ``config.toml`` from the XDG config directory. A missing file yields
``DEFAULTS``; unknown keys and invalid values raise ``ConfigError`` naming
the offending key (closed schema per cli-runtime spec).
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_OUTPUT_ROOT = "./albumgrab-music"


class ConfigError(Exception):
    """Raised when config.toml contains an unknown key or an invalid value."""


@dataclass(frozen=True)
class Config:
    """Fully resolved configuration; config.toml sections flattened."""

    sleep_interval: float = 1.0
    max_sleep_interval: float = 3.0
    retries: int = 3
    backoff_base: float = 2.0
    player_client: tuple[str, ...] = ("android", "ios", "web_music")
    cookies_file: str = ""
    ffmpeg: str = ""
    output_root: str = ""


DEFAULTS = Config()

# Closed schema: dotted "section.key" -> accepted value types.
_KEY_TYPES: dict[str, tuple[type, ...]] = {
    "download.sleep_interval": (int, float),
    "download.max_sleep_interval": (int, float),
    "download.retries": (int,),
    "download.backoff_base": (int, float),
    "youtube.player_client": (list,),
    "youtube.cookies_file": (str,),
    "binaries.ffmpeg": (str,),
    "output.root": (str,),
}


def default_config_path() -> Path:
    """Resolve ``albumgrab/config.toml`` under the XDG config directory."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "albumgrab" / "config.toml"


def load(config_path: Path | None = None) -> Config:
    """Load the configuration; a missing file yields ``DEFAULTS``."""
    path = default_config_path() if config_path is None else config_path
    if not path.is_file():
        return DEFAULTS
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    values: dict[str, object] = {}
    for section, table in raw.items():
        if not isinstance(table, dict):
            raise ConfigError(f"config section [{section}] must be a table")
        for key, value in table.items():
            dotted = f"{section}.{key}"
            if dotted not in _KEY_TYPES:
                raise ConfigError(f"unknown config key '{dotted}'")
            _check_value(dotted, value)
            field = "output_root" if key == "root" else key
            values[field] = tuple(value) if key == "player_client" else value
    return Config(**values)


def resolve_output_root(cli_output: str | None, config: Config) -> Path:
    """Resolve the output root: CLI flag > [output] root > ./albumgrab-music."""
    if cli_output:
        return Path(cli_output)
    if config.output_root:
        return Path(config.output_root)
    return Path(DEFAULT_OUTPUT_ROOT)


def _check_value(dotted_key: str, value: object) -> None:
    """Reject wrong-typed values; bool never counts as a number."""
    valid = not isinstance(value, bool) and isinstance(value, _KEY_TYPES[dotted_key])
    if dotted_key.endswith("player_client"):
        valid = valid and all(isinstance(item, str) for item in value)
    if not valid:
        raise ConfigError(f"invalid value for config key '{dotted_key}': {value!r}")
