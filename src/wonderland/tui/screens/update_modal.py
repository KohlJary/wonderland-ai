"""UpdateAvailableModal — fires on startup when a newer release of
the ``wonderland-ai`` package is on PyPI.

Same shape as the welcome modal: a simple ModalScreen with a body,
a dismiss button, and a "don't check again" checkbox that persists
into ``UIConfig.check_updates``. Resolves with ``True`` if the user
acknowledged, ``None`` on escape. Both outcomes update the config
if the checkbox state changed.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Footer, Header, Static

from wonderland.config import (
    AnthropicConfig,
    UIConfig,
    WonderlandConfig,
    load_config,
    save_config,
)


class UpdateAvailableModal(ModalScreen[bool | None]):
    """Modal surfaced on startup when PyPI has a newer release. The
    caller is expected to have already verified that an update is
    available — the modal itself doesn't do the network round-trip."""

    BINDINGS = [
        Binding("escape", "cancel", "Dismiss", show=True),
        Binding("enter", "confirm", "OK", show=True),
    ]

    DEFAULT_CSS = """
    UpdateAvailableModal {
        align: center middle;
    }

    UpdateAvailableModal > #update-modal-root {
        width: 70;
        max-height: 22;
        background: $panel;
        border: thick $accent;
        padding: 1 2;
    }

    UpdateAvailableModal #update-modal-title {
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }

    UpdateAvailableModal #update-modal-body {
        margin-bottom: 1;
    }

    UpdateAvailableModal #update-modal-install {
        background: $boost;
        color: $text;
        padding: 0 1;
        margin-bottom: 1;
    }

    UpdateAvailableModal #update-modal-actions {
        height: auto;
        align: center middle;
    }

    UpdateAvailableModal #update-modal-actions Button {
        margin: 0 1;
    }
    """

    def __init__(self, installed: str, latest: str) -> None:
        super().__init__()
        self._installed = installed
        self._latest = latest
        try:
            self._config = load_config()
        except Exception:  # noqa: BLE001
            self._config = WonderlandConfig()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="update-modal-root"):
            yield Static(
                f"★ Wonderland {self._latest} is out",
                id="update-modal-title",
            )
            yield Static(
                f"You're on [b]{self._installed}[/b]. The latest "
                f"release on PyPI is [b]{self._latest}[/b]. New "
                f"versions ship roughly weekly — release notes live "
                f"under [dim]release-notes/[/dim] in the repo.",
                id="update-modal-body",
            )
            yield Static(
                f"  pip install -U wonderland-ai=={self._latest}",
                id="update-modal-install",
            )
            yield Checkbox(
                "Don't check for updates on startup",
                value=False,
                id="update-modal-dont-check",
            )
            with Horizontal(id="update-modal-actions"):
                yield Button(
                    "Dismiss", id="update-modal-dismiss"
                )
                yield Button(
                    "Got it",
                    id="update-modal-ok",
                    variant="primary",
                )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "update-modal-dismiss":
            self.action_cancel()
        elif bid == "update-modal-ok":
            self.action_confirm()

    def action_cancel(self) -> None:
        self._save_pref()
        self.dismiss(None)

    def action_confirm(self) -> None:
        self._save_pref()
        self.dismiss(True)

    def _save_pref(self) -> None:
        """Persist the don't-check-again checkbox state. No-op when
        the checkbox value matches the current config so we don't
        thrash the config file on every dismissal."""
        try:
            dont_check = self.query_one(
                "#update-modal-dont-check", Checkbox
            )
            check_updates = not dont_check.value
        except Exception:  # noqa: BLE001
            return
        if check_updates == self._config.ui.check_updates:
            return
        new_config = WonderlandConfig(
            anthropic=AnthropicConfig(
                api_key=self._config.anthropic.api_key,
                model=self._config.anthropic.model,
            ),
            ui=UIConfig(
                show_welcome=self._config.ui.show_welcome,
                check_updates=check_updates,
            ),
        )
        try:
            save_config(new_config)
        except Exception:  # noqa: BLE001
            pass


__all__ = ["UpdateAvailableModal"]
