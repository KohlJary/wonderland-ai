"""User-level configuration — API keys, model overrides, preferences.

Per-project state lives under the host project's ``.wonderland/`` (per
D-001). This module is for *user*-level state that's the same regardless
of which project Wonderland is running in: API keys, defaults, anything
that belongs to the developer rather than the codebase.

Storage is a JSON file at the platform-appropriate user config directory:

- Linux/BSD:  ``$XDG_CONFIG_HOME/wonderland/config.json`` or
              ``~/.config/wonderland/config.json``
- macOS:      ``~/Library/Application Support/wonderland/config.json``
- Windows:    ``%APPDATA%\\wonderland\\config.json``

Path resolution is delegated to ``platformdirs`` so we don't reimplement
the XDG / Apple / Windows conventions in-house.

Resolution order for any setting:
1. Explicit argument passed to the consumer
2. Environment variable (e.g., ``ANTHROPIC_API_KEY``)
3. This config file
4. Hard-coded default

Secrets sit unencrypted on disk — acceptable for a developer tool used
on a workstation. Switch to ``keyring`` if/when we need to harden that.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from platformdirs import user_config_dir

APP_NAME = "wonderland"
CONFIG_FILENAME = "config.json"


def config_dir() -> Path:
    """Return the platform-appropriate user config directory for Wonderland."""
    return Path(user_config_dir(APP_NAME, appauthor=False))


def config_path() -> Path:
    """Return the path to the Wonderland user config file."""
    return config_dir() / CONFIG_FILENAME


@dataclass
class AnthropicConfig:
    api_key: str | None = None
    model: str | None = None


@dataclass
class UIConfig:
    """User-level UI preferences. Currently the welcome-screen and
    update-check toggles; expand as the TUI grows other persistent
    preferences (default theme, default project, etc.).

    show_welcome: when True, the welcome modal fires on app startup.
    Operators can dismiss it permanently via the modal's checkbox or
    re-enable it from Settings.

    check_updates: when True, the TUI hits PyPI on startup and pops a
    modal if a newer ``wonderland-ai`` release is available. The check
    is best-effort — network failures are swallowed silently so a
    disconnected operator still gets to work. Toggleable from the
    update modal's "don't check again" checkbox.
    """

    show_welcome: bool = True
    check_updates: bool = True


@dataclass
class WonderlandConfig:
    anthropic: AnthropicConfig = field(default_factory=AnthropicConfig)
    ui: UIConfig = field(default_factory=UIConfig)


def load_config(*, path: Path | None = None) -> WonderlandConfig:
    """Read the config file and return a parsed ``WonderlandConfig``.

    Returns defaults if the file doesn't exist. Raises if the file exists
    but isn't valid JSON — silent fallback would mask a config typo.
    """
    target = path or config_path()
    if not target.is_file():
        return WonderlandConfig()
    raw = json.loads(target.read_text(encoding="utf-8"))
    anthropic_raw = raw.get("anthropic") or {}
    ui_raw = raw.get("ui") or {}
    return WonderlandConfig(
        anthropic=AnthropicConfig(
            api_key=anthropic_raw.get("api_key"),
            model=anthropic_raw.get("model"),
        ),
        ui=UIConfig(
            show_welcome=ui_raw.get("show_welcome", True),
            check_updates=ui_raw.get("check_updates", True),
        ),
    )


def save_config(config: WonderlandConfig, *, path: Path | None = None) -> None:
    """Write the config to disk, creating the parent directory if needed."""
    target = path or config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "anthropic": asdict(config.anthropic),
        "ui": asdict(config.ui),
    }
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
