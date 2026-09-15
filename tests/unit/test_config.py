"""Tests for albumgrab.config (Slice 1 pure module).

Covers the cli-runtime scenarios assigned to Slice 1: defaults without a
config file, XDG_CONFIG_HOME honored, closed schema rejecting unknown keys
and invalid values (offending key named), and --output precedence.
"""

from pathlib import Path

import pytest

from albumgrab.config import ConfigError, load, resolve_output_root


def test_missing_config_file_yields_defaults(tmp_path: Path) -> None:
    config = load(tmp_path / "missing" / "config.toml")
    assert config.download.sleep_interval == 1.0
    assert config.download.max_sleep_interval == 3.0
    assert config.download.retries == 3
    assert config.download.backoff_base == 2.0
    assert config.youtube.player_client == ("android", "ios", "web_music")
    assert config.youtube.cookies_file == ""
    assert config.binaries.ffmpeg == ""
    assert config.output.root == ""


def test_xdg_config_home_is_honored(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    config_dir = tmp_path / "albumgrab"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text(
        "[download]\nsleep_interval = 5.0\nretries = 7\n",
        encoding="utf-8",
    )
    config = load()
    assert config.download.sleep_interval == 5.0
    assert config.download.retries == 7
    # Keys absent from the file keep their defaults.
    assert config.download.backoff_base == 2.0


def test_unknown_key_rejected_naming_key(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text("[download]\nslepe_interval = 1.0\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="slepe_interval"):
        load(path)


def test_unknown_section_rejected(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text("[downloadz]\nsleep_interval = 1.0\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="downloadz"):
        load(path)


def test_invalid_value_rejected_naming_key(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text('[download]\nsleep_interval = "fast"\n', encoding="utf-8")
    with pytest.raises(ConfigError, match="sleep_interval"):
        load(path)


def test_cli_output_flag_wins_over_everything(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text(f'[output]\nroot = "{tmp_path / "from-config"}"\n', encoding="utf-8")
    config = load(path)
    cli_root = tmp_path / "from-cli"
    assert resolve_output_root(str(cli_root), config) == cli_root


def test_config_root_used_when_no_cli_flag(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text(f'[output]\nroot = "{tmp_path / "from-config"}"\n', encoding="utf-8")
    config = load(path)
    assert resolve_output_root(None, config) == tmp_path / "from-config"


def test_default_output_root_when_neither_cli_nor_config(tmp_path: Path) -> None:
    config = load(tmp_path / "missing.toml")
    assert resolve_output_root(None, config) == Path("./albumgrab-music")
