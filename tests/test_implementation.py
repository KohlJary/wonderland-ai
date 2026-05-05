"""Tests for the Implementation writer + registry."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from wonderland import (
    ImplementationPayload,
    ImplementationRegistry,
    ImplementationSide,
    render_implementation,
)

# ---------- helpers ----------


def _payload(**overrides) -> ImplementationPayload:
    base = {
        "title": "Translation message subscription",
        "side": ImplementationSide.FRONTEND,
        "ticket_reference": "ticket-014-translation-message-subscription",
        "approach_summary": (
            "Wired the message list to the WebSocket subscription using a "
            "virtual scroll for history and an in-memory pending-translation "
            "queue for messages awaiting translation."
        ),
        "contract": (
            "message-envelope v3 (translation_status enum + source_lang FK); "
            "message-translated WebSocket event."
        ),
        "files_touched": [
            "src/chat/MessageList.tsx: virtual scroll + subscription wiring",
            "src/chat/usePendingTranslations.ts: client-side queue hook",
        ],
        "open_questions_for_pair": [
            "Does message-translated arrive once or once-per-language?",
        ],
        "ready_for_review": True,
        "known_limitations": [
            "Offline message composition not yet supported — offline-queued "
            "state shows 'reconnect to send'.",
        ],
        "ui_states_implemented": [
            "loading: skeleton bubbles for the first paint",
            "empty: 'no messages yet' with a tip",
            "error-recoverable: 'reconnecting...' with retry",
            "stale: warning badge when subscription is older than 30s",
        ],
        "client_state": (
            "Pending-translation queue keyed by message_id. Reconciles with "
            "server state when message-translated arrives; entries TTL out "
            "after 60s with an error-recoverable surface."
        ),
    }
    return ImplementationPayload(**(base | overrides))


def _backend_payload(**overrides) -> ImplementationPayload:
    base = {
        "title": "Translation worker pipeline",
        "side": ImplementationSide.BACKEND,
        "ticket_reference": "ticket-015-translation-worker-pipeline",
        "approach_summary": (
            "Translation jobs picked up by a worker pool, persisted with "
            "translation_status enum, emitted as message-translated events "
            "on completion or message-translation-failed on dead-letter."
        ),
        "contract": (
            "message-envelope v3 (matches frontend); message-translated + "
            "message-translation-failed WebSocket events."
        ),
        "files_touched": [
            "services/translation/worker.py: job loop + retry policy",
            "db/migrations/0042_translation_status.sql: enum + index",
        ],
        "ready_for_review": True,
        "invariants_enforced": [
            "every translated message has exactly one source_lang (DB FK NOT NULL)",
            "translation_status transitions are monotonic (DB CHECK constraint)",
        ],
        "schema_changes": (
            "Migration 0042 adds translation_status enum and source_lang FK to "
            "messages. Backward-compatible: existing rows backfilled with "
            "status='not_required' and source_lang derived from sender locale."
        ),
        "failure_modes_handled": [
            "worker crash mid-message: job re-enqueued via at-least-once delivery",
            "DB write succeeds but WebSocket emit fails: retry from outbox table",
            "translation provider 5xx: exponential backoff up to 3 attempts then dead-letter",
        ],
    }
    return ImplementationPayload(**(base | overrides))


# ---------- ImplementationPayload validation: structural ----------


def test_payload_requires_non_empty_title() -> None:
    with pytest.raises(ValidationError):
        _payload(title="")


@pytest.mark.parametrize("side", list(ImplementationSide))
def test_payload_accepts_each_side(side: ImplementationSide) -> None:
    payload = _payload(side=side)
    assert payload.side is side


def test_payload_rejects_unknown_side() -> None:
    with pytest.raises(ValidationError):
        _payload(side="middleware")  # type: ignore[arg-type]


def test_payload_optional_fields_default() -> None:
    payload = _payload(
        files_touched=[],
        open_questions_for_pair=[],
        known_limitations=[],
        ui_states_implemented=[],
        client_state="",
    )
    assert payload.files_touched == []
    assert payload.ready_for_review is True  # we set it; default is False elsewhere


def test_payload_ready_for_review_defaults_false() -> None:
    """Without explicit setting, ready_for_review is False — Caterpillar
    won't engage until the Tweedle flips it explicitly."""
    payload = ImplementationPayload(
        title="x",
        side=ImplementationSide.FRONTEND,
        ticket_reference="t",
        approach_summary="a",
        contract="c",
    )
    assert payload.ready_for_review is False


# ---------- ImplementationPayload validation: the grin (contract) ----------


def test_payload_requires_non_empty_contract() -> None:
    """The grin equivalent — implicit contracts are bugs in the making (§II)."""
    with pytest.raises(ValidationError, match="implicit contracts"):
        _payload(contract="")


def test_payload_rejects_only_whitespace_contract() -> None:
    with pytest.raises(ValidationError, match="implicit contracts"):
        _payload(contract="   ")


# ---------- ImplementationPayload validation: ticket reference ----------


def test_payload_requires_non_empty_ticket_reference() -> None:
    with pytest.raises(ValidationError, match="trace to a Rabbit ticket"):
        _payload(ticket_reference="")


# ---------- ImplementationPayload validation: approach summary ----------


def test_payload_requires_non_empty_approach_summary() -> None:
    with pytest.raises(ValidationError, match="vague"):
        _payload(approach_summary="")


# ---------- render_implementation: frontend ----------


def test_render_frontend_includes_required_sections() -> None:
    out = render_implementation(7, _payload())
    assert "## Implementation 007: Translation message subscription" in out
    assert "**Side:** frontend" in out
    assert "**Ticket:** ticket-014-translation-message-subscription" in out
    assert "**Contract:** message-envelope v3" in out
    assert "**Ready for review:** yes" in out
    assert "**Approach:**" in out
    assert "Wired the message list" in out


def test_render_frontend_includes_side_specific_sections() -> None:
    out = render_implementation(1, _payload())
    assert "**UI States Implemented:**" in out
    assert "- loading: skeleton bubbles" in out
    assert "**Client State:**" in out
    assert "Pending-translation queue keyed by message_id" in out


def test_render_frontend_omits_backend_sections() -> None:
    out = render_implementation(1, _payload())
    assert "**Invariants Enforced:**" not in out
    assert "**Schema Changes:**" not in out
    assert "**Failure Modes Handled:**" not in out


# ---------- render_implementation: backend ----------


def test_render_backend_includes_side_specific_sections() -> None:
    out = render_implementation(2, _backend_payload())
    assert "**Side:** backend" in out
    assert "**Invariants Enforced:**" in out
    assert "- every translated message has exactly one source_lang" in out
    assert "**Schema Changes:**" in out
    assert "Migration 0042" in out
    assert "**Failure Modes Handled:**" in out


def test_render_backend_omits_frontend_sections() -> None:
    out = render_implementation(2, _backend_payload())
    assert "**UI States Implemented:**" not in out
    assert "**Client State:**" not in out


# ---------- render_implementation: shared sections ----------


def test_render_includes_files_touched() -> None:
    out = render_implementation(1, _payload())
    assert "**Files:**" in out
    assert "- src/chat/MessageList.tsx" in out


def test_render_includes_open_questions() -> None:
    out = render_implementation(1, _payload())
    assert "**Open Questions for Pair:**" in out
    assert "Does message-translated arrive once" in out


def test_render_omits_open_questions_when_empty() -> None:
    out = render_implementation(1, _payload(open_questions_for_pair=[]))
    assert "**Open Questions for Pair:**" not in out


def test_render_includes_known_limitations() -> None:
    out = render_implementation(1, _payload())
    assert "**Known Limitations:**" in out


def test_render_marks_not_ready_for_review() -> None:
    out = render_implementation(1, _payload(ready_for_review=False))
    assert "**Ready for review:** no" in out


def test_render_three_digit_padding() -> None:
    assert "Implementation 003:" in render_implementation(3, _payload())


# ---------- ImplementationRegistry — empty state ----------


def test_empty_registry_state(tmp_path: Path) -> None:
    registry = ImplementationRegistry(tmp_path)
    assert registry.list_implementations() == []
    assert registry.next_number() == 1
    assert registry.find_by_slug("anything") is None
    assert registry.find_by_number(1) is None


def test_path_under_dot_wonderland_implementations(tmp_path: Path) -> None:
    registry = ImplementationRegistry(tmp_path)
    assert registry.path == tmp_path / ".wonderland" / "implementations"


# ---------- ImplementationRegistry — write ----------


def test_write_creates_file_at_expected_path(tmp_path: Path) -> None:
    registry = ImplementationRegistry(tmp_path)
    record = registry.write(_payload())
    assert record.number == 1
    assert record.slug.startswith("translation-message-subscription")
    assert record.path.is_file()
    assert record.side is ImplementationSide.FRONTEND
    assert record.ready_for_review is True


def test_write_creates_parent_directory(tmp_path: Path) -> None:
    registry = ImplementationRegistry(tmp_path)
    registry.write(_payload())
    assert registry.path.is_dir()


def test_write_accepts_dict_payload(tmp_path: Path) -> None:
    registry = ImplementationRegistry(tmp_path)
    record = registry.write(
        {
            "title": "Auth refresh endpoint",
            "side": "backend",
            "ticket_reference": "ticket-021-auth-refresh",
            "approach_summary": "POST /auth/refresh validates session and returns new tokens.",
            "contract": "auth API v2 (HttpOnly refresh cookie + access token in body)",
            "ready_for_review": True,
            "invariants_enforced": ["session has exactly one active refresh token"],
        }
    )
    assert record.side is ImplementationSide.BACKEND
    assert record.ticket_reference == "ticket-021-auth-refresh"


def test_write_rejects_payload_without_contract(tmp_path: Path) -> None:
    registry = ImplementationRegistry(tmp_path)
    with pytest.raises(ValidationError):
        registry.write(
            {
                "title": "x",
                "side": "frontend",
                "ticket_reference": "t",
                "approach_summary": "a",
                "contract": "",
            }
        )


def test_write_auto_increments(tmp_path: Path) -> None:
    registry = ImplementationRegistry(tmp_path)
    a = registry.write(_payload(title="A"))
    b = registry.write(_backend_payload(title="B"))
    assert (a.number, b.number) == (1, 2)


def test_written_file_round_trips_through_render(tmp_path: Path) -> None:
    registry = ImplementationRegistry(tmp_path)
    payload = _payload()
    record = registry.write(payload)
    assert record.read() == render_implementation(1, payload)


# ---------- ImplementationRegistry — queries ----------


def test_list_in_number_order(tmp_path: Path) -> None:
    registry = ImplementationRegistry(tmp_path)
    for title in ("Third", "First", "Second"):
        registry.write(_payload(title=title))
    listing = registry.list_implementations()
    assert [r.number for r in listing] == [1, 2, 3]
    assert [r.title for r in listing] == ["Third", "First", "Second"]


def test_find_by_slug(tmp_path: Path) -> None:
    registry = ImplementationRegistry(tmp_path)
    registry.write(_payload(title="Auth refresh endpoint"))
    found = registry.find_by_slug("auth-refresh-endpoint")
    assert found is not None
    assert found.side is ImplementationSide.FRONTEND  # the helper's default


def test_find_by_number(tmp_path: Path) -> None:
    registry = ImplementationRegistry(tmp_path)
    registry.write(_payload(title="A"))
    registry.write(_payload(title="B"))
    found = registry.find_by_number(2)
    assert found is not None
    assert found.title == "B"


def test_recovers_side_and_ticket_from_disk(tmp_path: Path) -> None:
    registry = ImplementationRegistry(tmp_path)
    registry.write(_backend_payload(title="Backend impl"))
    fresh = ImplementationRegistry(tmp_path)
    listing = fresh.list_implementations()
    assert listing[0].side is ImplementationSide.BACKEND
    assert listing[0].ticket_reference == "ticket-015-translation-worker-pipeline"
    assert listing[0].ready_for_review is True


def test_skips_non_implementation_files(tmp_path: Path) -> None:
    registry = ImplementationRegistry(tmp_path)
    registry.write(_payload(title="A"))
    (registry.path / "README.md").write_text("not an implementation")
    (registry.path / "implementation-malformed.md").write_text("also not")
    assert len(registry.list_implementations()) == 1
