"""Configuration loading for albumgrab (Slice 1 pure module).

Reads ``config.toml`` from the XDG config directory. A missing file yields
built-in defaults; unknown keys/sections and invalid values raise
``ConfigError`` naming the offending key (closed schema per cli-runtime spec).
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_OUTPUT_ROOT = "./albumgrab-music"


class ConfigError(Exception):
    """Raised when config.toml contains an unknown key or an invalid value."""


@dataclass(frozen=True)
class DownloadConfig:
    sleep_interval: float = 1.0
    max_sleep_interval: float = 3.0
    retries: int = 3
    backoff_base: float = 2.0


@dataclass(frozen=True)
class YoutubeConfig:
    player_client: tuple[str, ...] = ("android", "ios", "web_music")
    cookies_file: str = ""


@dataclass(frozen=True)
class BinariesConfig:
    ffmpeg: str = ""


@dataclass(frozen=True)
class OutputConfig:
    root: str = ""


@dataclass(frozen=True)
class Config:
    download: DownloadConfig = field(default_factory=DownloadConfig)
    youtube: YoutubeConfig = field(default_factory=YoutubeConfig)
    binaries: BinariesConfig = field(default_factory=BinariesConfig)
    output: OutputConfig = field(default_factory=OutputConfig)


# Closed schema: section name -> (dataclass, {field: accepted value types}).
_SCHEMA: dict[str, tuple[type, dict[str, tuple[type, ...]]]] = {
    "download": (
        DownloadConfig,
        {
            "sleep_interval": (int, float),
            "max_sleep_interval": (int, float),
            "retries": (int,),
            "backoff_base": (int, float),
        },
    ),
    "youtube": (YoutubeConfig, {"player_client": (list,), "cookies_file": (str,)}),
    "binaries": (BinariesConfig, {"ffmpeg": (str,)}),
    "output": (OutputConfig, {"root": (str,)}),
}


def default_config_path() -> Path:
    """Resolve ``albumgrab/config.toml`` under the XDG config directory."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "albumgrab" / "config.toml"


def load(config_path: Path | None = None) -> Config:
    """Load the configuration; a missing file yields built-in defaults."""
    path = default_config_path() if config_path is None else config_path
    if not path.is_file():
        return Config()
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    sections: dict[str, object] = {}
    for name, (cls, fields) in _SCHEMA.items():
        table = raw.get(name, {})
        if not isinstance(table, dict):
            raise ConfigError(f"config section [{name}] must be a table")
        clean: dict[str, object] = {}
        for key, value in table.items():
            if key not in fields:
                raise ConfigError(f"unknown config key '{name}.{key}'")
            _validate_value(name, key, value, fields[key])
            clean[key] = tuple(value) if key == "player_client" else value
        sections[name] = cls(**clean)
    for name in raw:
        if name not in _SCHEMA:
            raise ConfigError(f"unknown config section '[{name}]'")
    return Config(**sections)


def resolve_output_root(cli_output: str | None, config: Config) -> Path:
    """Resolve the output root: CLI flag > [output] root > ./albumgrab-music."""
    if cli_output:
        return Path(cli_output)
    if config.output.root:
        return Path(config.output.root)
    return Path(DEFAULT_OUTPUT_ROOT)


def _validate_value(
    section: str, key: str, value: object, allowed: tuple[type, ...]
) -> None:
    """Reject values of the wrong type; bool never counts as a number."""
    valid = not isinstance(value, bool) and isinstance(value, allowed)
    if key == "player_client":
        valid = valid and all(isinstance(item, str) for item in value)
    if not valid:
        expected = "list of strings" if key == "player_client" else " or ".join(
            t.__name__ for t in allowed
        )
        raise ConfigError(
            f"invalid value for config key '{section}.{key}': {value!r} "
            f"(expected {expected})"
        )
