"""Tests for the Observation writer + registry."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from wonderland import (
    ObservationPayload,
    ObservationRegistry,
    ObservationSeverity,
    ObservationType,
    render_observation,
)

# ---------- helpers ----------


def _payload(**overrides) -> ObservationPayload:
    base = {
        "title": "Translation service error rate spike",
        "type": ObservationType.INCIDENT,
        "severity": ObservationSeverity.SEV2,
        "time_window_start": "2026-05-05T14:23:00Z",
        "time_window_end": "2026-05-05T14:31:00Z",
        "symptom": (
            "Error rate on the translation service rose from 0.04% to 2.7% "
            "between 14:23 and 14:31 UTC, affecting approximately 380 requests."
        ),
        "affected_scope": (
            "translation-service in eu-west-1; primarily the message-translate endpoint."
        ),
        "evidence": [
            "https://grafana.internal/d/translation/overview?from=14:00&to=15:00",
            "trace ID 01HXYZABCDEFGH",
            "logs: app=translation, level=error, count=2104, window=14:23-14:31",
        ],
        "probable_domain": "backend",
        "routed_to": "tweedledum",
    }
    return ObservationPayload(**(base | overrides))


# ---------- ObservationPayload validation: structural ----------


@pytest.mark.parametrize(
    "field",
    ["title", "time_window_start", "symptom", "affected_scope"],
)
def test_payload_requires_non_empty_field(field: str) -> None:
    with pytest.raises(ValidationError):
        _payload(**{field: ""})


@pytest.mark.parametrize("type_", list(ObservationType))
def test_payload_accepts_each_type(type_: ObservationType) -> None:
    payload = _payload(type=type_)
    assert payload.type is type_


def test_payload_rejects_unknown_type() -> None:
    with pytest.raises(ValidationError):
        _payload(type="catastrophe")  # type: ignore[arg-type]


@pytest.mark.parametrize("severity", list(ObservationSeverity))
def test_payload_accepts_each_severity(severity: ObservationSeverity) -> None:
    payload = _payload(severity=severity)
    assert payload.severity is severity


def test_payload_rejects_unknown_severity() -> None:
    with pytest.raises(ValidationError):
        _payload(severity="critical")  # type: ignore[arg-type]


def test_payload_optional_fields_default_to_empty() -> None:
    payload = _payload(
        time_window_end="",
        probable_domain="",
        routed_to="",
    )
    assert payload.time_window_end == ""
    assert payload.probable_domain == ""
    assert payload.routed_to == ""


# ---------- ObservationPayload validation: the grin (evidence) ----------


def test_payload_rejects_empty_evidence_list() -> None:
    """The grin equivalent — observations without evidence are unverifiable (§VIII)."""
    with pytest.raises(ValidationError, match="Crying wolf"):
        _payload(evidence=[])


def test_payload_rejects_only_whitespace_evidence() -> None:
    with pytest.raises(ValidationError, match="Crying wolf"):
        _payload(evidence=["", "   ", "\t"])


def test_payload_strips_whitespace_only_evidence_entries() -> None:
    payload = _payload(evidence=["a real dashboard URL", "  ", ""])
    assert payload.evidence == ["a real dashboard URL"]


# ---------- render_observation ----------


def test_render_includes_required_sections() -> None:
    out = render_observation(7, _payload())
    assert "## Observation 007: Translation service error rate spike" in out
    assert "**Type:** incident" in out
    assert "**Severity:** sev2" in out
    assert "**Time window:** 2026-05-05T14:23:00Z — 2026-05-05T14:31:00Z" in out
    assert "**Symptom:**" in out
    assert "Error rate on the translation service rose" in out
    assert "**Affected scope:**" in out
    assert "**Evidence:**" in out
    assert "- https://grafana.internal" in out


def test_render_marks_time_window_as_ongoing_when_end_empty() -> None:
    out = render_observation(1, _payload(time_window_end=""))
    assert "**Time window:** 2026-05-05T14:23:00Z — ongoing" in out


def test_render_includes_routing_when_present() -> None:
    out = render_observation(1, _payload())
    assert "**Probable domain:** backend" in out
    assert "**Routed to:** tweedledum" in out


def test_render_omits_routing_when_empty() -> None:
    out = render_observation(
        1,
        _payload(probable_domain="", routed_to=""),
    )
    assert "**Probable domain:**" not in out
    assert "**Routed to:**" not in out


def test_render_three_digit_padding() -> None:
    assert "Observation 003:" in render_observation(3, _payload())


# ---------- ObservationRegistry — empty state ----------


def test_empty_registry_state(tmp_path: Path) -> None:
    registry = ObservationRegistry(tmp_path)
    assert registry.list_observations() == []
    assert registry.next_number() == 1
    assert registry.find_by_slug("anything") is None
    assert registry.find_by_number(1) is None


def test_path_under_dot_wonderland_observations(tmp_path: Path) -> None:
    registry = ObservationRegistry(tmp_path)
    assert registry.path == tmp_path / ".wonderland" / "observations"


# ---------- ObservationRegistry — write ----------


def test_write_creates_file_at_expected_path(tmp_path: Path) -> None:
    registry = ObservationRegistry(tmp_path)
    record = registry.write(_payload())
    assert record.number == 1
    assert record.slug.startswith("translation-service-error-rate-spike")
    assert record.path.is_file()
    assert record.type is ObservationType.INCIDENT
    assert record.severity is ObservationSeverity.SEV2


def test_write_creates_parent_directory(tmp_path: Path) -> None:
    registry = ObservationRegistry(tmp_path)
    registry.write(_payload())
    assert registry.path.is_dir()


def test_write_accepts_dict_payload(tmp_path: Path) -> None:
    registry = ObservationRegistry(tmp_path)
    record = registry.write(
        {
            "title": "Steady-state confirmation: translation service",
            "type": "steady-state",
            "severity": "informational",
            "time_window_start": "2026-05-05T00:00:00Z",
            "time_window_end": "2026-05-05T23:59:59Z",
            "symptom": "Error rate held at ~0.03% across the day; latency p99 within budget.",
            "affected_scope": "translation-service across all regions",
            "evidence": ["dashboard: translation/overview, full-day view"],
        }
    )
    assert record.type is ObservationType.STEADY_STATE
    assert record.severity is ObservationSeverity.INFORMATIONAL


def test_write_rejects_payload_without_evidence(tmp_path: Path) -> None:
    registry = ObservationRegistry(tmp_path)
    with pytest.raises(ValidationError):
        registry.write(
            {
                "title": "x",
                "type": "incident",
                "severity": "sev2",
                "time_window_start": "now",
                "symptom": "y",
                "affected_scope": "z",
                "evidence": [],
            }
        )


def test_write_auto_increments(tmp_path: Path) -> None:
    registry = ObservationRegistry(tmp_path)
    a = registry.write(_payload(title="A"))
    b = registry.write(_payload(title="B"))
    assert (a.number, b.number) == (1, 2)


def test_written_file_round_trips_through_render(tmp_path: Path) -> None:
    registry = ObservationRegistry(tmp_path)
    payload = _payload()
    record = registry.write(payload)
    assert record.read() == render_observation(1, payload)


# ---------- ObservationRegistry — queries ----------


def test_list_in_number_order(tmp_path: Path) -> None:
    registry = ObservationRegistry(tmp_path)
    for title in ("Third", "First", "Second"):
        registry.write(_payload(title=title))
    listing = registry.list_observations()
    assert [r.number for r in listing] == [1, 2, 3]
    assert [r.title for r in listing] == ["Third", "First", "Second"]


def test_find_by_slug(tmp_path: Path) -> None:
    registry = ObservationRegistry(tmp_path)
    registry.write(_payload(title="Auth latency spike"))
    found = registry.find_by_slug("auth-latency-spike")
    assert found is not None
    assert found.severity is ObservationSeverity.SEV2


def test_find_by_number(tmp_path: Path) -> None:
    registry = ObservationRegistry(tmp_path)
    registry.write(_payload(title="A"))
    registry.write(_payload(title="B"))
    found = registry.find_by_number(2)
    assert found is not None
    assert found.title == "B"


def test_recovers_type_and_severity_from_disk(tmp_path: Path) -> None:
    registry = ObservationRegistry(tmp_path)
    registry.write(
        _payload(
            title="Sev1 incident",
            type=ObservationType.INCIDENT,
            severity=ObservationSeverity.SEV1,
        )
    )
    fresh = ObservationRegistry(tmp_path)
    listing = fresh.list_observations()
    assert listing[0].type is ObservationType.INCIDENT
    assert listing[0].severity is ObservationSeverity.SEV1


def test_skips_non_observation_files(tmp_path: Path) -> None:
    registry = ObservationRegistry(tmp_path)
    registry.write(_payload(title="A"))
    (registry.path / "README.md").write_text("not an observation")
    (registry.path / "observation-malformed.md").write_text("also not")
    assert len(registry.list_observations()) == 1
