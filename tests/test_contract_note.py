"""Tests for the Contract Note writer + registry."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from wonderland import (
    ContractNotePayload,
    ContractNoteRegistry,
    ContractNoteState,
    render_contract_note,
)

# ---------- helpers ----------


def _payload(**overrides) -> ContractNotePayload:
    base = {
        "title": "Translation message envelope",
        "current_shape": "message-envelope v2 (text + sender_id)",
        "proposed_change": (
            "Add translation_status enum (pending/translated/failed) and "
            "source_lang FK to support multilingual chat."
        ),
        "source": "story-003-multilingual-chat",
        "frontend_impact": (
            "UI badge per message; locale toggle in conversation header; "
            "pending state with skeleton."
        ),
    }
    base.update(overrides)
    return ContractNotePayload(**base)


# ---------- payload validation ----------


def test_payload_round_trips_through_validator() -> None:
    p = _payload()
    assert p.title == "Translation message envelope"
    assert p.state is ContractNoteState.PROPOSED
    assert p.contract_version == ""


def test_proposed_change_is_required_with_pair_protocol_message() -> None:
    with pytest.raises(ValidationError) as excinfo:
        _payload(proposed_change="   ")
    assert "proposed_change must be non-empty" in str(excinfo.value)
    assert "Pair Protocol §II" in str(excinfo.value)


def test_current_shape_is_required() -> None:
    with pytest.raises(ValidationError) as excinfo:
        _payload(current_shape="")
    assert "current_shape must be non-empty" in str(excinfo.value)


def test_source_is_required() -> None:
    with pytest.raises(ValidationError) as excinfo:
        _payload(source="")
    assert "source must be non-empty" in str(excinfo.value)


def test_state_defaults_to_proposed() -> None:
    p = _payload()
    assert p.state is ContractNoteState.PROPOSED


# ---------- render ----------


def test_render_includes_state_and_pending_markers() -> None:
    payload = _payload()  # frontend_impact filled, backend_impact empty
    text = render_contract_note(7, payload)
    assert "## Contract Note 007: Translation message envelope" in text
    assert "**State:** proposed" in text
    assert "**Contract Version:** (unlocked)" in text
    assert "**Frontend Impact (Tweedledee):**" in text
    assert "UI badge per message" in text
    assert "**Backend Impact (Tweedledum):** _pending_" in text


def test_render_includes_resolution_when_set() -> None:
    payload = _payload(
        state=ContractNoteState.AGREED,
        contract_version="message-envelope v3",
        backend_impact="New columns; migration; index on source_lang",
        resolution="Both sides accept; ship under v3",
    )
    text = render_contract_note(1, payload)
    assert "**State:** agreed" in text
    assert "**Contract Version:** message-envelope v3" in text
    assert "**Resolution:**" in text
    assert "Both sides accept" in text


# ---------- registry: write + read ----------


def test_write_creates_file_and_returns_record(tmp_path: Path) -> None:
    reg = ContractNoteRegistry(tmp_path)
    record = reg.write(_payload())
    assert record.number == 1
    assert record.slug == "translation-message-envelope"
    # T-g3: filename embeds short_guid for substrate identity.
    assert record.path.name == (
        f"contract-note-{record.guid[:8]}-translation-message-envelope.md"
    )
    assert record.path.is_file()
    assert record.state is ContractNoteState.PROPOSED


def test_next_number_increments() -> None:
    reg = ContractNoteRegistry(Path("/nonexistent"))
    assert reg.next_number() == 1


def test_write_increments_number(tmp_path: Path) -> None:
    reg = ContractNoteRegistry(tmp_path)
    reg.write(_payload(title="First note"))
    reg.write(_payload(title="Second note"))
    notes = reg.list_contract_notes()
    assert [n.number for n in notes] == [1, 2]
    assert notes[0].slug == "first-note"
    assert notes[1].slug == "second-note"


def test_find_by_slug_returns_match(tmp_path: Path) -> None:
    reg = ContractNoteRegistry(tmp_path)
    reg.write(_payload())
    found = reg.find_by_slug("translation-message-envelope")
    assert found is not None
    assert found.title == "Translation message envelope"


def test_find_by_slug_returns_none_when_missing(tmp_path: Path) -> None:
    reg = ContractNoteRegistry(tmp_path)
    assert reg.find_by_slug("does-not-exist") is None


def test_list_contract_notes_tolerates_extraneous_files(tmp_path: Path) -> None:
    reg = ContractNoteRegistry(tmp_path)
    reg.write(_payload())
    # Drop a stray .md file in the directory; the registry should ignore it.
    (reg.path / "notes-from-the-team.md").write_text("free text", encoding="utf-8")
    notes = reg.list_contract_notes()
    assert len(notes) == 1


# ---------- registry: read_payload round-trips ----------


def test_read_payload_round_trips_proposed_state(tmp_path: Path) -> None:
    reg = ContractNoteRegistry(tmp_path)
    written = reg.write(_payload())
    payload = reg.read_payload(written.slug)
    assert payload is not None
    assert payload.title == "Translation message envelope"
    assert payload.state is ContractNoteState.PROPOSED
    assert payload.frontend_impact.startswith("UI badge per message")
    assert payload.backend_impact == ""
    assert payload.proposed_change.startswith("Add translation_status enum")


def test_read_payload_returns_none_for_missing_slug(tmp_path: Path) -> None:
    reg = ContractNoteRegistry(tmp_path)
    assert reg.read_payload("nope") is None


# ---------- registry: update mutates in place ----------


def test_update_fills_in_counterpart_impact(tmp_path: Path) -> None:
    reg = ContractNoteRegistry(tmp_path)
    written = reg.write(_payload())
    updated = reg.update(
        written.slug,
        backend_impact="New columns; migration; index on source_lang",
        state=ContractNoteState.COUNTERPART_ASSESSED,
    )
    assert updated.state is ContractNoteState.COUNTERPART_ASSESSED
    payload = reg.read_payload(written.slug)
    assert payload is not None
    assert payload.backend_impact.startswith("New columns")
    assert payload.frontend_impact.startswith("UI badge")  # preserved


def test_update_locks_contract_version_at_agreed(tmp_path: Path) -> None:
    reg = ContractNoteRegistry(tmp_path)
    written = reg.write(_payload())
    reg.update(
        written.slug,
        backend_impact="New columns",
        state=ContractNoteState.COUNTERPART_ASSESSED,
    )
    final = reg.update(
        written.slug,
        state=ContractNoteState.AGREED,
        contract_version="message-envelope v3",
        resolution="Both sides accept; ship under v3",
    )
    assert final.state is ContractNoteState.AGREED
    assert final.contract_version == "message-envelope v3"

    # The on-disk file's header reflects the locked version.
    text = final.path.read_text(encoding="utf-8")
    assert "**State:** agreed" in text
    assert "**Contract Version:** message-envelope v3" in text
    assert "Both sides accept" in text


def test_update_raises_for_unknown_slug(tmp_path: Path) -> None:
    reg = ContractNoteRegistry(tmp_path)
    with pytest.raises(KeyError, match="No Contract Note with slug"):
        reg.update("does-not-exist", state=ContractNoteState.DEFERRED, resolution="x")


def test_update_can_transition_to_escalated_or_deferred(tmp_path: Path) -> None:
    reg = ContractNoteRegistry(tmp_path)
    written = reg.write(_payload())
    escalated = reg.update(
        written.slug,
        state=ContractNoteState.ESCALATED,
        resolution="Disagreement on whether to break v2; Cat to rule.",
    )
    assert escalated.state is ContractNoteState.ESCALATED

    # New note + defer
    second = reg.write(_payload(title="Stale messages"))
    deferred = reg.update(
        second.slug,
        state=ContractNoteState.DEFERRED,
        resolution="Out of scope for v3; revisit after multilingual ships.",
    )
    assert deferred.state is ContractNoteState.DEFERRED


# ---------- registry: header parser tolerance ----------


def test_record_from_disk_recovers_state_and_version(tmp_path: Path) -> None:
    reg = ContractNoteRegistry(tmp_path)
    reg.write(
        _payload(
            state=ContractNoteState.AGREED,
            contract_version="message-envelope v3",
            backend_impact="New columns",
            resolution="Ship",
        )
    )
    # Re-instantiate registry to force re-scan from disk.
    reg2 = ContractNoteRegistry(tmp_path)
    notes = reg2.list_contract_notes()
    assert len(notes) == 1
    assert notes[0].state is ContractNoteState.AGREED
    assert notes[0].contract_version == "message-envelope v3"
