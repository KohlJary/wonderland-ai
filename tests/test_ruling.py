"""Tests for the Ruling writer + registry."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from wonderland import (
    RulingDomain,
    RulingPayload,
    RulingRegistry,
    RulingSeverity,
    render_ruling,
)

# ---------- helpers ----------


def _payload(**overrides) -> RulingPayload:
    base = {
        "title": "PII written to debug logs in payment refund handler",
        "severity": RulingSeverity.HIGH,
        "domain": RulingDomain.LOGGING_AND_AUDIT,
        "source": "implementation from tweedledum",
        "citation": (
            "OWASP A09:2021 Security Logging and Monitoring Failures; "
            "GDPR Art. 5(1)(c) data minimization."
        ),
        "finding": (
            "The handler logs the full request payload at debug level, "
            "including payment instrument tokens and the user's full name. "
            "These reach centralized logs accessible to the entire on-call "
            "rotation, including engineers without PCI training."
        ),
        "required_remediation": (
            "Strip payment instrument fields and personal identifiers from "
            "the log payload before emission. Approved approach is a "
            "log-redaction filter applied at the structured-logger layer; "
            "the Tweedles retain the choice between filter-at-source and "
            "filter-at-sink."
        ),
        "acceptance_criteria": [
            "no payment instrument fields appear in any log line under any log level",
            "no email or full name fields appear in any log line at info/debug levels",
            "the redaction is unit-tested against a representative payload fixture",
        ],
        "residual_risk": (
            "Existing log data already in centralized storage retains the "
            "leaked fields until the next 30-day rotation."
        ),
        "compliance_implications": (
            "GDPR Art. 5(1)(c) requires data minimization; PCI DSS 3.4 prohibits "
            "storing the PAN even in logs. The current state is non-compliant "
            "with both."
        ),
        "audit_reference": "ruling-NNN tracked in Threat Garden under data-handling.",
    }
    return RulingPayload(**(base | overrides))


# ---------- RulingPayload validation: structural ----------


@pytest.mark.parametrize(
    "field",
    ["title", "finding", "required_remediation"],
)
def test_payload_requires_non_empty_field(field: str) -> None:
    with pytest.raises(ValidationError):
        _payload(**{field: ""})


@pytest.mark.parametrize("severity", list(RulingSeverity))
def test_payload_accepts_each_severity(severity: RulingSeverity) -> None:
    payload = _payload(severity=severity)
    assert payload.severity is severity


def test_payload_rejects_unknown_severity() -> None:
    with pytest.raises(ValidationError):
        _payload(severity="catastrophic")  # type: ignore[arg-type]


@pytest.mark.parametrize("domain", list(RulingDomain))
def test_payload_accepts_each_domain(domain: RulingDomain) -> None:
    payload = _payload(domain=domain)
    assert payload.domain is domain


def test_payload_rejects_unknown_domain() -> None:
    with pytest.raises(ValidationError):
        _payload(domain="vibes")  # type: ignore[arg-type]


def test_payload_optional_fields_default_to_empty() -> None:
    payload = _payload(
        source="",
        residual_risk="",
        compliance_implications="",
        audit_reference="",
    )
    assert payload.source == ""
    assert payload.residual_risk == ""
    assert payload.compliance_implications == ""
    assert payload.audit_reference == ""


# ---------- RulingPayload validation: the grin (citation) ----------


def test_payload_requires_non_empty_citation() -> None:
    """The grin equivalent — rulings without citation are opinions (§VIII)."""
    with pytest.raises(ValidationError, match="opinions"):
        _payload(citation="")


def test_payload_rejects_only_whitespace_citation() -> None:
    with pytest.raises(ValidationError, match="opinions"):
        _payload(citation="   ")


# ---------- RulingPayload validation: acceptance criteria ----------


def test_payload_rejects_empty_acceptance_criteria() -> None:
    with pytest.raises(ValidationError):
        _payload(acceptance_criteria=[])


def test_payload_rejects_only_whitespace_acceptance_criteria() -> None:
    with pytest.raises(ValidationError, match="unfalsifiable"):
        _payload(acceptance_criteria=["", "  "])


# ---------- render_ruling ----------


def test_render_includes_required_sections() -> None:
    out = render_ruling(7, _payload())
    assert "## Ruling 007: PII written to debug logs" in out
    assert "**Severity:** high" in out
    assert "**Domain:** logging-and-audit" in out
    assert "**Source:** implementation from tweedledum" in out
    assert "**Citation:**" in out
    assert "OWASP A09:2021" in out
    assert "**Finding:**" in out
    assert "**Required Remediation:**" in out
    assert "**Acceptance Criteria:**" in out
    assert "- no payment instrument fields appear" in out


def test_render_includes_optional_sections_when_present() -> None:
    out = render_ruling(1, _payload())
    assert "**Residual Risk:**" in out
    assert "**Compliance Implications:**" in out
    assert "**Audit Reference:**" in out


def test_render_omits_optional_sections_when_empty() -> None:
    out = render_ruling(
        1,
        _payload(
            source="",
            residual_risk="",
            compliance_implications="",
            audit_reference="",
        ),
    )
    assert "**Source:**" not in out
    assert "**Residual Risk:**" not in out
    assert "**Compliance Implications:**" not in out
    assert "**Audit Reference:**" not in out


def test_render_three_digit_padding() -> None:
    assert "Ruling 003:" in render_ruling(3, _payload())


# ---------- RulingRegistry — empty state ----------


def test_empty_registry_state(tmp_path: Path) -> None:
    registry = RulingRegistry(tmp_path)
    assert registry.list_rulings() == []
    assert registry.next_number() == 1
    assert registry.find_by_slug("anything") is None
    assert registry.find_by_number(1) is None


def test_path_under_dot_wonderland_rulings(tmp_path: Path) -> None:
    registry = RulingRegistry(tmp_path)
    assert registry.path == tmp_path / ".wonderland" / "rulings"


# ---------- RulingRegistry — write ----------


def test_write_creates_file_at_expected_path(tmp_path: Path) -> None:
    registry = RulingRegistry(tmp_path)
    record = registry.write(_payload())
    assert record.number == 1
    assert record.slug.startswith("pii-written-to-debug-logs")
    assert record.path.is_file()
    assert record.severity is RulingSeverity.HIGH
    assert record.domain is RulingDomain.LOGGING_AND_AUDIT


def test_write_creates_parent_directory(tmp_path: Path) -> None:
    registry = RulingRegistry(tmp_path)
    registry.write(_payload())
    assert registry.path.is_dir()


def test_write_accepts_dict_payload(tmp_path: Path) -> None:
    registry = RulingRegistry(tmp_path)
    record = registry.write(
        {
            "title": "Hardcoded API key in repo",
            "severity": "critical",
            "domain": "secret-handling",
            "source": "implementation",
            "citation": "CWE-798 Use of Hard-coded Credentials",
            "finding": "Active production credential checked into the repository at config/clients.py:14.",
            "required_remediation": "Rotate the credential; move to the secrets manager; remove from git history.",
            "acceptance_criteria": ["the key is rotated at the provider", "the file no longer contains the key"],
        }
    )
    assert record.severity is RulingSeverity.CRITICAL
    assert record.domain is RulingDomain.SECRET_HANDLING


def test_write_rejects_payload_without_citation(tmp_path: Path) -> None:
    registry = RulingRegistry(tmp_path)
    with pytest.raises(ValidationError):
        registry.write(
            {
                "title": "x",
                "severity": "high",
                "domain": "authentication",
                "citation": "",
                "finding": "y",
                "required_remediation": "z",
                "acceptance_criteria": ["w"],
            }
        )


def test_write_auto_increments(tmp_path: Path) -> None:
    registry = RulingRegistry(tmp_path)
    a = registry.write(_payload(title="A"))
    b = registry.write(_payload(title="B"))
    assert (a.number, b.number) == (1, 2)


def test_written_file_round_trips_through_render(tmp_path: Path) -> None:
    registry = RulingRegistry(tmp_path)
    payload = _payload()
    record = registry.write(payload)
    assert record.read() == render_ruling(1, payload)


# ---------- RulingRegistry — queries ----------


def test_list_in_number_order(tmp_path: Path) -> None:
    registry = RulingRegistry(tmp_path)
    for title in ("Third", "First", "Second"):
        registry.write(_payload(title=title))
    listing = registry.list_rulings()
    assert [r.number for r in listing] == [1, 2, 3]
    assert [r.title for r in listing] == ["Third", "First", "Second"]


def test_find_by_slug(tmp_path: Path) -> None:
    registry = RulingRegistry(tmp_path)
    registry.write(_payload(title="Auth bypass on retry"))
    found = registry.find_by_slug("auth-bypass-on-retry")
    assert found is not None
    assert found.severity is RulingSeverity.HIGH


def test_find_by_number(tmp_path: Path) -> None:
    registry = RulingRegistry(tmp_path)
    registry.write(_payload(title="A"))
    registry.write(_payload(title="B"))
    found = registry.find_by_number(2)
    assert found is not None
    assert found.title == "B"


def test_recovers_severity_and_domain_from_disk(tmp_path: Path) -> None:
    registry = RulingRegistry(tmp_path)
    registry.write(
        _payload(
            title="Critical thing",
            severity=RulingSeverity.CRITICAL,
            domain=RulingDomain.AUTHENTICATION,
        )
    )
    fresh = RulingRegistry(tmp_path)
    listing = fresh.list_rulings()
    assert listing[0].severity is RulingSeverity.CRITICAL
    assert listing[0].domain is RulingDomain.AUTHENTICATION


def test_skips_non_ruling_files(tmp_path: Path) -> None:
    registry = RulingRegistry(tmp_path)
    registry.write(_payload(title="A"))
    (registry.path / "README.md").write_text("not a ruling")
    (registry.path / "ruling-malformed.md").write_text("also not")
    assert len(registry.list_rulings()) == 1
