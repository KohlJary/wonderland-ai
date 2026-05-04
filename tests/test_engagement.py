"""Tests for the structured engagement rules system."""

from __future__ import annotations

import pytest

from wonderland import (
    AgentIdentity,
    Engagement,
    EngagementRule,
    EngagementRules,
    SpeechAct,
    Utterance,
    UtteranceContent,
    addressed_to,
    almost_never,
    always,
    body_contains_any,
    make_engagement_policy,
    rarely,
    selectively,
    speaker_is,
)

# ---------- helpers ----------


def _u(
    *,
    act: SpeechAct = SpeechAct.PROPOSAL,
    speaker: str = "white_rabbit",
    addressed: list[str] | str = "caucus",
    body: str = "...",
) -> Utterance:
    return Utterance(
        thread_id="t",
        speaker=AgentIdentity(name=speaker, constitution_version="0.1"),
        addressed_to=(
            "caucus"
            if addressed == "caucus"
            else [AgentIdentity(name=n, constitution_version="0.1") for n in addressed]
        ),
        speech_act=act,
        content=UtteranceContent(body=body),
    )


# ---------- EngagementRule.matches ----------


def test_rule_matches_speech_act_only_when_no_condition() -> None:
    rule = EngagementRule(speech_act=SpeechAct.PROPOSAL, category=Engagement.ALWAYS)
    assert rule.matches(_u(act=SpeechAct.PROPOSAL))
    assert not rule.matches(_u(act=SpeechAct.TICKET))


def test_rule_requires_condition_to_pass_when_present() -> None:
    rule = EngagementRule(
        speech_act=SpeechAct.TICKET,
        category=Engagement.ALWAYS,
        condition=speaker_is("white_rabbit"),
    )
    assert rule.matches(_u(act=SpeechAct.TICKET, speaker="white_rabbit"))
    assert not rule.matches(_u(act=SpeechAct.TICKET, speaker="someone_else"))
    # Condition is not consulted when speech_act mismatches
    assert not rule.matches(_u(act=SpeechAct.PROPOSAL, speaker="white_rabbit"))


# ---------- EngagementRules.categorize ----------


def test_categorize_returns_default_when_no_rule_matches() -> None:
    rules = EngagementRules.of(default=Engagement.ALMOST_NEVER)
    assert rules.categorize(_u()) is Engagement.ALMOST_NEVER


def test_categorize_first_matching_rule_wins() -> None:
    """Narrower rules placed first take precedence over broader ones."""
    rules = EngagementRules.of(
        EngagementRule(
            speech_act=SpeechAct.TICKET,
            category=Engagement.ALWAYS,
            condition=speaker_is("white_rabbit"),
        ),
        EngagementRule(
            speech_act=SpeechAct.TICKET,
            category=Engagement.RARELY,
        ),
    )
    rabbit_ticket = _u(act=SpeechAct.TICKET, speaker="white_rabbit")
    other_ticket = _u(act=SpeechAct.TICKET, speaker="dodo")
    assert rules.categorize(rabbit_ticket) is Engagement.ALWAYS
    assert rules.categorize(other_ticket) is Engagement.RARELY


def test_categorize_handles_multiple_speech_acts() -> None:
    rules = EngagementRules.of(
        always(SpeechAct.PROPOSAL),
        selectively(SpeechAct.TICKET),
        rarely(SpeechAct.OBSERVATION),
        almost_never(SpeechAct.DEFERENCE),
    )
    assert rules.categorize(_u(act=SpeechAct.PROPOSAL)) is Engagement.ALWAYS
    assert rules.categorize(_u(act=SpeechAct.TICKET)) is Engagement.SELECTIVELY
    assert rules.categorize(_u(act=SpeechAct.OBSERVATION)) is Engagement.RARELY
    assert rules.categorize(_u(act=SpeechAct.DEFERENCE)) is Engagement.ALMOST_NEVER
    # Unmentioned act → default
    assert rules.categorize(_u(act=SpeechAct.QUESTION)) is Engagement.ALMOST_NEVER


# ---------- should_engage ----------


@pytest.mark.parametrize(
    "category,expected",
    [
        (Engagement.ALWAYS, True),
        (Engagement.SELECTIVELY, True),
        (Engagement.RARELY, True),
        (Engagement.ALMOST_NEVER, False),
    ],
)
def test_should_engage_only_skips_almost_never(category: Engagement, expected: bool) -> None:
    rules = EngagementRules.of(
        EngagementRule(speech_act=SpeechAct.PROPOSAL, category=category),
    )
    assert rules.should_engage(_u(act=SpeechAct.PROPOSAL)) is expected


def test_should_engage_uses_default_when_no_rule_matches() -> None:
    rules = EngagementRules.of(default=Engagement.ALMOST_NEVER)
    assert rules.should_engage(_u()) is False
    rules2 = EngagementRules.of(default=Engagement.SELECTIVELY)
    assert rules2.should_engage(_u()) is True


# ---------- predicate helpers ----------


def test_speaker_is_predicate() -> None:
    pred = speaker_is("white_rabbit")
    assert pred(_u(speaker="white_rabbit"))
    assert not pred(_u(speaker="cheshire_cat"))


def test_addressed_to_predicate_matches_directed_utterance() -> None:
    pred = addressed_to("cheshire_cat")
    assert pred(_u(addressed=["cheshire_cat"]))
    assert pred(_u(addressed=["white_rabbit", "cheshire_cat"]))
    assert not pred(_u(addressed=["white_rabbit"]))


def test_addressed_to_predicate_skips_caucus_broadcasts() -> None:
    """A caucus-broadcast utterance isn't 'addressed to' anyone specifically."""
    pred = addressed_to("cheshire_cat")
    assert not pred(_u(addressed="caucus"))


def test_body_contains_any_is_case_insensitive() -> None:
    pred = body_contains_any("real-time", "multi-tenant")
    assert pred(_u(body="this is REAL-TIME work"))
    assert pred(_u(body="we need multi-tenant support"))
    assert not pred(_u(body="just a normal feature"))


# ---------- speech_acts derivation ----------


def test_speech_acts_returns_distinct_acts_in_rules() -> None:
    rules = EngagementRules.of(
        always(SpeechAct.PROPOSAL),
        always(SpeechAct.PROPOSAL),  # duplicate — still distinct in set
        selectively(SpeechAct.TICKET),
        rarely(SpeechAct.OBSERVATION),
    )
    assert rules.speech_acts() == {
        SpeechAct.PROPOSAL,
        SpeechAct.TICKET,
        SpeechAct.OBSERVATION,
    }


# ---------- make_engagement_policy ----------


def test_make_engagement_policy_produces_callable() -> None:
    rules = EngagementRules.of(always(SpeechAct.PROPOSAL))
    policy = make_engagement_policy(rules)
    proposal = _u(act=SpeechAct.PROPOSAL)
    ticket = _u(act=SpeechAct.TICKET)
    assert policy(proposal, None) is True
    assert policy(ticket, None) is False


def test_policy_ignores_memory_argument() -> None:
    """T9 leaves LLM tiebreak deferred — the policy is heuristic-only."""
    rules = EngagementRules.of(always(SpeechAct.PROPOSAL))
    policy = make_engagement_policy(rules)
    sentinel = object()
    proposal = _u(act=SpeechAct.PROPOSAL)
    assert policy(proposal, sentinel) is True


# ---------- end-to-end shape resembling the Cat ----------


def test_cat_shaped_rules_compose_intelligibly() -> None:
    """A small ruleset shaped like the Cat's §III shows the API in use.

    The actual Cat rules ship with T11; this test just verifies the
    primitives compose into a readable, working policy.
    """
    rules = EngagementRules.of(
        always(SpeechAct.PROPOSAL),
        always(SpeechAct.DIRECTIVE),
        always(SpeechAct.QUESTION, condition=addressed_to("cheshire_cat")),
        always(
            SpeechAct.TICKET,
            condition=body_contains_any("synchronous call", "per message", "per request"),
        ),
        selectively(
            SpeechAct.STORY,
            condition=body_contains_any("real-time", "multi-tenant", "offline", "cross-language"),
        ),
        rarely(SpeechAct.OBSERVATION),
        almost_never(SpeechAct.DEFERENCE),
    )

    policy = make_engagement_policy(rules)

    # Always-on: proposals
    assert policy(_u(act=SpeechAct.PROPOSAL), None)

    # Question only when addressed
    assert policy(_u(act=SpeechAct.QUESTION, addressed=["cheshire_cat"]), None)
    assert not policy(_u(act=SpeechAct.QUESTION, addressed="caucus"), None)

    # Ticket only when implementation hint smells
    assert policy(_u(act=SpeechAct.TICKET, body="use a synchronous call"), None)
    assert not policy(_u(act=SpeechAct.TICKET, body="add a button"), None)

    # Story only when architectural primitive surfaces
    assert policy(_u(act=SpeechAct.STORY, body="needs real-time updates"), None)
    assert not policy(_u(act=SpeechAct.STORY, body="user wants a profile page"), None)

    # Observation falls into RARELY → engage (no condition refines)
    assert policy(_u(act=SpeechAct.OBSERVATION), None)

    # Deference is skipped
    assert not policy(_u(act=SpeechAct.DEFERENCE), None)

    # Unmentioned act → default ALMOST_NEVER → skip
    assert not policy(_u(act=SpeechAct.RULING), None)
