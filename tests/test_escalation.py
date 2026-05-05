"""Tests for the escalation data + registry."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from wonderland import (
    AgentProposalSchema,
    EscalationBrief,
    EscalationRegistry,
    render_escalation,
)

# ---------- helpers ----------


def _brief(
    *,
    thread_id: str = "demo-thread",
    decision: str = "Should X happen, given Y and Z?",
) -> EscalationBrief:
    return EscalationBrief(
        thread_id=thread_id,
        decision_required=decision,
        agent_proposals=[
            AgentProposalSchema(
                speaker="cheshire_cat",
                position="async layer",
                rationale="latency varies",
                domain="architecture",
            ),
            AgentProposalSchema(
                speaker="white_rabbit",
                position="synchronous v1",
                rationale="Thursday demo",
            ),
        ],
        suggested_resolution="Lean toward Cat — architecture domain implicated.",
        suggested_owner="cheshire_cat",
        suggested_domain="architecture",
        stakes="async lands in 2 days; sync lands in 1 day but needs rework later.",
        background="Translation chat directive; Alice's stories blocked.",
    )


# ---------- EscalationBrief validation ----------


def test_brief_requires_non_empty_decision_required() -> None:
    with pytest.raises(ValidationError):
        EscalationBrief(
            thread_id="t",
            decision_required="",
            agent_proposals=[
                AgentProposalSchema(speaker="a", position="x"),
                AgentProposalSchema(speaker="b", position="y"),
            ],
            suggested_resolution="...",
        )


def test_brief_requires_at_least_two_proposals() -> None:
    """A "conflict" with one proposal isn't a conflict."""
    with pytest.raises(ValidationError):
        EscalationBrief(
            thread_id="t",
            decision_required="?",
            agent_proposals=[AgentProposalSchema(speaker="a", position="x")],
            suggested_resolution="...",
        )


def test_brief_requires_non_empty_suggested_resolution() -> None:
    with pytest.raises(ValidationError):
        EscalationBrief(
            thread_id="t",
            decision_required="?",
            agent_proposals=[
                AgentProposalSchema(speaker="a", position="x"),
                AgentProposalSchema(speaker="b", position="y"),
            ],
            suggested_resolution="",
        )


def test_brief_optional_fields_default_empty() -> None:
    brief = EscalationBrief(
        thread_id="t",
        decision_required="?",
        agent_proposals=[
            AgentProposalSchema(speaker="a", position="x"),
            AgentProposalSchema(speaker="b", position="y"),
        ],
        suggested_resolution="...",
    )
    assert brief.stakes == ""
    assert brief.background == ""
    assert brief.suggested_owner is None
    assert brief.suggested_domain is None


# ---------- render_escalation ----------


def test_render_includes_all_required_sections() -> None:
    out = render_escalation(7, _brief())
    assert "## Escalation 007: demo-thread" in out
    assert "**Decision Required:**" in out
    assert "Should X happen" in out
    assert "**Agent Proposals:**" in out
    assert "**cheshire_cat**" in out
    assert "**white_rabbit**" in out
    assert "async layer" in out
    assert "**Suggested Resolution:**" in out
    assert "**Stakes:**" in out
    assert "**Background:**" in out


def test_render_includes_domain_primacy_hint() -> None:
    out = render_escalation(1, _brief())
    assert "`architecture`" in out
    assert "`cheshire_cat`" in out


def test_render_omits_optional_sections_when_empty() -> None:
    brief = EscalationBrief(
        thread_id="t",
        decision_required="?",
        agent_proposals=[
            AgentProposalSchema(speaker="a", position="x"),
            AgentProposalSchema(speaker="b", position="y"),
        ],
        suggested_resolution="...",
    )
    out = render_escalation(1, brief)
    assert "**Stakes:**" not in out
    assert "**Background:**" not in out


def test_render_renders_proposal_rationale_indented() -> None:
    out = render_escalation(1, _brief())
    # Rationale lines indented two spaces under their proposal bullet
    assert "  latency varies" in out
    assert "  Thursday demo" in out


def test_render_three_digit_padding() -> None:
    assert "Escalation 003:" in render_escalation(3, _brief())


# ---------- EscalationRegistry ----------


def test_empty_registry_state(tmp_path: Path) -> None:
    registry = EscalationRegistry(tmp_path)
    assert registry.list_escalations() == []
    assert registry.next_number() == 1
    assert registry.find_by_slug("anything") is None
    assert registry.find_by_number(1) is None


def test_path_under_dot_wonderland_escalations(tmp_path: Path) -> None:
    registry = EscalationRegistry(tmp_path)
    assert registry.path == tmp_path / ".wonderland" / "escalations"


def test_write_creates_file_and_record(tmp_path: Path) -> None:
    registry = EscalationRegistry(tmp_path)
    record = registry.write(_brief(thread_id="alpha"))
    assert record.number == 1
    assert record.slug == "alpha"
    assert record.path.is_file()
    assert "Escalation 001: alpha" in record.read()


def test_write_auto_increments(tmp_path: Path) -> None:
    registry = EscalationRegistry(tmp_path)
    a = registry.write(_brief(thread_id="alpha"))
    b = registry.write(_brief(thread_id="beta"))
    assert (a.number, b.number) == (1, 2)


def test_write_accepts_dict_payload(tmp_path: Path) -> None:
    registry = EscalationRegistry(tmp_path)
    record = registry.write(
        {
            "thread_id": "demo",
            "decision_required": "Should X?",
            "agent_proposals": [
                {"speaker": "a", "position": "x"},
                {"speaker": "b", "position": "y"},
            ],
            "suggested_resolution": "...",
        }
    )
    assert record.number == 1


def test_write_rejects_invalid_payload(tmp_path: Path) -> None:
    registry = EscalationRegistry(tmp_path)
    with pytest.raises(ValidationError):
        registry.write({"thread_id": "", "decision_required": "?", "agent_proposals": []})


def test_list_in_number_order(tmp_path: Path) -> None:
    registry = EscalationRegistry(tmp_path)
    for tid in ("third", "first", "second"):
        registry.write(_brief(thread_id=tid))
    listing = registry.list_escalations()
    assert [r.number for r in listing] == [1, 2, 3]
    assert [r.title for r in listing] == ["third", "first", "second"]


def test_skips_non_escalation_files(tmp_path: Path) -> None:
    registry = EscalationRegistry(tmp_path)
    registry.write(_brief(thread_id="alpha"))
    (registry.path / "README.md").write_text("not an escalation")
    listing = registry.list_escalations()
    assert len(listing) == 1
