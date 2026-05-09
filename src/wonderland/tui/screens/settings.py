"""Settings screen — user-level configuration from inside the TUI.

The most important thing this screen surfaces is the Anthropic API
key, which is the single piece of config a fresh ``pip install
wonderland-ai`` user needs before they can do anything substantive.
Without an in-TUI path to set it, users hit the 'no API key found'
error in NewRunScreen and have to drop to the shell to write
~/.config/wonderland/config.json by hand. This screen makes it
clickable.

Persists via ``wonderland.config.save_config`` to the platform-
appropriate user config dir (XDG / macOS Application Support / APPDATA
on Windows, all delegated to ``platformdirs``).

Reachable from the home view via the visible 'Settings' button or
the 'S' binding. NewRunScreen.action_go also pushes this when no
API key resolves so the missing-key error has a one-click recovery.
"""

from __future__ import annotations

import os

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static

from wonderland.config import (
    AnthropicConfig,
    WonderlandConfig,
    config_path,
    load_config,
    save_config,
)


class SettingsScreen(Screen[None]):
    """User-level configuration form. Currently surfaces the
    Anthropic API key + model override; future fields slot into
    the same shape (model picker, default workflow, default budget,
    etc.).
    """

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("ctrl+s", "save", "Save", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        try:
            self._config = load_config()
        except Exception:  # noqa: BLE001 — bad config file shouldn't crash
            self._config = WonderlandConfig()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical():
            yield Static(
                "[b]Settings[/b]    "
                "[dim]User-level configuration (saved to your home dir)[/dim]",
                id="settings-header",
            )

            # Status line: where the config lives + whether key is
            # currently set (env var or file).
            cfg_path = config_path()
            env_set = bool(os.environ.get("ANTHROPIC_API_KEY"))
            key_status_lines = [
                f"[b]Config file:[/b] [dim]{cfg_path}[/dim]",
            ]
            if env_set:
                key_status_lines.append(
                    "[b]ANTHROPIC_API_KEY env var:[/b] "
                    "[green]set (overrides any saved key)[/green]"
                )
            elif self._config.anthropic.api_key:
                masked = (
                    self._config.anthropic.api_key[:6]
                    + "…"
                    + self._config.anthropic.api_key[-4:]
                    if len(self._config.anthropic.api_key) > 12
                    else "(short value)"
                )
                key_status_lines.append(
                    f"[b]Saved API key:[/b] [green]{masked}[/green]"
                )
            else:
                key_status_lines.append(
                    "[b]API key:[/b] [yellow]not set[/yellow]"
                )
            yield Static("\n".join(key_status_lines), id="settings-status")

            # API key input
            yield Static(
                "[b]Anthropic API key[/b]\n"
                "[dim]Get one at https://console.anthropic.com/. Saved "
                "in plaintext to the config file above. Leave blank to "
                "leave the existing key alone.[/dim]",
                id="settings-api-key-label",
            )
            with Horizontal(id="settings-api-key-row"):
                yield Label("Key:", id="api-key-input-label")
                yield Input(
                    placeholder="sk-ant-…",
                    password=True,
                    id="api-key-input",
                )

            # Model override (optional)
            yield Static(
                "[b]Model[/b] [dim](optional override; defaults to "
                "claude-haiku-4-5-20251001)[/dim]",
                id="settings-model-label",
            )
            with Horizontal(id="settings-model-row"):
                yield Label("Model:", id="model-input-label")
                yield Input(
                    value=self._config.anthropic.model or "",
                    placeholder="claude-haiku-4-5-20251001",
                    id="model-input",
                )

            with Horizontal(id="settings-actions"):
                yield Button(
                    "💾 Save (Ctrl+S)",
                    id="save-button",
                    variant="primary",
                )
                yield Button("Cancel (esc)", id="cancel-button")
        yield Footer()

    def on_mount(self) -> None:
        # Focus the api-key input by default — the most-likely
        # reason the user opened this screen is to set the key.
        self.query_one("#api-key-input", Input).focus()

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_save(self) -> None:
        new_key = self.query_one("#api-key-input", Input).value.strip()
        new_model = self.query_one("#model-input", Input).value.strip()

        # Updated config: keep existing key when the input was left
        # blank (the placeholder hint says so explicitly). Update
        # when the user typed something.
        existing_key = self._config.anthropic.api_key
        api_key_to_save = new_key if new_key else existing_key
        model_to_save = new_model if new_model else None

        new_config = WonderlandConfig(
            anthropic=AnthropicConfig(
                api_key=api_key_to_save,
                model=model_to_save,
            ),
        )

        try:
            save_config(new_config)
        except Exception as exc:  # noqa: BLE001
            self.notify(
                f"Failed to save settings: {exc}", severity="error"
            )
            return

        self.notify(
            f"Saved settings to {config_path()}",
            severity="information",
            timeout=3,
        )
        # Update local cache so the status line reflects the save
        # if the user stays on the screen.
        self._config = new_config
        # Then pop back.
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-button":
            self.action_save()
        elif event.button.id == "cancel-button":
            self.action_back()


__all__ = ["SettingsScreen"]
