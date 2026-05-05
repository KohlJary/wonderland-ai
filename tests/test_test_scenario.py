"""Tests for the Test Scenario writer + registry."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from wonderland import (
    Severity,
    TestScenarioPayload,
    TestScenarioRegistry,
    render_test_scenario,
)

# ---------- helpers ----------


def _payload(**overrides) -> TestScenarioPayload:
    base = {
        "title": "User pastes 40,000 emoji into a one-line message field",
        "severity": Severity.SILENT_WRONGNESS,
        "setup": "A composer that advertises a 280-char limit but does no client-side enforcement.",
        "trigger": "User pastes an emoji block far exceeding the limit and presses send.",
        "expected": "Message rejected with a clear error before it leaves the device.",
        "concern": (
            "I suspect the emoji are sliced byte-wise, not grapheme-wise, "
            "producing a half-emoji at the boundary that the recipient renders as garbage."
        ),
        "property": "For all messages M, render(receive(send(M))) == M or send rejects M.",
        "implies": [
            "Implies architectural decision about encoding boundary — flag for Cat.",
        ],
    }
    return TestScenarioPayload(**(base | overrides))


# ---------- TestScenarioPayload validation ----------


def test_payload_requires_non_empty_title() -> None:
    with pytest.raises(ValidationError):
        _payload(title="")


def test_payload_requires_non_empty_setup() -> None:
    with pytest.raises(ValidationError):
        _payload(setup="")


def test_payload_requires_non_empty_trigger() -> None:
    with pytest.raises(ValidationError):
        _payload(trigger="")


def test_payload_requires_non_empty_expected() -> None:
    with pytest.raises(ValidationError):
        _payload(expected="")


def test_payload_requires_non_empty_concern() -> None:
    """Concern is the grin equivalent — required hypothesis."""
    with pytest.raises(ValidationError):
        _payload(concern="")


def test_payload_rejects_only_whitespace_concern() -> None:
    with pytest.raises(ValidationError, match="grin"):
        _payload(concern="   ")


@pytest.mark.parametrize("severity", list(Severity))
def test_payload_accepts_each_severity(severity: Severity) -> None:
    payload = _payload(severity=severity)
    assert payload.severity is severity


def test_payload_rejects_unknown_severity() -> None:
    with pytest.raises(ValidationError):
        _payload(severity="critical")  # type: ignore[arg-type]


def test_payload_property_optional() -> None:
    payload = _payload(property="")
    assert payload.property == ""


def test_payload_implies_optional() -> None:
    payload = _payload(implies=[])
    assert payload.implies == []


# ---------- render_test_scenario ----------


def test_render_includes_required_sections() -> None:
    out = render_test_scenario(7, _payload())
    assert "## Scenario 007: User pastes 40,000 emoji" in out
    assert "**Severity:** silent-wrongness" in out
    assert "**Setup:**" in out
    assert "A composer that advertises" in out
    assert "**Trigger:**" in out
    assert "**Expected:**" in out
    assert "**Concern:**" in out
    assert "I suspect the emoji are sliced" in out


def test_render_includes_property_when_present() -> None:
    out = render_test_scenario(1, _payload())
    assert "**Property:**" in out
    assert "render(receive(send(M))) == M" in out


def test_render_omits_property_when_empty() -> None:
    out = render_test_scenario(1, _payload(property=""))
    assert "**Property:**" not in out


def test_render_includes_implies_list() -> None:
    out = render_test_scenario(1, _payload())
    assert "**Implies:**" in out
    assert "- Implies architectural decision about encoding boundary" in out


def test_render_omits_implies_when_empty() -> None:
    out = render_test_scenario(1, _payload(implies=[]))
    assert "**Implies:**" not in out


def test_render_three_digit_padding() -> None:
    assert "Scenario 003:" in render_test_scenario(3, _payload())


# ---------- TestScenarioRegistry — empty state ----------


def test_empty_registry_state(tmp_path: Path) -> None:
    registry = TestScenarioRegistry(tmp_path)
    assert registry.list_scenarios() == []
    assert registry.next_number() == 1
    assert registry.find_by_slug("anything") is None
    assert registry.find_by_number(1) is None


def test_path_under_dot_wonderland_test_scenarios(tmp_path: Path) -> None:
    registry = TestScenarioRegistry(tmp_path)
    assert registry.path == tmp_path / ".wonderland" / "test-scenarios"


# ---------- TestScenarioRegistry — write ----------


def test_write_creates_file_at_expected_path(tmp_path: Path) -> None:
    registry = TestScenarioRegistry(tmp_path)
    record = registry.write(_payload())
    assert record.number == 1
    assert record.slug.startswith("user-pastes-40-000-emoji")
    assert record.path.is_file()
    assert record.severity is Severity.SILENT_WRONGNESS


def test_write_creates_parent_directory(tmp_path: Path) -> None:
    registry = TestScenarioRegistry(tmp_path)
    registry.write(_payload())
    assert registry.path.is_dir()


def test_write_accepts_dict_payload(tmp_path: Path) -> None:
    registry = TestScenarioRegistry(tmp_path)
    record = registry.write(
        {
            "title": "Race between message edit and translation cache invalidation",
            "severity": "silent-wrongness",
            "setup": "Edit and translate run concurrently for the same message.",
            "trigger": "User edits message between translate-request and translate-response.",
            "expected": "Stale translation discarded; new translation requested.",
            "concern": "Cache returns stale text without invalidation.",
            "property": "",
            "implies": [],
        }
    )
    assert record.title.startswith("Race between message edit")


def test_write_rejects_payload_without_concern(tmp_path: Path) -> None:
    registry = TestScenarioRegistry(tmp_path)
    with pytest.raises(ValidationError):
        registry.write(
            {
                "title": "x",
                "severity": "breakage",
                "setup": "y",
                "trigger": "z",
                "expected": "w",
                "concern": "",
            }
        )


def test_write_auto_increments(tmp_path: Path) -> None:
    registry = TestScenarioRegistry(tmp_path)
    a = registry.write(_payload(title="A"))
    b = registry.write(_payload(title="B"))
    assert (a.number, b.number) == (1, 2)


def test_written_file_round_trips_through_render(tmp_path: Path) -> None:
    registry = TestScenarioRegistry(tmp_path)
    payload = _payload()
    record = registry.write(payload)
    assert record.read() == render_test_scenario(1, payload)


# ---------- TestScenarioRegistry — queries ----------


def test_list_in_number_order(tmp_path: Path) -> None:
    registry = TestScenarioRegistry(tmp_path)
    for title in ("Third", "First", "Second"):
        registry.write(_payload(title=title))
    listing = registry.list_scenarios()
    assert [r.number for r in listing] == [1, 2, 3]
    assert [r.title for r in listing] == ["Third", "First", "Second"]


def test_find_by_slug(tmp_path: Path) -> None:
    registry = TestScenarioRegistry(tmp_path)
    registry.write(_payload(title="Maya joins"))
    found = registry.find_by_slug("maya-joins")
    assert found is not None
    assert found.severity is Severity.SILENT_WRONGNESS


def test_find_by_number(tmp_path: Path) -> None:
    registry = TestScenarioRegistry(tmp_path)
    registry.write(_payload(title="A"))
    registry.write(_payload(title="B"))
    found = registry.find_by_number(2)
    assert found is not None
    assert found.title == "B"


def test_recovers_severity_from_disk(tmp_path: Path) -> None:
    registry = TestScenarioRegistry(tmp_path)
    registry.write(_payload(title="Breakage thing", severity=Severity.BREAKAGE))
    # Re-read from disk to confirm severity round-trips through the
    # filename-and-header parse path, not just the in-memory record.
    fresh = TestScenarioRegistry(tmp_path)
    listing = fresh.list_scenarios()
    assert listing[0].severity is Severity.BREAKAGE


def test_skips_non_scenario_files(tmp_path: Path) -> None:
    registry = TestScenarioRegistry(tmp_path)
    registry.write(_payload(title="A"))
    (registry.path / "README.md").write_text("not a scenario")
    (registry.path / "scenario-malformed.md").write_text("also not")
    assert len(registry.list_scenarios()) == 1
