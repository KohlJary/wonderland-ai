"""Tests for user-level config (cross-platform)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from wonderland import (
    AnthropicConfig,
    WonderlandConfig,
    config_dir,
    config_path,
    load_config,
    save_config,
)
from wonderland.config import APP_NAME, CONFIG_FILENAME

# ---------- platform paths ----------


def test_config_dir_returns_a_path() -> None:
    assert isinstance(config_dir(), Path)


def test_config_path_appends_filename() -> None:
    assert config_path() == config_dir() / CONFIG_FILENAME


def test_config_dir_delegates_to_platformdirs() -> None:
    """We use platformdirs so cross-platform conventions stay correct.

    platformdirs has its own per-platform test suite. Our contract is just
    "we ask platformdirs the right question" — XDG on Linux, Application
    Support on macOS, %APPDATA% on Windows.
    """
    from platformdirs import user_config_dir as pd_user_config_dir

    assert config_dir() == Path(pd_user_config_dir(APP_NAME, appauthor=False))


@pytest.mark.skipif(sys.platform != "linux", reason="Linux-specific path convention")
def test_linux_config_dir_lives_under_dot_config() -> None:
    """Sanity check on the Linux-default location when XDG_CONFIG_HOME is unset."""
    path = config_dir()
    assert path.name == APP_NAME


@pytest.mark.skipif(sys.platform != "linux", reason="XDG only applies on Linux/BSD")
def test_xdg_config_home_override_redirects_resolution(tmp_path: Path) -> None:
    """platformdirs reads $XDG_CONFIG_HOME at call time."""
    from platformdirs import user_config_dir as pd_user_config_dir

    with patch.dict("os.environ", {"XDG_CONFIG_HOME": str(tmp_path)}):
        resolved = Path(pd_user_config_dir(APP_NAME, appauthor=False))
        assert resolved == tmp_path / APP_NAME


# ---------- load / save ----------


def test_load_returns_defaults_when_file_missing(tmp_path: Path) -> None:
    config = load_config(path=tmp_path / "missing.json")
    assert config == WonderlandConfig()
    assert config.anthropic.api_key is None
    assert config.anthropic.model is None


def test_save_writes_json_to_target_path(tmp_path: Path) -> None:
    target = tmp_path / "config.json"
    config = WonderlandConfig(
        anthropic=AnthropicConfig(api_key="sk-ant-test", model="claude-haiku-4-5-20251001"),
    )
    save_config(config, path=target)
    assert target.is_file()
    raw = json.loads(target.read_text(encoding="utf-8"))
    assert raw == {
        "anthropic": {
            "api_key": "sk-ant-test",
            "model": "claude-haiku-4-5-20251001",
        },
        "ui": {
            "show_welcome": True,
        },
    }


def test_save_creates_parent_directory(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "deep" / "config.json"
    save_config(WonderlandConfig(), path=target)
    assert target.parent.is_dir()
    assert target.is_file()


def test_save_then_load_roundtrip(tmp_path: Path) -> None:
    target = tmp_path / "config.json"
    original = WonderlandConfig(
        anthropic=AnthropicConfig(api_key="sk-ant-xyz", model="claude-sonnet-4-6"),
    )
    save_config(original, path=target)
    rehydrated = load_config(path=target)
    assert rehydrated == original


def test_load_partial_config(tmp_path: Path) -> None:
    """Config file with only some fields populated still parses cleanly."""
    target = tmp_path / "config.json"
    target.write_text(json.dumps({"anthropic": {"api_key": "sk-ant-only"}}))
    config = load_config(path=target)
    assert config.anthropic.api_key == "sk-ant-only"
    assert config.anthropic.model is None


def test_load_empty_anthropic_section(tmp_path: Path) -> None:
    target = tmp_path / "config.json"
    target.write_text(json.dumps({}))
    config = load_config(path=target)
    assert config == WonderlandConfig()


def test_load_raises_on_malformed_json(tmp_path: Path) -> None:
    """Silent fallback would mask a config typo — better to fail loudly."""
    target = tmp_path / "config.json"
    target.write_text("{not valid json")
    with pytest.raises(json.JSONDecodeError):
        load_config(path=target)
