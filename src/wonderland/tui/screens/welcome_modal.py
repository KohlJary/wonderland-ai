"""WelcomeModal — first-run onboarding for the Wonderland TUI.

Multi-page modal that fires on first launch (or whenever the operator
re-enables it from Settings). Walks a new user through what Wonderland
is, what makes it different, how to get started, and surfaces an API
key entry field if no key is configured yet.

Pages:
  1. What it is (the friendly elevator pitch)
  2. What's cool (the value props)
  3. How a session feels (project → directive → watch → review loop)
  4. Setup (API key entry if unset, "don't show again" toggle, get
     started button)

Dismisses with True (welcome flow finished — proceed to project
library) or None (escape pressed — same outcome). The modal saves
its own state (API key + show_welcome flag) before dismissing.
"""

from __future__ import annotations

import os

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Footer, Header, Input, Static

from wonderland.config import (
    AnthropicConfig,
    UIConfig,
    WonderlandConfig,
    load_config,
    save_config,
)


# ---------------------------------------------------------------------- #
# Page content. Edit copy here without touching the modal logic below.
# Tone target: friendly, plain-English, value-forward. Speak to a
# curious developer who's heard about agents but doesn't know what
# distinguishes Wonderland yet.
# ---------------------------------------------------------------------- #

_PAGE_1_TITLE = "Welcome to Wonderland"
_PAGE_1_BODY = """
[b]A team of AI characters that builds software with you.[/b]

You give them a directive — "build me a personal finance tracker," "ship
a /hello endpoint," whatever — and they collaborate to deliver it.
[b]Alice[/b] writes user stories. The [b]White Rabbit[/b] decomposes them
into tickets. The [b]Cheshire Cat[/b] makes architectural decisions.
The [b]Tweedles[/b] write the code. The [b]Mad Hatter[/b] writes the
tests first. The [b]Caterpillar[/b] reviews everything before it ships.

Each character has a stable identity that persists across runs. They're
not playing roles — they [i]inhabit[/i] them.
"""

_PAGE_2_TITLE = "Why this is different"
_PAGE_2_BODY = """
[b]Cheap iteration.[/b] A full design pass costs about as much as a coffee
($1–$3). Implementation runs add a few dollars per feature. You can
iterate the design 5–10 times before committing to the implementation
budget.

[b]Real review.[/b] Caterpillar isn't a linter — she catches contract
drift between files, schema-vs-test mismatches, and the kind of
cross-cutting bugs that single-file reviews miss. Her verdicts gate
the lifecycle: features don't reach "ready to ship" until she signs off.

[b]TDD discipline by default.[/b] Hatter writes failing tests first;
the Tweedles make them pass. The substrate enforces this — there's no
"forgot to write tests" pattern.

[b]Cross-run continuity.[/b] Your project's design state (features,
tickets, contracts, ADRs) lives in [dim].wonderland/[/dim] alongside the
code. Re-running picks up where you left off, not from scratch.
"""

_PAGE_3_TITLE = "How a session feels"
_PAGE_3_BODY = """
[b]1. Open a project[/b] — anywhere on your machine. The TUI's home
screen lists your projects; create one with a directory and a stack
profile.

[b]2. Pick a directive[/b] — there are sample directives bundled in
("Build a Geocities", "Pomodoro timer", "Personal fitness tracker").
Or write your own. Be casual; the team is good at extracting structure
from natural-language asks.

[b]3. Watch the team work[/b] — the live-watch screen shows each
character's contributions in real time. Cost ticks up; you see who's
saying what.

[b]4. Review what shipped[/b] — features land in your project's
[dim].wonderland/[/dim] directory. The dashboard shows them with
lifecycle state badges. Queue the ones you want implemented; the team
flows them through tests, code, and review.
"""

_PAGE_4_TITLE = "Setup"

# Tail body for page 4 when an API key is already configured (env var
# OR config file). No entry needed; just the get-started prompt.
_PAGE_4_BODY_KEY_SET = """
[green]✓[/green] [b]API key configured.[/b] You're ready to go.

[dim]Click "Get Started" to land on the project library. Pick or create
a project, then try a sample directive to see the team in action.
The [b]Geocities[/b] sample is the showcase — about 8 minutes wall-clock
for $2 of API spend, with auth, GDPR-deletion, and a working multi-user
feature set.[/dim]
"""

# Tail body when no key is set. Surfaces the entry field.
_PAGE_4_BODY_KEY_UNSET = """
[b]One thing first:[/b] Wonderland needs an Anthropic API key to talk to
the LLM. Paste yours below and it'll save to your user config (no project
state, no commits).

Don't have one yet? Grab one at [dim]https://console.anthropic.com/[/dim]
— it takes about a minute to sign up, and Wonderland's per-run cost is
in the single-digit dollars.

[dim]Tip: you can also set [b]ANTHROPIC_API_KEY[/b] as an environment
variable; that takes priority over the saved key.[/dim]
"""


# ---------------------------------------------------------------------- #
# Page sequence — list of (title, body) tuples. The setup-page body is
# resolved at compose time based on whether a key is already set.
# Adding a page is a one-line addition here.
# ---------------------------------------------------------------------- #


_PAGES: tuple[tuple[str, str], ...] = (
    (_PAGE_1_TITLE, _PAGE_1_BODY),
    (_PAGE_2_TITLE, _PAGE_2_BODY),
    (_PAGE_3_TITLE, _PAGE_3_BODY),
    (_PAGE_4_TITLE, ""),  # body resolved dynamically per key state
)


# ---------------------------------------------------------------------- #
# Modal
# ---------------------------------------------------------------------- #


class WelcomeModal(ModalScreen[bool | None]):
    """First-run onboarding modal. Multi-page; persists config on
    dismissal so the API key + show-on-startup preference survive
    the run."""

    BINDINGS = [
        Binding("escape", "cancel", "Skip", show=True),
        Binding("right", "next_page", "Next", show=False),
        Binding("left", "prev_page", "Back", show=False),
        Binding("enter", "next_or_finish", "Next/Done", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._page_idx = 0
        try:
            self._config = load_config()
        except Exception:  # noqa: BLE001
            self._config = WonderlandConfig()
        # Load existing key into the input so re-launching doesn't
        # erase it. Env var takes priority and means we don't need
        # the input at all.
        self._env_key_set = bool(os.environ.get("ANTHROPIC_API_KEY"))
        self._initial_key = self._config.anthropic.api_key or ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="welcome-modal-root"):
            yield Static(
                "",  # title set in on_mount + page transitions
                id="welcome-modal-title",
            )
            yield Static(
                "",
                id="welcome-modal-page-indicator",
            )
            yield Static(
                "",
                id="welcome-modal-body",
            )
            # API key entry — only meaningful on the setup page; we
            # show/hide via the page-transition handler.
            with Horizontal(id="welcome-modal-key-row"):
                yield Static(
                    "API key:",
                    id="welcome-modal-key-label",
                )
                yield Input(
                    value=self._initial_key,
                    placeholder="sk-ant-...",
                    password=True,
                    id="welcome-modal-key-input",
                )
            # Don't-show-again checkbox lives on the setup page too.
            yield Checkbox(
                "Don't show this welcome screen on startup",
                value=False,
                id="welcome-modal-dont-show",
            )
            with Horizontal(id="welcome-modal-actions"):
                yield Button(
                    "← Back",
                    id="welcome-modal-back",
                )
                yield Button(
                    "Skip",
                    id="welcome-modal-skip",
                )
                yield Button(
                    "Next →",
                    id="welcome-modal-next",
                    variant="primary",
                )
        yield Footer()

    def on_mount(self) -> None:
        self._render_page()

    def _render_page(self) -> None:
        title, body = _PAGES[self._page_idx]
        is_setup = self._page_idx == len(_PAGES) - 1
        if is_setup:
            body = (
                _PAGE_4_BODY_KEY_SET
                if (self._env_key_set or self._initial_key)
                else _PAGE_4_BODY_KEY_UNSET
            )

        self.query_one("#welcome-modal-title", Static).update(
            f"[b]{title}[/b]"
        )
        self.query_one("#welcome-modal-page-indicator", Static).update(
            f"[dim]Page {self._page_idx + 1} of {len(_PAGES)}[/dim]"
        )
        self.query_one("#welcome-modal-body", Static).update(body.strip())

        # Show the key-entry row only on setup page AND only if no
        # key is set via env var (env wins; surfacing input would
        # confuse the operator into thinking the env doesn't apply).
        # If a saved key exists, still show the input so they can
        # update it.
        key_row = self.query_one("#welcome-modal-key-row")
        key_row.display = is_setup and not self._env_key_set

        # "Don't show again" stays visible on every page so an
        # operator who's just clicking through has a chance to see
        # it before hitting Get Started. Tucking it on the last
        # page only would mean people who skip with Esc never
        # discover it exists.

        # Button labels: Back disabled on first page; Next becomes
        # "Get Started" on the setup page.
        back_btn = self.query_one("#welcome-modal-back", Button)
        next_btn = self.query_one("#welcome-modal-next", Button)
        back_btn.disabled = self._page_idx == 0
        if is_setup:
            next_btn.label = "▶ Get Started"
        else:
            next_btn.label = "Next →"

    # ------------------------------------------------------------------ #
    # Navigation
    # ------------------------------------------------------------------ #

    def action_next_page(self) -> None:
        if self._page_idx < len(_PAGES) - 1:
            self._page_idx += 1
            self._render_page()

    def action_prev_page(self) -> None:
        if self._page_idx > 0:
            self._page_idx -= 1
            self._render_page()

    def action_next_or_finish(self) -> None:
        # Enter advances pages; on the setup page it finishes.
        if self._page_idx < len(_PAGES) - 1:
            self.action_next_page()
        else:
            self._finish()

    def action_cancel(self) -> None:
        # Skip / Esc still respects the "don't show again" checkbox
        # if the operator toggled it. Saving just the show_welcome
        # preference (no API key change) so an operator who set
        # "don't show" on page 1 then escaped doesn't see the modal
        # again next launch.
        self._save_show_welcome_only()
        self.dismiss(None)

    def _save_show_welcome_only(self) -> None:
        """Persist only the show-welcome checkbox state. Used when
        the operator dismisses without going through the setup page
        (skip/escape). Doesn't touch the API key — that requires
        the operator to land on the setup page and explicitly
        save."""
        try:
            dont_show = self.query_one(
                "#welcome-modal-dont-show", Checkbox
            )
            show_welcome = not dont_show.value
        except Exception:  # noqa: BLE001
            return
        # Only save if the value actually differs from current config
        # — avoid unnecessary writes when the operator just hit Esc
        # without touching the checkbox.
        if show_welcome == self._config.ui.show_welcome:
            return
        new_config = WonderlandConfig(
            anthropic=self._config.anthropic,
            ui=UIConfig(show_welcome=show_welcome),
        )
        try:
            save_config(new_config)
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------ #
    # Button handlers
    # ------------------------------------------------------------------ #

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "welcome-modal-back":
            self.action_prev_page()
        elif bid == "welcome-modal-next":
            self.action_next_or_finish()
        elif bid == "welcome-modal-skip":
            self.action_cancel()

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #

    def _finish(self) -> None:
        """Save config (API key + show_welcome flag) and dismiss."""
        # Pull current input values.
        try:
            key_input = self.query_one(
                "#welcome-modal-key-input", Input
            )
            entered_key = key_input.value.strip() or None
        except Exception:  # noqa: BLE001
            entered_key = None

        try:
            dont_show = self.query_one(
                "#welcome-modal-dont-show", Checkbox
            )
            show_welcome = not dont_show.value
        except Exception:  # noqa: BLE001
            show_welcome = True

        # Build the config update. Preserve any existing model setting.
        new_config = WonderlandConfig(
            anthropic=AnthropicConfig(
                api_key=entered_key
                if entered_key is not None
                else self._config.anthropic.api_key,
                model=self._config.anthropic.model,
            ),
            ui=UIConfig(show_welcome=show_welcome),
        )
        try:
            save_config(new_config)
        except Exception as exc:  # noqa: BLE001
            self.notify(
                f"Couldn't save config: {exc}",
                severity="warning",
                timeout=6,
            )
        self.dismiss(True)


__all__ = ["WelcomeModal"]
